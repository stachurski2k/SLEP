# RealTime_DynamicGesture_Recognition

A real-time dynamic gesture recognition system. The project uses MediaPipe hand and pose landmarks, sequence encoders for gesture embeddings, FAISS similarity search, and optional DTW sequence matching.

## Key Features

- Landmark extraction from video files with MediaPipe Hands and Pose.
- Sequence preprocessing: missing-value interpolation, static-frame removal, smoothing, normalization, and resampling.
- Gesture encoder training with LSTM, GRU, BiLSTM, BiGRU, and Transformer models.
- Embedding learning with `MultiSimilarityLoss`.
- FAISS similarity index generation.
- Real-time gesture recognition from a camera stream.
- Optional DTW-based comparison for temporal gesture sequences.

## Pipeline

```text
Dataset/*.mp4
    -> DataProcessing/collector.py
    -> Features/*.npy
    -> TrainModel/train.py
    -> Models/*_Checkpoints/best_encoder.pt
    -> Recognition/build_faiss_db.py
    -> Recognition/*_db/index.faiss
    -> Recognition/live_recognition.py
```

## Repository Structure

```text
DataProcessing/       landmark extraction, preprocessing, augmentation, and data splitting
Dataset/              input videos grouped by gesture class
Features/             extracted landmark sequences saved as .npy files
MediapipeModels/      MediaPipe .task model files
Models/               encoder definitions and saved checkpoints
Recognition/          FAISS, DTW, index building, and live recognition
TrainModel/           training loop, sampler, embedding metrics, and training utilities
Diagnostic/           diagnostic notebooks and helper scripts
```

## Requirements

The project is written in Python and uses:

- PyTorch,
- MediaPipe,
- OpenCV,
- FAISS CPU,
- dtaidistance,
- pytorch-metric-learning,
- NumPy, SciPy, scikit-learn, pandas, and plotly.

Install the dependencies:

```bash
pip install -r requirements.txt
```

## Data Preparation

Place video recordings in `Dataset/`, grouped by gesture class:

```text
Dataset/
  gesture_name_1/
    sample_001.mp4
    sample_002.mp4
  gesture_name_2/
    sample_001.mp4
```

Then run landmark extraction:

```bash
python DataProcessing/collector.py
```

The extracted sequences are saved in `Features/` as `.npy` files. Each sequence contains 144 features per frame:

- 6 upper-body pose points,
- 21 left-hand points,
- 21 right-hand points,
- `x`, `y`, and `z` coordinates for each point.

## Model Training

Training uses the processed sequences from `Features/`. The script saves checkpoints and embeddings in the selected model directory:

```bash
python TrainModel/train.py
```

You can also choose the encoder explicitly:

```bash
python TrainModel/train.py --model lstm
python TrainModel/train.py --model gru
python TrainModel/train.py --model bilstm
python TrainModel/train.py --model bigru
python TrainModel/train.py --model transformer
```

Training artifacts are saved to:

```text
Models/<ModelName>_Checkpoints/
  best_encoder.pt
  train_embeddings.npz
  val_embeddings.npz
  training_logs.npz
```

Available encoder architectures:

- `LSTMEncoder`,
- `GRUEncoder`,
- `BiLSTMEncoder`,
- `BiGRUEncoder`,
- `TransformerEncoder`.

The model used by the FAISS and live-recognition scripts can be changed in files such as `Recognition/build_faiss_db.py` and `Recognition/live_recognition.py`.

## Building the FAISS Database

After training, build the similarity index from the training embeddings:

```bash
python Recognition/build_faiss_db.py
```

For the default `TransformerEncoder`, the database is saved to:

```text
Recognition/TransformerEncoder_db/
  index.faiss
  index_labels.npz
```

FAISS is used for fast nearest-neighbor retrieval, while DTW can be used for more precise temporal sequence comparison.

## Real-Time Recognition

After preparing the model checkpoint and FAISS database, run:

```bash
python Recognition/live_recognition.py
```

The script reads frames from the camera, detects active gesture segments, buffers the landmark sequence, preprocesses it, and returns the most similar gesture class.

## Diagnostics and Experiments

The `Diagnostic/` directory contains training notebooks and helper scripts for individual model architectures:

- `training_LSTM.ipynb`,
- `training_GRU.ipynb`,
- `training_BiLSTM.ipynb`,
- `training_BiGRU.ipynb`,
- `training_Transformer.ipynb`,
- `diagnose_video.py`,
- `check_all_features.py`.

## Notes

- MediaPipe model files should be stored in `MediapipeModels/`.
- Training data, checkpoints, and FAISS indexes can be large, so they are usually not committed to the repository.
- If you change the architecture used for training, update the model selection in the FAISS-building and live-recognition scripts as well.

