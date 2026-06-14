import os
import tempfile
import numpy as np
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import accuracy_score


class EarlyStopping:
    def __init__(self, patience=15, min_delta=0.001):
        self.patience   = patience
        self.min_delta  = min_delta
        self.best_acc   = 0.0
        self.counter    = 0
        self.should_stop = False

    def step(self, val_acc, is_best=False):
        if val_acc > self.best_acc + self.min_delta or is_best:
            self.best_acc = max(self.best_acc, val_acc)
            self.counter  = 0
        else:
            self.counter += 1
            if self.counter == self.patience:
                self.should_stop = True
        return self.should_stop


def _atomic_write_path(path):
    directory = os.path.dirname(path) or "."
    os.makedirs(directory, exist_ok=True)

    tmp_file = tempfile.NamedTemporaryFile(
        dir=directory,
        prefix=f".{os.path.basename(path)}.",
        suffix=".tmp",
        delete=False,
    )
    tmp_file.close()
    return tmp_file.name


def atomic_torch_save(payload, path):
    tmp_path = _atomic_write_path(path)
    try:
        torch.save(payload, tmp_path)
        os.replace(tmp_path, path)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


def atomic_np_savez(path, **arrays):
    tmp_path = _atomic_write_path(path)
    try:
        with open(tmp_path, "wb") as file:
            np.savez(file, **arrays)
        os.replace(tmp_path, path)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


def get_embeddings(model, loader, device, normalize=True):
    model.eval()

    all_last_embeddings = []
    all_seq_embeddings = []
    all_labels = []

    with torch.no_grad():
        for seq, labels in loader:
            seq = seq.to(device)

            seq_embeddings, last_embeddings = model(seq)

            if normalize:
                last_embeddings = F.normalize(last_embeddings, p=2, dim=1)

            all_last_embeddings.append(last_embeddings.cpu().numpy())
            all_seq_embeddings.append(seq_embeddings.cpu().numpy())
            all_labels.append(labels.numpy())

    return np.concatenate(all_last_embeddings), np.concatenate(all_seq_embeddings), np.concatenate(all_labels)


def save_embeddings(model, dataset, paths_with_labels, label_map, device, save_path, normalize=True):
    reference_loader = DataLoader(
        dataset=dataset,
        batch_size=64,
        shuffle=False,
        num_workers=0,
        pin_memory=torch.cuda.is_available(),
    )

    last_embeddings, seq_embeddings, labels = get_embeddings(model, reference_loader, device, normalize=normalize)
    paths = np.array([path for path, _ in paths_with_labels])
    label_names = np.array([label for _, label in paths_with_labels])
    id_to_label = np.array(
        [label for label, _ in sorted(label_map.items(), key=lambda item: item[1])]
    )

    atomic_np_savez(
        save_path,
        last_embeddings=last_embeddings.astype(np.float32),
        seq_embeddings=seq_embeddings.astype(np.float32),
        labels=labels.astype(np.int64),
        paths=paths,
        label_names=label_names,
        id_to_label=id_to_label,
    )


def evaluate_knn(model, train_eval_loader, val_eval_loader, device, normalize=True):
    train_embeddings, _, train_labels = get_embeddings(
        model,
        train_eval_loader,
        device,
        normalize=normalize
    )

    val_embeddings, _, val_labels = get_embeddings(
        model,
        val_eval_loader,
        device,
        normalize=normalize
    )

    knn = KNeighborsClassifier(
        n_neighbors=1,
        metric="euclidean"
    )

    knn.fit(train_embeddings, train_labels)
    predictions = knn.predict(val_embeddings)
    accuracy = accuracy_score(val_labels, predictions)

    return accuracy, val_labels, predictions

