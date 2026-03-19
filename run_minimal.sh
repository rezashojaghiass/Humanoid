#!/bin/bash

# Check if Docker is running
if ! systemctl is-active --quiet docker; then
        echo "[ERROR] Docker is not running. Please start Docker and try again."
        exit 1
fi

# Check if Riva container is running
RIVA_CONTAINER=$(docker ps --filter "name=riva-speech" --format '{{.Names}}')
if [ -z "$RIVA_CONTAINER" ]; then
        echo "[INFO] Riva container not running. Attempting to start Riva using start_humanoid_calibration.sh..."
        bash /home/reza/Humanoid/start_humanoid_calibration.sh
        sleep 10
fi

# Check if Riva is up at localhost:50051
if ! nc -z localhost 50051; then
        echo "[ERROR] Riva server is not responding at localhost:50051."
        exit 1
fi

echo "✓ Riva is up at localhost:50051"
echo "📋 Running with MINIMAL config (no face, no servos)"
cd /home/reza/Humanoid/robot_sync_app
PYTHONPATH=src python3 -m robot_sync_app.main --config ../config_minimal.yaml --voice --intent chat
