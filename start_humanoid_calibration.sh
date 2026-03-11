#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$ROOT_DIR/robot_sync_app"
CONFIG_PATH="$APP_DIR/config/config.calibration.yaml"
FALLBACK_CONFIG_PATH="$APP_DIR/config/config.yaml"
SERIAL_PORT="/dev/ttyACM0"

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  echo "Usage: $0"
  echo "Starts dedicated arm calibration voice mode."
  exit 0
fi

if [[ ! -d "$APP_DIR" ]]; then
  echo "[ERROR] App directory not found: $APP_DIR"
  exit 1
fi

if [[ ! -f "$CONFIG_PATH" ]]; then
  echo "[WARN] Calibration config not found: $CONFIG_PATH"
  if [[ -f "$FALLBACK_CONFIG_PATH" ]]; then
    CONFIG_PATH="$FALLBACK_CONFIG_PATH"
    echo "[WARN] Falling back to: $CONFIG_PATH"
  else
    echo "[ERROR] No valid config found."
    exit 1
  fi
fi

echo "[INFO] Checking Riva container..."
if docker ps --format '{{.Names}}' | grep -qx 'riva-speech'; then
  echo "[OK] riva-speech is running"
else
  echo "[WARN] riva-speech is not running. Attempting to start it..."
  if docker ps -a --format '{{.Names}}' | grep -qx 'riva-speech'; then
    docker start riva-speech >/dev/null
    echo "[OK] riva-speech started"
  else
    echo "[ERROR] riva-speech container not found. Start Riva first, then run again."
    exit 1
  fi
fi

echo "[INFO] Checking Arduino serial port..."
if [[ -e "$SERIAL_PORT" ]]; then
  echo "[OK] Found $SERIAL_PORT"
else
  echo "[ERROR] $SERIAL_PORT not found. Calibration mode requires the Arduino."
  exit 1
fi

echo "[INFO] Starting arm calibration mode..."
cd "$APP_DIR"
PYTHONPATH=src python3 -m robot_sync_app.main \
  --config "$CONFIG_PATH" \
  --voice \
  --intent arm_calibration
