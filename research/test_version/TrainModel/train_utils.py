import os
import tempfile
import time
import numpy as np
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import accuracy_score
from torch.optim.swa_utils import AveragedModel
from Recognition.build_faiss_db import build_index_from_npz

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


def _robust_replace(src, dst, max_retries=10, delay=0.5):
    for i in range(max_retries):
        try:
            os.replace(src, dst)
            return
        except PermissionError:
            if i == max_retries - 1:
                raise
            time.sleep(delay)


def atomic_torch_save(payload, path):
    tmp_path = _atomic_write_path(path)
    try:
        torch.save(payload, tmp_path)
        _robust_replace(tmp_path, path)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


def atomic_np_savez(path, **arrays):
    tmp_path = _atomic_write_path(path)
    try:
        with open(tmp_path, "wb") as file:
            np.savez(file, **arrays)
        _robust_replace(tmp_path, path)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


def atomic_faiss_save(embeddings, path):
    import faiss

    tmp_path = _atomic_write_path(path)
    try:
        emb = np.ascontiguousarray(embeddings, dtype=np.float32)
        faiss.normalize_L2(emb)

        index = faiss.IndexFlatIP(emb.shape[1])
        index.add(emb)
        faiss.write_index(index, tmp_path)

        _robust_replace(tmp_path, path)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


def get_embeddings(model, loader, device, normalize=True):
    model.eval()

    all_embeddings = []
    all_seq = []
    all_labels = []

    with torch.no_grad():
        for seq, labels in loader:
            seq = seq.to(device)

            embedding, reconstructed = model(seq)

            if normalize:
                embedding = F.normalize(embedding, p=2, dim=1)

            all_embeddings.append(embedding.cpu().numpy())
            all_seq.append(reconstructed.cpu().numpy())
            all_labels.append(labels.numpy())

    return np.concatenate(all_embeddings), np.concatenate(all_seq), np.concatenate(all_labels)


def save_embeddings(model, dataset, paths_with_labels, label_map, device, save_path, normalize=True):
    reference_loader = DataLoader(
        dataset=dataset,
        batch_size=64,
        shuffle=False,
        num_workers=0,
        pin_memory=torch.cuda.is_available(),
    )

    embeddings, sequence, labels = get_embeddings(model, reference_loader, device, normalize=normalize)
    paths = np.array([path for path, _ in paths_with_labels])
    label_names = np.array([label for _, label in paths_with_labels])
    id_to_label = np.array(
        [label for label, _ in sorted(label_map.items(), key=lambda item: item[1])]
    )

    atomic_np_savez(
        save_path,
        embeddings=embeddings.astype(np.float32),
        sequence=sequence.astype(np.float32),
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

def build_best_artifacts(
    model_encoder,
    checkpoint_path,
    train_dataset,
    val_dataset,
    train_paths,
    val_paths,
    label_map,
    device,
    train_embeddings_file,
    val_embeddings_file,
    model_name,
    normalize_embeddings,
):
    if not os.path.exists(checkpoint_path):
        print(f"Best checkpoint not found, skipping derived artifacts: {checkpoint_path}")
        return

    checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=True)
    config = checkpoint["config"]

    best_model = model_encoder(
        config["input_dim"],
        config["hidden_dim"],
        config["num_layers"],
        config["dropout"],
    ).to(device)
    best_model.load_state_dict(checkpoint["model_state"])
    best_model.eval()

    normalize = config.get("normalize_embeddings", normalize_embeddings)

    save_embeddings(
        best_model, train_dataset, train_paths,
        label_map, device, train_embeddings_file, normalize=normalize
    )
    save_embeddings(
        best_model, val_dataset, val_paths,
        label_map, device, val_embeddings_file, normalize=normalize
    )

    print(f"Train embeddings saved: {train_embeddings_file}")
    print(f"Val embeddings saved: {val_embeddings_file}")


def export_model_state(eval_model):
    if isinstance(eval_model, AveragedModel):
        return eval_model.module.state_dict(), "ema"
    return eval_model.state_dict(), "raw"


def format_dists(dists):
    return (
        f"d_pos={dists['d_pos']:.4f} | "
        f"d_neg={dists['d_neg']:.4f} | "
        f"diff={dists['diff']:.4f}"
    )
