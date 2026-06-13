#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
LAN_IP="${FITLOG_LAN_IP:-$(ipconfig getifaddr en0 2>/dev/null || true)}"
API_PORT="${FITLOG_API_PORT:-8000}"
EXPO_PORT="${FITLOG_EXPO_PORT:-8082}"
IMAGE_ANALYSIS_PROVIDER="${FITLOG_IMAGE_ANALYSIS_PROVIDER:-demo}"

if [[ -z "$LAN_IP" ]]; then
  LAN_IP="$(ifconfig | awk '/inet 192\.168\.|inet 10\.|inet 172\.(1[6-9]|2[0-9]|3[01])\./ { print $2; exit }')"
fi

if [[ -z "$LAN_IP" ]]; then
  echo "Unable to detect a private LAN IP. Set FITLOG_LAN_IP and retry." >&2
  exit 1
fi

cleanup() {
  if [[ -n "${API_PID:-}" ]]; then
    kill "$API_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

echo "Fitlog API: http://${LAN_IP}:${API_PORT}"
echo "Expo Go: exp://${LAN_IP}:${EXPO_PORT}"
echo "Image analysis: ${IMAGE_ANALYSIS_PROVIDER}"

cd "$ROOT_DIR"
FITLOG_IMAGE_ANALYSIS_PROVIDER="$IMAGE_ANALYSIS_PROVIDER" \
  "$ROOT_DIR/.venv/bin/uvicorn" app.main:app \
  --app-dir services/api \
  --host 0.0.0.0 \
  --port "$API_PORT" &
API_PID=$!

cd "$ROOT_DIR/apps/mobile"
EXPO_PUBLIC_API_BASE_URL="http://${LAN_IP}:${API_PORT}/api/v1" \
  npx expo start --lan --port "$EXPO_PORT"
