import os
import random
import numpy as np
import torch
import torch.nn.functional as F
from pytorch_metric_learning import losses, miners
from torch.utils.data import DataLoader
from DataProcessing.data_split import GestureDataset, build_splits
from DataProcessing.augmentation import SequenceAugmentor
from TrainModel.balanced_sampler import BalancedBatchSampler
from TrainModel.emb_quality import print_embedding_distances
from LSTM.LSTM_encoder import LSTMEncoder
from TrainModel.train_utils import save_reference_embeddings, evaluate_knn, EarlyStopping

# ── PATHS ────────────────────────────────────────────────────────────────
LANDMARKS_DIR           = "Features"
CHECKPOINT              = "LSTM/Checkpoints/best_encoder.pt"
REFERENCE               = "LSTM/Checkpoints/reference_embeddings.npz"

# ── MODEL ────────────────────────────────────────────────────────────────
MODEL                   = LSTMEncoder
INPUT_DIM               = 144    
HIDDEN_DIM              = 128
NUM_LAYERS              = 2
DROPOUT                 = 0.3
TARGET_LEN              = 60

# ── SAMPLER ──────────────────────────────────────────────────────────────
P_TRAIN                 = 8         # number of classes per batch
K_TRAIN                 = 4         # number of samples per class
P_VAL                   = 8
K_VAL                   = 4

# ── SCHEDULER ─────────────────────────────────────────────────────────────
LEARNING_RATE           = 5e-4
MIN_LR                  = 1e-5
PATIENCE                = 20
FACTOR                  = 0.7

# ── EARLY STOPPING ───────────────────────────────────────────────────────
EARLY_STOP_PATIENCE     = 20
EARLY_STOP_DELTA        = 0.005

# ── TRAINING ─────────────────────────────────────────────────────────────
EPOCHS                  = 120
MARGIN                  = 0.7
VAL_RATIO               = 0.2
SEED                    = 42
NORMALIZE_EMBEDDINGS    = True
MAX_BATCHES             = 5

# ── AUGMENTATION ─────────────────────────────────────────────────────────
AUG_NOISE_STD           = 0.02   # Gaussian noise on landmarks
AUG_STRETCH_RANGE       = (0.85, 1.15)  # temporal stretch factor
AUG_WARP_PROB           = 0.5    # probability of applying time warp
AUG_WARP_STD            = 0.08   # strength of time warp
AUG_SCALE_RANGE         = (0.90, 1.10)  # random scale of gesture size
AUG_MIRROR_PROB         = 0.5    # probability of horizontal mirror
AUG_DROPOUT_PROB        = 0.05   # probability of zeroing a landmark

