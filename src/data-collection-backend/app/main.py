from fastapi import FastAPI
from app.core.logging import setup_logging
from app.api.v1.video import router as video_router
from app.api.v1.gesture_class import router as gesture_class_router
from app.api.v1.gesture_type import router as gesture_type_router
app = FastAPI(
    title="Backend API",
    description="API for fullstack template",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

setup_logging()

app.include_router(video_router,prefix="/api/v1/video")
app.include_router(gesture_class_router,prefix="/api/v1/gesture_class")
app.include_router(gesture_type_router,prefix="/api/v1/gesture_type")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)
