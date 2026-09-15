import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from shared.database import engine, Base
# Import modeli, aby zarejestrować je w Base.metadata przed wywołaniem create_all
import modules.users.infrastructure.models  # noqa: F401
from modules.users.presentation.controllers import user_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("language-learning-backend")


@asynccontextmanager
async def lifespan(app: FastAPI):

    try:
        logger.info("Database Initialization and table creation...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Tables in database initialize sucessfully")
    except Exception as e:
        logger.warning(
            f"Failed to initialize database (check if database is running): {e}"
        )

    yield

    logger.info("Closing connection pool...")
    await engine.dispose()
    logger.info("Connection pool closed.")


app = FastAPI(
    title="Language Learning Backend API",
    description="API SLEP",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_router, prefix="/api/v1")
app.include_router(user_router)


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "ok",
        "service": "language-learning-backend",
        "version": "1.0.0",
    }


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Language Learning API działa poprawnie",
        "docs": "/docs",
        "health": "/health",
        "users_api": "/api/v1/users",
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
