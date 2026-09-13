# model-service

FastAPI service that predicts a gesture class from an uploaded video.

Pipeline: video -> MediaPipe hand/pose landmarks -> preprocessing (interpolate/smooth/normalize/resample to a fixed length) -> sequence encoder forward pass -> FAISS nearest-neighbor lookup against training embeddings -> predicted label.

The encoder is a metric-learning model (no classifier head), so predictions come from nearest-neighbor search against `train_embeddings.npz`, not a softmax.

## Setup

```bash
uv sync
uv run scripts/fetch_artifacts.py
```

This downloads into `storage/`:
- `storage/encoder/best_encoder.pt` (Google Drive)
- `storage/embeddings/train_embeddings.npz` (Google Drive)
- `storage/mediapipe/hand_landmarker.task`, `pose_landmarker_full.task` (Google's model CDN)

## Run

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 5001 --reload
```

## Endpoints

- `POST /api/v1/predict` - multipart form upload, field name `video`. Returns `{label, score, margin}`.
- `GET /api/v1/health` - `{status, device, num_classes, faiss_size}`.

```bash
curl -F "video=@sample.mp4" http://localhost:5001/api/v1/predict
```

## Configuration

Settings (env vars, prefix `MODEL_SERVICE_`, or a `.env` file):

| Variable | Default | Meaning |
|---|---|---|
| `MODEL_SERVICE_DEVICE` | auto (`cuda` if available) | inference device |
| `MODEL_SERVICE_LANDMARKER_POOL_SIZE` | `2` | number of MediaPipe hand/pose landmarker pairs kept warm for concurrent requests |
| `MODEL_SERVICE_TARGET_LEN` | `60` | frames the sequence is resampled to before the encoder |
| `MODEL_SERVICE_MIN_GESTURE_FRAMES` | `8` | reject videos with fewer detected frames |
| `MODEL_SERVICE_MAX_UPLOAD_MB` | `200` | upload size limit |

## Notes

- `app/model.py`, `app/landmarks.py` are ported from `research/test_version/` (`Models/Transformer_encoder.py`, `DataProcessing/collector.py`, `DataProcessing/preprocessing.py`) so this service has no runtime dependency on the research project. Keep them in sync if the training pipeline changes (e.g. a different target length or preprocessing step would silently break predictions).
- `HandLandmarker`/`PoseLandmarker` run in `RunningMode.VIDEO`, which requires strictly increasing timestamps per instance and isn't safe to call concurrently on one instance. `app/inference.py`'s `LandmarkerPool` keeps a small pool of instances that requests check out/return, each carrying its own running timestamp offset.
