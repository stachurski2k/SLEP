import os
import random
import numpy as np
import torch
from torch.utils.data import DataLoader
from DataProcessing.preprocessing import preprocess
from DataProcessing.train_data import GestureDataset, build_splits
from Training.balanced_sampler import BalancedBatchSampler
from Model.LSTM_encoder import LSTMEncoder
from Training.triplet_loss import OnlineHardTripletLoss
 
 
LANDMARKS_DIR = "Features"
CHECKPOINT    = "Model/Checkpoints/encoder_best.pt"
 
INPUT_DIM  = 204    
HIDDEN_DIM = 64
NUM_LAYERS = 3
DROPOUT    = 0.3
TARGET_LEN = 60
 
P          = 8     
K          = 4     
EPOCHS     = 100
LR         = 3e-3
MARGIN     = 0.1
VAL_RATIO  = 0.2
SEED       = 42
 
def print_distances(model, loader, device, n_batches=3):
    """Wypisuje średnie d_pos i d_neg dla pierwszych n_batches."""
    model.eval()
    with torch.no_grad():
        for i, (seqs, labels) in enumerate(loader):
            if i >= n_batches:
                break
            seqs   = seqs.to(device)
            labels = labels.to(device)
 
            _, last_state = model(seqs)
 
            dot   = torch.mm(last_state, last_state.t())
            sq    = dot.diag().unsqueeze(1)
            dists = torch.clamp(sq + sq.t() - 2.0 * dot, min=1e-12).sqrt()
 
            labels_eq  = labels.unsqueeze(0) == labels.unsqueeze(1)
            eye        = torch.eye(len(labels), dtype=torch.bool, device=device)
            labels_eq  = labels_eq & ~eye
            labels_neq = ~(labels.unsqueeze(0) == labels.unsqueeze(1))
 
            d_pos = dists[labels_eq].mean().item()
            d_neg = dists[labels_neq].mean().item()
            print(f"  batch {i+1}: d_pos={d_pos:.4f}  "
                  f"d_neg={d_neg:.4f}  "
                  f"d_neg-d_pos={d_neg - d_pos:.4f}")
    model.train()
 
def train():
    torch.manual_seed(SEED)
    random.seed(SEED)
    np.random.seed(SEED)
 
    DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Urządzenie: {DEVICE}\n")
 
    os.makedirs(os.path.dirname(CHECKPOINT), exist_ok=True)
 
    # ── dane ─────────────────────────────────────────────────────────────────
    train_paths, val_paths, label_map = build_splits(LANDMARKS_DIR,
                                                     val_ratio=VAL_RATIO,
                                                     seed=SEED)
 
    train_ds = GestureDataset(train_paths, label_map)
    val_ds   = GestureDataset(val_paths,   label_map)
 
    train_sampler = BalancedBatchSampler(train_ds.labels, P=P, K=K)
    train_loader  = DataLoader(train_ds, batch_sampler=train_sampler,
                               num_workers=0, pin_memory=True)
    val_loader    = DataLoader(val_ds, batch_size=P * K,
                               shuffle=False, num_workers=0)
 
    # ── model ─────────────────────────────────────────────────────────────────
    model     = LSTMEncoder(INPUT_DIM, HIDDEN_DIM, NUM_LAYERS, DROPOUT).to(DEVICE)
    criterion = OnlineHardTripletLoss(margin=MARGIN)
    optimizer = torch.optim.Adam(model.parameters(), lr=LR)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, patience=10, factor=0.5, verbose=True
    )
 
    print("─" * 60)
    print(f"Model:   LSTM  input={INPUT_DIM}  hidden={HIDDEN_DIM}  "
          f"layers={NUM_LAYERS}  dropout={DROPOUT}")
    print(f"Trening: epochs={EPOCHS}  lr={LR}  margin={MARGIN}")
    print(f"Batch:   P={P} klas × K={K} przykładów = {P*K} próbek")
    print("─" * 60)
 
    best_val_loss = float("inf")
 
    for epoch in range(1, EPOCHS + 1):
 
        # ── diagnostyka co 5 epok ────────────────────────────────────────────
        if epoch % 5 == 1:
            print(f"\n[Epoch {epoch}] Odległości w batchu train:")
            print_distances(model, train_loader, DEVICE)
            print()
 
        # ── trening ──────────────────────────────────────────────────────────
        model.train()
        train_loss = 0.0
 
        for sequences, labels in train_loader:
            sequences = sequences.to(DEVICE)
            labels    = labels.to(DEVICE)
 
            _, last_state = model(sequences)
            loss = criterion(last_state, labels)
 
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
 
            train_loss += loss.item()
 
        train_loss /= len(train_loader)
 
        # ── walidacja ─────────────────────────────────────────────────────────
        model.eval()
        val_loss = 0.0
 
        with torch.no_grad():
            for sequences, labels in val_loader:
                sequences = sequences.to(DEVICE)
                labels    = labels.to(DEVICE)
                _, last_state = model(sequences)
                val_loss += criterion(last_state, labels).item()
 
        val_loss /= max(len(val_loader), 1)
        scheduler.step(val_loss)
 
        # ── zapis najlepszego modelu ──────────────────────────────────────────
        saved = ""
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save({
                "epoch":       epoch,
                "model_state": model.state_dict(),
                "val_loss":    val_loss,
                "label_map":   label_map,
                "config": {
                    "input_dim":  INPUT_DIM,
                    "hidden_dim": HIDDEN_DIM,
                    "num_layers": NUM_LAYERS,
                    "target_len": TARGET_LEN,
                },
            }, CHECKPOINT)
            saved = "  ← zapisano"
 
        print(f"Epoch {epoch:3d} | train: {train_loss:.4f} "
              f"| val: {val_loss:.4f}{saved}")
 
    print("\n" + "─" * 60)
    print(f"Trening zakończony. Najlepszy val loss: {best_val_loss:.4f}")
    print(f"Checkpoint: {CHECKPOINT}")
 
if __name__ == "__main__":
    train()