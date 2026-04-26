#!/usr/bin/env bash
set -euo pipefail

API_URL="${API_URL:-http://localhost:5000}"
S3_KEY="test/test_upload.txt"
CONTENT="hello from presigned url test"

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

pass() { echo -e "${GREEN}PASS${NC} $1"; }
fail() { echo -e "${RED}FAIL${NC} $1"; exit 1; }

# ── 1. Get presigned upload URL ────────────────────────────────────────────────
echo "── 1. Requesting presigned upload URL..."
UPLOAD_RESPONSE=$(curl -sf -X POST "$API_URL/api/v1/s3/upload-url" \
  -H "Content-Type: application/json" \
  -d "{\"s3_key\": \"$S3_KEY\", \"content_type\": \"text/plain\"}")

UPLOAD_URL=$(echo "$UPLOAD_RESPONSE" | jq -r '.url')
ACTUAL_KEY=$(echo "$UPLOAD_RESPONSE" | jq -r '.key')

[[ "$UPLOAD_URL" != "null" && -n "$UPLOAD_URL" ]] || fail "No upload URL in response: $UPLOAD_RESPONSE"
[[ "$ACTUAL_KEY" != "null" && -n "$ACTUAL_KEY" ]] || fail "No key in response: $UPLOAD_RESPONSE"
pass "Got upload URL (key: $ACTUAL_KEY)"

# ── 2. Upload file via presigned URL ──────────────────────────────────────────
echo "── 2. Uploading file via presigned URL..."
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X PUT "$UPLOAD_URL" \
  -H "Content-Type: text/plain" \
  -d "$CONTENT")

[[ "$HTTP_STATUS" == "200" ]] || fail "Upload failed with HTTP $HTTP_STATUS"
pass "File uploaded (HTTP $HTTP_STATUS)"

# ── 3. Get presigned download URL ─────────────────────────────────────────────
echo "── 3. Requesting presigned download URL..."
DOWNLOAD_RESPONSE=$(curl -sf -X POST "$API_URL/api/v1/s3/download-url" \
  -H "Content-Type: application/json" \
  -d "{\"s3_key\": \"$ACTUAL_KEY\"}")

DOWNLOAD_URL=$(echo "$DOWNLOAD_RESPONSE" | jq -r '.url')

[[ "$DOWNLOAD_URL" != "null" && -n "$DOWNLOAD_URL" ]] || fail "No download URL in response: $DOWNLOAD_RESPONSE"
pass "Got download URL"

# ── 4. Download and verify content ────────────────────────────────────────────
echo "── 4. Downloading and verifying content..."
DOWNLOADED=$(curl -sf "$DOWNLOAD_URL")

[[ "$DOWNLOADED" == "$CONTENT" ]] || fail "Content mismatch. Expected: '$CONTENT', got: '$DOWNLOADED'"
pass "Content matches"

echo ""
echo -e "${GREEN}All tests passed.${NC}"
