import os
import random
import numpy as np
import torch
import torch.nn.functional as F
from pytorch_metric_learning import losses
from torch.utils.data import DataLoader
from torch.optim.swa_utils import AveragedModel
from DataProcessing.data_split import GestureDataset, build_splits
from DataProcessing.augmentation import SequenceAugmentor
from TrainModel.balanced_sampler import BalancedBatchSampler
from TrainModel.emb_quality import embedding_distances
from TrainModel.train_utils import (
    EarlyStopping,
    atomic_np_savez,
    atomic_torch_save,
    evaluate_knn,
    save_embeddings,
)

# ── PATHS ────────────────────────────────────────────────────────────────
LANDMARKS_DIR           = "Features"

# ── MODEL ────────────────────────────────────────────────────────────────
INPUT_DIM               = 144
HIDDEN_DIM              = 256
NUM_LAYERS              = 2
DROPOUT                 = 0.4

# ── TRAINING ─────────────────────────────────────────────────────────────
EPOCHS                  = 500
VAL_RATIO               = 0.3
SEED                    = 42
NORMALIZE_EMBEDDINGS    = True

# ── LOSS ───────────────────────────────────────────────────────────────── 
MS_ALPHA                = 2.0
MS_BETA                 = 40.0
MS_BASE                 = 0.5

# ── SAMPLER ──────────────────────────────────────────────────────────────
P_TRAIN                 = 16
K_TRAIN                 = 4
P_VAL                   = 16
K_VAL                   = 4

# ── SCHEDULER ────────────────────────────────────────────────────────────
LEARNING_RATE           = 5e-4
MIN_LR                  = 1e-5
PATIENCE                = 20
FACTOR                  = 0.7

# ── EMA ──────────────────────────────────────────────────────────────────
EMA_DECAY               = 0.99
EMA_START_EPOCH         = 30

# ── EARLY STOPPING ───────────────────────────────────────────────────────
EARLY_STOP_PATIENCE     = 50
EARLY_STOP_DELTA        = 0.005

# ── AUGMENTATION ─────────────────────────────────────────────────────────
AUG_NOISE_STD           = 0.02
AUG_STRETCH_RANGE       = (0.85, 1.15)
AUG_WARP_PROB           = 0.5
AUG_WARP_STD            = 0.08
AUG_SCALE_RANGE         = (0.90, 1.10)
AUG_MIRROR_PROB         = 0.5
AUG_DROPOUT_PROB        = 0.05


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


