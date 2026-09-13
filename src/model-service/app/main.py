import os

# Must be set before mediapipe is imported anywhere (via app.inference / app.landmarks).
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
os.environ.setdefault("GLOG_minloglevel", "2")
os.environ.setdefault("ABSL_LOGGING_MIN_LEVEL", "2")

import asyncio
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from pydantic import BaseModel

from app.config import get_settings
from app.inference import InferenceService, NoGestureDetectedError, PoolExhaustedError

try:
    from absl import logging as absl_logging

    absl_logging.set_verbosity(absl_logging.ERROR)
except ImportError:
    pass

ALLOWED_CONTENT_TYPES = {"video/mp4", "video/quicktime", "video/x-msvideo", "video/webm"}


class PredictionResponse(BaseModel):
    label: str
    score: float
    margin: float


class HealthResponse(BaseModel):
    status: str
    device: str
    num_classes: int
    faiss_size: int


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    app.state.inference_service = InferenceService.from_settings(settings)
    app.state.settings = settings
    try:
        yield
    finally:
        app.state.inference_service.close()


app = FastAPI(
    title="Gesture Recognition Model Service",
    description="Predicts a gesture class from an uploaded video via a trained sequence encoder + FAISS lookup.",
    version="0.1.0",
    lifespan=lifespan,
)


def get_inference_service(request: Request) -> InferenceService:
    return request.app.state.inference_service


@app.post("/api/v1/predict", response_model=PredictionResponse)
async def predict(request: Request, video: UploadFile = File(...)) -> PredictionResponse:
    if video.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=415, detail=f"Unsupported content type: {video.content_type}")

    settings = request.app.state.settings
    contents = await video.read()

    max_bytes = settings.max_upload_mb * 1024 * 1024
    if len(contents) > max_bytes:
        raise HTTPException(status_code=413, detail=f"Video exceeds {settings.max_upload_mb} MB limit")

    suffix = Path(video.filename or "upload.mp4").suffix or ".mp4"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(contents)
        tmp_path = Path(tmp.name)

    inference_service = get_inference_service(request)
    try:
        result = await asyncio.to_thread(inference_service.predict, tmp_path)
    except NoGestureDetectedError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except PoolExhaustedError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    finally:
        tmp_path.unlink(missing_ok=True)

    return PredictionResponse(label=result.label, score=result.score, margin=result.margin)


@app.get("/api/v1/health", response_model=HealthResponse)
def health(request: Request) -> HealthResponse:
    inference_service = get_inference_service(request)
    return HealthResponse(
        status="ok",
        device=inference_service.device,
        num_classes=len(inference_service.id_to_label),
        faiss_size=int(inference_service.faiss_index.ntotal),
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=5001, reload=True)
