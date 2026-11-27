FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Biblioteki systemowe wymagane przez OpenCV i MediaPipe
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libgles2 \
    libegl1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_NO_DEV=1
ENV PYTHONUNBUFFERED=1

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project

COPY . /app

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 5001

# Artefakty (encoder, embeddingi, modele MediaPipe) trafiają do /app/storage;
# skrypt pomija pliki, które już istnieją.
CMD ["sh", "-c", "python scripts/fetch_artifacts.py && uvicorn app.main:app --host 0.0.0.0 --port 5001"]