def training(model_encoder):
    np.random.seed(SEED)
    random.seed(SEED)
    torch.manual_seed(SEED)

    DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # ── PATHS ─────────────────────────────────────────────────────────────
    model_name = model_encoder.__name__
    artifact_dir = os.path.join("Models", f"{model_name}_Checkpoints")
    os.makedirs(artifact_dir, exist_ok=True)
    
    best_encoder_file            = os.path.join(artifact_dir, "best_encoder.pt")
    train_embeddings_file        = os.path.join(artifact_dir, "train_embeddings.npz")
    val_embeddings_file          = os.path.join(artifact_dir, "val_embeddings.npz")
    training_logs_file           = os.path.join(artifact_dir, "training_logs.npz")

    # ── DATA ─────────────────────────────────────────────────────────────
    train_paths, val_paths, label_map = build_splits(
        LANDMARKS_DIR, val_ratio=VAL_RATIO, seed=SEED
    )

    augmentor = SequenceAugmentor(
        noise_std     = AUG_NOISE_STD,
        stretch_range = AUG_STRETCH_RANGE,
        warp_prob     = AUG_WARP_PROB,
        warp_std      = AUG_WARP_STD,
        scale_range   = AUG_SCALE_RANGE,
        mirror_prob   = AUG_MIRROR_PROB,
        dropout_prob  = AUG_DROPOUT_PROB,
    )

    train_ds      = GestureDataset(train_paths, label_map, augmentor=augmentor)
    val_ds        = GestureDataset(val_paths, label_map)
    train_eval_ds = GestureDataset(train_paths, label_map)

    train_sampler = BalancedBatchSampler(train_ds.labels, P=P_TRAIN, K=K_TRAIN)
    val_sampler   = BalancedBatchSampler(val_ds.labels,   P=P_VAL,   K=K_VAL)

    train_loader = DataLoader(
        train_ds, batch_sampler=train_sampler, num_workers=0, pin_memory=True
    )
    val_loader = DataLoader(
        val_ds, batch_sampler=val_sampler, num_workers=0, pin_memory=True
    )
    train_eval_loader = DataLoader(
        train_eval_ds, batch_size=64, shuffle=False, num_workers=0, pin_memory=True
    )
    val_eval_loader = DataLoader(
        val_ds, batch_size=64, shuffle=False, num_workers=0, pin_memory=True
    )

    # ── MODEL ─────────────────────────────────────────────────────────────
    model     = model_encoder(INPUT_DIM, HIDDEN_DIM, NUM_LAYERS, DROPOUT).to(DEVICE)
    criterion = losses.MultiSimilarityLoss(alpha=MS_ALPHA, beta=MS_BETA, base=MS_BASE)
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
    ema_model = AveragedModel(
        model, multi_avg_fn=torch.optim.swa_utils.get_ema_multi_avg_fn(EMA_DECAY)
    )
    scheduler = torch.optim.lr_scheduler.CosineAnnealingWarmRestarts(
        optimizer, T_0=30, T_mult=2, eta_min=1e-6
    )
    early_stopping = EarlyStopping(patience=EARLY_STOP_PATIENCE, min_delta=EARLY_STOP_DELTA)

    print("-" * 90)
    print(f"Model: {model_name}      input= {INPUT_DIM}      hidden= {HIDDEN_DIM}   "
          f"layers= {NUM_LAYERS}   dropout= {DROPOUT}    device= {DEVICE}")
    print(f"Training: epochs= {EPOCHS}    lr= {LEARNING_RATE}    "
          f"MultiSimilarityLoss: alpha= {MS_ALPHA} beta= {MS_BETA} base= {MS_BASE}")
    print(f"Batch Train: P = {P_TRAIN} classes x K = {K_TRAIN} = {P_TRAIN*K_TRAIN} samples")
    print(f"Batch Val:   P = {P_VAL} classes x K = {K_VAL} = {P_VAL*K_VAL} samples")
    print("-" * 90)

    # ── LOGS VARIABLES ─────────────────────────────────────────────
    best_val_accuracy  = 0.0
    best_val_loss      = float("inf")
    best_epoch         = 0
    train_loss_history = []
    val_loss_history   = []
    val_acc_history    = []
    train_dists_history = []
    val_dists_history = []
    best_train_dists = {"d_pos": float("nan"), "d_neg": float("nan"), "diff": float("nan")}
    best_val_dists = {"d_pos": float("nan"), "d_neg": float("nan"), "diff": float("nan")}
    best_prediction_history = []
    best_labels_history = []
    lr_history = []

    best_prediction = np.array([], dtype=np.int64)
    best_labels = np.array([], dtype=np.int64)

    for epoch in range(1, EPOCHS + 1):

        # ── TRAINING LOOP ─────────────────────────────────────────────────
        model.train()
        train_loss    = 0.0
        train_batches = 0

        for seq, labels in train_loader:
            seq    = seq.to(DEVICE)
            labels = labels.to(DEVICE)

            reconstructed, embedding = model(seq)

            embeddings = F.normalize(embedding, dim=1)

            loss_ms = criterion(embeddings, labels)
            rec_loss = F.mse_loss(reconstructed, seq)

            loss = loss_ms + 0.25 * rec_loss

            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()

            if epoch >= EMA_START_EPOCH:
                ema_model.update_parameters(model)

            train_loss    += loss.item()
            train_batches += 1

        train_loss /= max(train_batches, 1)

        # ── VALIDATION LOOP ───────────────────────────────────────────────
        current_eval_model = ema_model if epoch >= EMA_START_EPOCH else model
        current_eval_model.eval()

        val_loss    = 0.0
        val_batches = 0

        with torch.no_grad():
            for seq, labels in val_loader:
                seq    = seq.to(DEVICE)
                labels = labels.to(DEVICE)

                reconstructed, last_state = current_eval_model(seq)

                last_state = F.normalize(last_state, p=2, dim=1)
                loss_ms = criterion(last_state, labels)
                rec_loss = F.mse_loss(reconstructed, seq)
                loss = loss_ms + 0.25 * rec_loss

                val_loss += loss.item()
                val_batches += 1

        val_loss /= max(val_batches, 1)

        # ── KNN EVALUATION ────────────────────────────────────────────────
        val_accuracy, val_labels, val_prediction = evaluate_knn(
            current_eval_model, train_eval_loader, val_eval_loader,
            DEVICE, normalize=NORMALIZE_EMBEDDINGS
        )

        scheduler.step()
        lr = optimizer.param_groups[0]["lr"]
        lr_history.append(lr)

        is_best = (
            val_accuracy > best_val_accuracy or
            (val_accuracy == best_val_accuracy and val_loss < best_val_loss)
        )

        train_loss_history.append(train_loss)
        val_loss_history.append(val_loss)
        val_acc_history.append(val_accuracy)
        best_prediction_history.append(val_prediction)
        best_labels_history.append(val_labels)
        

        # ── SAVE BEST MODEL ───────────────────────────────────────────────
        saved = ""

        if is_best:
            best_val_accuracy = val_accuracy
            best_val_loss = val_loss
            best_epoch = epoch
            best_labels = val_labels.copy()
            best_prediction = val_prediction.copy()
            model_state, model_state_source = export_model_state(current_eval_model)

            checkpoint = {
                "model_state": model_state,
                "label_map": label_map,
                "train_embeddings": train_embeddings_file,
                "val_embeddings": val_embeddings_file,
                "config": {
                    "input_dim": INPUT_DIM,
                    "hidden_dim": HIDDEN_DIM,
                    "num_layers": NUM_LAYERS,
                    "dropout": DROPOUT,
                    "normalize_embeddings": NORMALIZE_EMBEDDINGS,
                },
                "metadata":{
                    "optimizer": "Adam",
                    "scheduler": "CosineAnnealingWarmRestarts",
                    "lr": LEARNING_RATE,
                    "min_lr": MIN_LR,
                    "scheduler_patience": PATIENCE,
                    "scheduler_factor": FACTOR,
                    "loss": "MultiSimilarityLoss",
                    "alpha": MS_ALPHA,
                    "beta": MS_BETA,
                    "base": MS_BASE,
                    "p_train": P_TRAIN,
                    "k_train": K_TRAIN,
                    "p_val": P_VAL,
                    "k_val": K_VAL,
                    "selection_metric": "val_1nn_accuracy",
                    "train_acc": best_val_accuracy,
                    "train_loss": best_val_loss,
                    "val_acc": val_accuracy,
                    "val_loss": val_loss,
                    "best_epoch": best_epoch,
                }
            }

            atomic_torch_save(checkpoint, best_encoder_file)
            save_embeddings(
                current_eval_model, train_eval_ds, train_paths,
                label_map, DEVICE, train_embeddings_file, normalize=NORMALIZE_EMBEDDINGS
            )
            save_embeddings(
                current_eval_model, val_ds, val_paths,
                label_map, DEVICE, val_embeddings_file, normalize=NORMALIZE_EMBEDDINGS
            )
            saved = "  <- best"

        # ── EMBEDDING DISTANCES  ─────────────────────────────────────────────
        with torch.no_grad():
            train_dists = embedding_distances(current_eval_model, train_eval_loader, DEVICE)
            val_dists   = embedding_distances(current_eval_model, val_eval_loader,   DEVICE)

            train_dists_history.append([train_dists["d_pos"], train_dists["d_neg"], train_dists["diff"]])
            val_dists_history.append([val_dists["d_pos"], val_dists["d_neg"], val_dists["diff"]])

        if is_best:
            best_train_dists = train_dists.copy()
            best_val_dists   = val_dists.copy()

        
        # ── SAVE LOGS ───────────────────────────────────────────────────
        atomic_np_savez(
            training_logs_file,
            epochs = np.arange(1, len(train_loss_history) + 1),
            train_loss = np.array(train_loss_history, dtype=np.float32),
            val_loss = np.array(val_loss_history, dtype=np.float32),
            val_acc = np.array(val_acc_history, dtype=np.float32),
            lr = np.array(lr_history, dtype=np.float32),
            train_dists = np.array(train_dists_history, dtype=np.float32),
            val_dists = np.array(val_dists_history, dtype=np.float32),
            best_train_dists = np.array([
                best_train_dists["d_pos"],
                best_train_dists["d_neg"],
                best_train_dists["diff"],
            ], dtype=np.float32),
            best_val_dists = np.array([
                best_val_dists["d_pos"],
                best_val_dists["d_neg"],
                best_val_dists["diff"],
            ], dtype=np.float32),
            best_epoch = np.array(best_epoch, dtype=np.int32),
            best_val_loss = np.array(best_val_loss, dtype=np.float32),
            best_val_accuracy = np.array(best_val_accuracy, dtype=np.float32),
            best_prediction = np.array(best_prediction),
            best_labels = np.array(best_labels),
        )

        print(
            f"Epoch {epoch:3d} | "
            f"train: {train_loss:.4f} | "
            f"val: {val_loss:.4f} | "
            f"lr: {lr:.2e} | "
            f"val_acc: {val_accuracy:.2%}"
            f"{saved}"
        )

        if early_stopping.step(val_accuracy, is_best=is_best):
            print(f"\n" + "-" * 90)
            print(f"Early stopping at epoch {epoch}")
            print("-" * 90 + "\n")
            break

    print("\n" + "-" * 90)
    print("Training completed")
    print(f"\nBest epoch:         {best_epoch}")
    print(f"Best val loss:      {best_val_loss:.4f}")
    print(f"Best val accuracy:  {best_val_accuracy:.2%}")
    print(f"\nBest train distances: {format_dists(best_train_dists)}")
    print(f"Best val distances:   {format_dists(best_val_dists)}")
    print(f"\nData saved in directory: {artifact_dir}")



if __name__ == "__main__":
    import argparse
    args = argparse.ArgumentParser()
    args.add_argument("--model", type=str, default="transformer")
    args = args.parse_args()
    from Models.Transformer_encoder import TransformerEncoder_model
    from Models.LSTM_encoder import LSTMEncoder
    from Models.BiLSTM_encoder import BiLSTMEncoder
    from Models.GRU_encoder import GRUEncoder
    from Models.BiGRU_encoder import BiGRUEncoder
    
    if args.model == "transformer":
        model = TransformerEncoder_model
    elif args.model == "lstm":
        model = LSTMEncoder
    elif args.model == "bilstm":
        model = BiLSTMEncoder
    elif args.model == "gru":
        model = GRUEncoder
    elif args.model == "bigru":
        model = BiGRUEncoder
    else:
        raise ValueError(f"Unknown model: {args.model}")
    training(model)
