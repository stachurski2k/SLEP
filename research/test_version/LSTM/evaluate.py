import torch
import numpy as np
from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import cross_val_score
from Model.LSTM_encoder import LSTMEncoder
from DataProcessing.train_data import GestureDataset, build_splits
from torch.utils.data import DataLoader


def evaluate(checkpoint_path="Model/Checkpoints/encoder_best.pt",
             landmarks_dir="Features"):

    ckpt = torch.load(checkpoint_path)
    config = ckpt["config"]
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    model = LSTMEncoder(
        config["input_dim"],
        config["hidden_dim"],
        config["num_layers"]
    ).to(device)
    model.load_state_dict(ckpt["model_state"])
    model.eval()

    # pobierz ścieżki do wszystkich plików
    train_paths, val_paths, label_map = build_splits(landmarks_dir, val_ratio=0.2)
    all_paths = train_paths + val_paths

    # jeśli checkpoint ma zapisany label_map, warto nadpisać by zachować zgodność ID
    if "label_map" in ckpt:
        label_map = ckpt["label_map"]

    # zbierz wszystkie embeddingi
    dataset = GestureDataset(all_paths, label_map)
    loader  = DataLoader(dataset, batch_size=64, shuffle=False)

    all_embeddings = []
    all_labels     = []

    with torch.no_grad():
        for anchor, _, _, label in loader:
            _, last_state = model(anchor.to(device))
            all_embeddings.append(last_state.cpu().numpy())
            all_labels.extend(label.numpy())

    X = np.concatenate(all_embeddings)
    y = np.array(all_labels)

    # 1-NN accuracy
    knn = KNeighborsClassifier(n_neighbors=1, metric="euclidean")
    scores = cross_val_score(knn, X, y, cv=5)

    print(f"1-NN accuracy: {scores.mean():.2%} ± {scores.std():.2%}")
    print(f"Last validation loss: {ckpt['val_loss']:.4f}")
    print(f"Epoch: {ckpt['epoch']}")


if __name__ == "__main__":
    evaluate()