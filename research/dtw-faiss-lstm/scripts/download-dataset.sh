#!/usr/bin/env bash
set -euo pipefail

FILE_ID="${GOOGLE_FOLDER:=https://drive.google.com/file/d/1yqmtwfkg3zqLkRWxL89qo3st7Cfdp2Kf/view?usp=sharing}"
OUTPUT_PATH="data"

# Upewnij się, że katalog istnieje
mkdir -p "$OUTPUT_PATH"

# Wykryj czy to folder czy plik
GDOWN_ARGS=""
if [[ "$FILE_ID" == *"/folders/"* ]]; then
    GDOWN_ARGS="--folder"
fi

# Pobierz przez gdown
uv run --no-sync gdown $GDOWN_ARGS "$FILE_ID" -O "$OUTPUT_PATH"

unzip "$OUTPUT_PATH"/*.zip -d "$OUTPUT_PATH"