#!/usr/bin/env bash
set -euo pipefail

MODEL_URL="https://storage.googleapis.com/mediapipe-models/holistic_landmarker/holistic_landmarker/float16/latest/holistic_landmarker.task"
OUTPUT_DIR="weights"
OUTPUT_FILE="$OUTPUT_DIR/holistic_landmarker.task"

# Upewnij się, że katalog istnieje
mkdir -p "$OUTPUT_DIR"

echo "Downloading MediaPipe Holistic model..."
if command -v curl >/dev/null 2>&1; then
    curl -L "$MODEL_URL" -o "$OUTPUT_FILE"
elif command -v wget >/dev/null 2>&1; then
    wget -O "$OUTPUT_FILE" "$MODEL_URL"
else
    echo "Error: Neither curl nor wget found. Please install one of them."
    exit 1
fi

echo "Model downloaded to $OUTPUT_FILE"
