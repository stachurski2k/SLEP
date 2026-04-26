FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# 1. Install system libs AND curl
RUN apt-get update && apt-get install -y \
    curl \
    libgl1 \
    libglib2.0-0 \
    libxcb1 \
    libxext6 \
    libxrender1 \
    libgles2 \
    libegl1 \
    libdbus-1-3 \
    && rm -rf /var/lib/apt/lists/*

# 2. Setup user and directories
RUN groupadd --system --gid 999 nonroot \
    && useradd --system --gid 999 --uid 999 --create-home nonroot
RUN mkdir -p /app/models && chown -R nonroot:nonroot /app/models

# 3. Download the model as ROOT (so curl works) but save to the owned folder
RUN curl -L https://storage.googleapis.com/mediapipe-models/holistic_landmarker/holistic_landmarker/float16/1/holistic_landmarker.task \
    -o /app/models/holistic_landmarker.task \
    && chown nonroot:nonroot /app/models/holistic_landmarker.task

WORKDIR /app

# UV Settings
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_NO_DEV=1

# 4. Install dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project

# 5. Copy source code
COPY --chown=nonroot:nonroot . /app

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked

ENV PATH="/app/.venv/bin:$PATH"

ENTRYPOINT []

# 6. Final switch to non-root
USER nonroot