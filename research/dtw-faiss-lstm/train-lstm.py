import os
import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Model
from tensorflow.keras.layers import LSTM, Dense, Input, MultiHeadAttention, GlobalAveragePooling1D, Dropout, LayerNormalization, Conv1D, BatchNormalization
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report
from pathlib import Path
from tqdm import tqdm

def load_data(processed_dir, window_size=120, limit=None, step_size=None):
    processed_dir = Path(processed_dir)
    classes = [d.name for d in processed_dir.iterdir() if d.is_dir()]
    classes.sort()
    
    if limit:
        classes = classes[:limit]
        print(f"Limiting to first {limit} classes: {classes}")
    
    X = []
    y = []
    
    EXPECTED_FEATURES = 1662 # 33*4 + 468*3 + 21*3 + 21*3

    print(f"Loading data from {processed_dir} (step_size={step_size})...")
    for class_name in tqdm(classes, desc="Classes"):
        class_dir = processed_dir / class_name
        for csv_file in class_dir.glob("*.csv"):
            data = []
            try:
                import csv
                with open(csv_file, 'r') as f:
                    reader = csv.reader(f)
                    next(reader) # Skip header
                    for row in reader:
                        if not row: continue
                        row_data = [float(x) for x in row[:EXPECTED_FEATURES]]
                        if len(row_data) < EXPECTED_FEATURES:
                            row_data.extend([0.0] * (EXPECTED_FEATURES - len(row_data)))
                        data.append(row_data)
                
                data = np.array(data)
                if len(data) == 0: continue

                if len(data) >= window_size:
                    if step_size:
                        # Data Augmentation: Sliding window
                        for i in range(0, len(data) - window_size + 1, step_size):
                            X.append(data[i:i+window_size])
                            y.append(class_name)
                    else:
                        X.append(data[:window_size])
                        y.append(class_name)
                else:
                    # Padding for short videos
                    padding = np.zeros((window_size - len(data), EXPECTED_FEATURES))
                    padded_data = np.vstack([data, padding])
                    X.append(padded_data)
                    y.append(class_name)
            except Exception as e:
                print(f"Skipping {csv_file} due to error: {e}")
                
    return np.array(X), np.array(y), classes

def build_attention_lstm_model(input_shape, num_classes):
    inputs = Input(shape=input_shape)
    
    # Pre-processing
    x = LayerNormalization()(inputs)
    
    # 1D Convolutions to extract local temporal features (motion patterns)
    x = Conv1D(filters=256, kernel_size=7, padding='same', activation='relu')(x)
    x = BatchNormalization()(x)
    x = Dropout(0.2)(x)
    x = Conv1D(filters=128, kernel_size=5, padding='same', activation='relu')(x)
    x = BatchNormalization()(x)
    x = Dropout(0.2)(x)
    
    # Stacked LSTM layers (User requested 512 -> 256 -> 128)
    x = LSTM(512, return_sequences=True)(x)
    x = Dropout(0.2)(x)
    x = LSTM(256, return_sequences=True)(x)
    x = Dropout(0.2)(x)
    x = LSTM(128, return_sequences=True)(x)
    x = Dropout(0.2)(x)
    
    # Attention layer on top of LSTM
    # MultiHeadAttention is a powerful choice
    attention_output = MultiHeadAttention(num_heads=4, key_dim=32)(x, x)
    attention_output = Dropout(0.2)(attention_output)
    x = LayerNormalization()(x + attention_output) # Residual connection
    
    # Global pooling to collapse the temporal dimension
    x = GlobalAveragePooling1D()(x)
    
    # Dense head
    x = Dense(64, activation='relu')(x)
    x = Dropout(0.2)(x)
    outputs = Dense(num_classes, activation='softmax')(x)
    
    model = Model(inputs=inputs, outputs=outputs)
    return model

def get_args():
    import argparse
    parser = argparse.ArgumentParser(description="Train LSTM model for landmark classification")
    parser.add_argument("--num-classes", type=int, default=None, help="Number of first classes to train on")
    parser.add_argument("--window-size", type=int, default=120, help="Window size (number of frames)")
    parser.add_argument("--step-size", type=int, default=None, help="Step size for sliding window augmentation")
    parser.add_argument("--epochs", type=int, default=50, help="Number of epochs")
    return parser.parse_args()

def main():
    args = get_args()
    
    # Configuration
    PROCESSED_DATA_DIR = "data/custom_dataset-processed"
    WINDOW_SIZE = args.window_size
    BATCH_SIZE = 32
    EPOCHS = args.epochs
    
    # Run configuration
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = Path("runs") / timestamp
    run_dir.mkdir(parents=True, exist_ok=True)
    
    MODEL_SAVE_PATH = run_dir / "lstm_attention_model.keras"

    # Load data
    if not os.path.exists(PROCESSED_DATA_DIR):
        print(f"Error: {PROCESSED_DATA_DIR} not found. Run preprocess-dataset.py first.")
        return

    X, y_raw, class_names = load_data(PROCESSED_DATA_DIR, WINDOW_SIZE, args.num_classes, args.step_size)
    print(f"Dataset loaded: X={X.shape}, y={len(y_raw)}")

    # Encode labels
    label_encoder = LabelEncoder()
    y = label_encoder.fit_transform(y_raw)
    num_classes = len(class_names)

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    # Build model
    input_shape = (WINDOW_SIZE, X.shape[2])
    model = build_attention_lstm_model(input_shape, num_classes)
    
    model.compile(
        optimizer='adam',
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy']
    )
    
    model.summary()

    # Training
    print("Starting training...")
    history = model.fit(
        X_train, y_train,
        validation_data=(X_test, y_test),
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        callbacks=[
            tf.keras.callbacks.EarlyStopping(patience=10, restore_best_weights=True),
            tf.keras.callbacks.ModelCheckpoint(str(MODEL_SAVE_PATH), save_best_only=True)
        ]
    )

    print(f"Training complete. Best model saved to {MODEL_SAVE_PATH}")

    # Evaluate
    print("Evaluating model...")
    y_pred_prob = model.predict(X_test)
    y_pred = np.argmax(y_pred_prob, axis=1)

    # Classification Report
    report = classification_report(y_test, y_pred, target_names=class_names)
    print("\nClassification Report:")
    print(report)
    
    with open(run_dir / "classification_report.txt", "w") as f:
        f.write(report)
        print(f"Classification report saved to {run_dir / 'classification_report.txt'}")

    # Confusion Matrix
    import matplotlib.pyplot as plt
    from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay

    cm = confusion_matrix(y_test, y_pred)
    fig, ax = plt.subplots(figsize=(12, 12))
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=class_names)
    disp.plot(ax=ax, cmap=plt.cm.Blues, xticks_rotation='vertical')
    
    plt.title(f"Confusion Matrix ({timestamp})")
    cm_path = run_dir / "confusion_matrix.png"
    plt.savefig(cm_path, bbox_inches='tight')
    print(f"Confusion matrix saved to {cm_path}")
    plt.show()

if __name__ == "__main__":
    main()