def training():
    np.random.seed(SEED)
    random.seed(SEED)
    torch.manual_seed(SEED)
    
    DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    os.makedirs(os.path.dirname(CHECKPOINT), exist_ok=True)
    os.makedirs(os.path.dirname(REFERENCE), exist_ok=True)

    # ── DATA ─────────────────────────────────────────────────────────────────
    train_paths, val_paths, label_map = build_splits(LANDMARKS_DIR,
                                                    val_ratio = VAL_RATIO, 
                                                    seed = SEED )

    augmentor = SequenceAugmentor(
        noise_std     = AUG_NOISE_STD,
        stretch_range = AUG_STRETCH_RANGE,
        warp_prob     = AUG_WARP_PROB,
        warp_std      = AUG_WARP_STD,
        scale_range   = AUG_SCALE_RANGE,
        mirror_prob   = AUG_MIRROR_PROB,
        dropout_prob  = AUG_DROPOUT_PROB,
    )

    train_ds = GestureDataset(train_paths, label_map)  # kiedyś tu będzie augmentor=augmentor
    val_ds = GestureDataset(val_paths,   label_map)                       
    train_eval_ds = GestureDataset(train_paths, label_map)                       

    train_sampler = BalancedBatchSampler(train_ds.labels, P=P_TRAIN, K=K_TRAIN)
    
    train_loader = DataLoader(
        dataset = train_ds,
        batch_sampler = train_sampler,
        num_workers = 0,
        pin_memory = True
    )

    val_sampler = BalancedBatchSampler(val_ds.labels, P=P_VAL, K=K_VAL, num_batches= 4)

    val_loader = DataLoader(
        dataset = val_ds,
        batch_sampler = val_sampler,
        num_workers = 0,
        pin_memory = True
    )

    train_eval_loader = DataLoader(
        dataset=train_eval_ds,
        batch_size=64,
        shuffle=False,
        num_workers=0,
        pin_memory=True
    )

    val_eval_loader = DataLoader(
        dataset=val_ds,
        batch_size=64,
        shuffle=False,
        num_workers=0,
        pin_memory=True
    )

    # ── MODEL ──────────────────────────────────────────────────────────────
    model = MODEL(INPUT_DIM, HIDDEN_DIM, NUM_LAYERS, DROPOUT).to(DEVICE)
    criterion = losses.TripletMarginLoss(margin = MARGIN)
    miner = miners.TripletMarginMiner( margin = MARGIN, type_of_triplets= "semihard")
    optimizer = torch.optim.Adam(model.parameters(), lr = LEARNING_RATE)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, patience= PATIENCE, factor= FACTOR, min_lr = MIN_LR
    )

    print("-" * 60)
    print(f"Model: LSTM      input= {INPUT_DIM}      hidden= {HIDDEN_DIM}   "
          f"layers= {NUM_LAYERS}    dropout= {DROPOUT}    device= {DEVICE}")
    print(f"Training: epochs= {EPOCHS}    lr= {LEARNING_RATE}    margin= {MARGIN}")
    print(f"Batch Train: P= {P_TRAIN} classes x K= {K_TRAIN} examples = {P_TRAIN*K_TRAIN} samples")
    print(f"Batch Val:   P= {P_VAL} classes x K= {K_VAL} examples = {P_VAL*K_VAL} samples")
    print("-" * 60)

    best_val_accuracy = 0.0
    best_val_loss = float("inf")
    best_epoch = 0
    best_train_dists = []
    best_val_dists = []

    early_stopping = EarlyStopping(patience=EARLY_STOP_PATIENCE, min_delta=EARLY_STOP_DELTA)

    for epoch in range( 1, EPOCHS+1):

        # ── TRAINING LOOP ─────────────────────────────────────────────────────
        model.train()
        total_train_loss = 0.0
        train_batches = 0

        for seq, labels in train_loader:
            seq = seq.to(DEVICE)
            labels = labels.to(DEVICE)

            _, last_state = model(seq)              # forward pass

            last_state = F.normalize(last_state, p=2, dim=1) # normalize embeddings

            triplets = miner(last_state, labels)    # select triplets

            if len(triplets[0]) == 0:
                continue

            train_loss = criterion(last_state, labels, triplets)  # loss calculation

            optimizer.zero_grad()                   # zero the gradients
            train_loss.backward()                   # backward
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0) # gradient clipping
            optimizer.step()                        # update weights

            total_train_loss += train_loss.item()
            train_batches += 1

        total_train_loss /= max(train_batches, 1)

        # ── VALIDATION LOOP ──────────────────────────────────────────────────
        model.eval()
        total_val_loss = 0.0
        val_batches = 0

        with torch.no_grad():
            for seq, labels in val_loader:
                seq = seq.to(DEVICE)
                labels = labels.to(DEVICE)

                seq_emb, last_state = model(seq)
                last_state = F.normalize(last_state, p=2, dim=1)

                triplets = miner(last_state, labels)

                if len(triplets[0]) == 0:
                    continue

                val_loss = criterion(last_state, labels, triplets)
                total_val_loss += val_loss.item()
                val_batches += 1
        
        total_val_loss /= max(val_batches, 1)
        scheduler.step(total_val_loss)

        # ── EVALUATION ─────────────────────────────────────────────────────
        val_accuracy = evaluate_knn(
            model,
            train_eval_loader,
            val_eval_loader,
            DEVICE,
            normalize=NORMALIZE_EMBEDDINGS
        )
        is_best = (
            val_accuracy > best_val_accuracy
            or (val_accuracy == best_val_accuracy and total_val_loss < best_val_loss)
        )

        # ── DISTANCE CHECK ──────────────────────────────────────────────────
        if epoch % 10 == 0 and not is_best:
            print(f"\n[Epoch {epoch}] distances in train batch:")
            train_dists = print_embedding_distances(model, train_loader, DEVICE, n_batches=MAX_BATCHES)
            print(f"\n[Epoch {epoch}] distances in val batch:")
            val_dists = print_embedding_distances(model, val_loader, DEVICE, n_batches=MAX_BATCHES)
            print()

        # ── SAVE BEST MODEL ──────────────────────────────────────────────────
        saved = ""

        if is_best:
            best_val_accuracy = val_accuracy
            best_val_loss = total_val_loss
            best_epoch = epoch

            checkpoint = {
                "epoch": epoch,
                "model_state": model.state_dict(),
                "optimizer_state": optimizer.state_dict(),
                "scheduler_state": scheduler.state_dict() if scheduler else None,

                "train_loss": total_train_loss,
                "val_loss": total_val_loss,
                "best_val_accuracy": best_val_accuracy,
                "best_val_loss": best_val_loss,

                "label_map": label_map,
                "reference_path": REFERENCE,

                "config": {
                    "input_dim": INPUT_DIM,
                    "hidden_dim": HIDDEN_DIM,
                    "num_layers": NUM_LAYERS,
                    "dropout": DROPOUT,
                    "target_len": TARGET_LEN,
                    "normalize_embeddings": NORMALIZE_EMBEDDINGS,
                    "loss": "TripletMarginLoss",
                    "miner": "TripletMarginMiner",
                    "miner_type": "semihard",
                    "margin": MARGIN,
                    "p_train": P_TRAIN,
                    "k_train": K_TRAIN,
                    "p_val": P_VAL,
                    "k_val": K_VAL,
                    "selection_metric": "val_1nn_accuracy",
                },
            }

            torch.save(checkpoint, CHECKPOINT)
            save_reference_embeddings(
                model,
                train_ds,
                train_paths,
                label_map,
                DEVICE,
                REFERENCE,
                normalize=NORMALIZE_EMBEDDINGS
            )

            saved = "  <- zapisano"
            print(f"\n[Epoch {epoch}] distances in train batch (best):")
            best_train_dists = print_embedding_distances(model, train_loader, DEVICE, n_batches=MAX_BATCHES)
            
            print(f"\n[Epoch {epoch}] distances in val batch (best):")
            best_val_dists = print_embedding_distances(model, val_loader, DEVICE, n_batches=MAX_BATCHES)
            print()

        print(
            f"Epoch {epoch:3d} | "
            f"train: {total_train_loss:.4f} | "
            f"val: {total_val_loss:.4f} | "
            f"val_acc: {val_accuracy:.2%}"
            f"{saved}"
        )
        if early_stopping.step(val_accuracy, is_best=is_best):
            print(f"Early stopping at epoch {epoch} | best acc: {early_stopping.best_acc:.2f}%")
            break 


    print("\n" + "-" * 60)
    print("Training completed")
    print(f"Best epoch: {best_epoch}")
    print(f"Best val loss: {best_val_loss:.4f}")
    print(f"Best val accuracy: {best_val_accuracy:.2%}")
    print("\nBest train distances:")
    for batch_idx, d_pos, d_neg, diff in best_train_dists:
        print(f"batch {batch_idx}: d_pos={d_pos:.4f} | d_neg={d_neg:.4f} | diff={diff:.4f}")
    print("\nBest val distances:")
    for batch_idx, d_pos, d_neg, diff in best_val_dists:
        print(f"batch {batch_idx}: d_pos={d_pos:.4f} | d_neg={d_neg:.4f} | diff={diff:.4f}")
    print(f"Checkpoint saved: {CHECKPOINT}")
    print(f"Reference embeddings saved: {REFERENCE}")
    print("-" * 60)

if __name__ == "__main__":
    training()
