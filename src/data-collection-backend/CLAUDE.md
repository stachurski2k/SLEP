# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FastAPI backend for video data collection and gesture recognition. Handles video ingestion, MediaPipe hand landmark extraction via Celery workers, and dataset export. Storage uses MinIO (S3-compatible).

## Commands

```bash
# Dependencies
uv sync

# Dev server (port 5000, auto-reload)
uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload

# Database migrations
alembic revision --autogenerate -m "description"
alembic upgrade head
alembic current

# Celery worker
celery -A app.workers.celery_app worker --loglevel=info

# Celery Flower monitoring UI (http://localhost:5555)
celery -A app.workers.celery_app flower --port=5555

# Tests
pytest
pytest tests/path/to/test_file.py::test_name  # single test

# Docker (from this directory)
make docker-build
make docker-run PORT=5000

# Full stack (from parent SLEP/ directory)
docker-compose up -d
```

## Architecture

### Layer Structure

```
app/
  api/v1/         # FastAPI routers — thin, delegate to services
  services/       # Business logic (VideoService, S3Service)
  crud/           # Database operations (async SQLAlchemy)
  models/         # SQLAlchemy ORM models
  schemas/        # Pydantic request/response schemas
  workers/        # Celery app config + task definitions
  db/database.py  # Async engine + session factory
  core/config.py  # Pydantic settings (env vars)
  dependencies.py # FastAPI Depends() providers
```

### Async Database

Uses SQLAlchemy 2.0 async with `asyncpg` driver for the application. Alembic migrations use a **sync** `psycopg2` connection (`config.db_url_sync`). The session lifecycle is managed in `dependencies.py`: auto-commit on success, rollback on error.

### Celery Task Flow

Video upload → `POST /api/v1/video/` → `VideoService.create_video()` → triggers `process_video.delay(video_id)` → worker downloads from S3, runs MediaPipe hand landmark detection, writes CSV, uploads CSV back to S3, updates DB. Worker config: `acks_late=True`, `prefetch_multiplier=1` (serial processing), max 3 retries.

### Job Tracking Models

`ImportVideoJob` and `ExportDatasetJob` have `status` enums (`in_queue`, `processing`, `done`, `error`) for tracking async operations. `ExportedDataset` stores metadata about completed exports.

### S3/MinIO

`S3Service` wraps boto3. All video files and landmark CSVs are stored in MinIO. Supports presigned upload/download URLs. MediaPipe model file is baked into the Docker image at `/app/models/hand_landmarker.task`.

### Infrastructure (docker-compose in parent SLEP/)

- `postgres:17` on port 5432, DB: `slep`
- `redis:7-alpine` on port 6379 (Celery broker + backend)
- `minio` on port 9000 (S3 API), 9001 (web console)
- `data-collection-api` on port 5000
- `data-collection-worker` (Celery)
- `data-collection-flower` on port 5555

### Key Config (`app/core/config.py`)

Pydantic `BaseSettings` — reads from environment or `.env`. Exposes `db_url` (async asyncpg URL) and `db_url_sync` (sync psycopg2 URL for Alembic). Default values point to localhost for local dev.
