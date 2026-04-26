from fastapi import FastAPI
from app.core.logging import setup_logging
from app.api.v1.videos import router as videos_router
from app.api.v1.s3 import router as s3_router
from app.api.v1.datasets import router as datasets_router
from app.api.v1.exported_datasets import router as exported_datasets_router
from app.api.v1.export_dataset_jobs import router as export_dataset_jobs_router
from app.api.v1.import_video_jobs import router as import_video_jobs_router
from app.api.v1.gesture_classes import router as gesture_classes_router
from app.api.v1.gesture_types import router as gesture_types_router

app = FastAPI(
    title="Backend API",
    description="API for fullstack template",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

setup_logging()

app.include_router(videos_router, prefix="/api/v1")
app.include_router(s3_router, prefix="/api/v1")
app.include_router(datasets_router, prefix="/api/v1")
app.include_router(exported_datasets_router, prefix="/api/v1")
app.include_router(export_dataset_jobs_router, prefix="/api/v1")
app.include_router(import_video_jobs_router, prefix="/api/v1")
app.include_router(gesture_classes_router, prefix="/api/v1")
app.include_router(gesture_types_router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)
