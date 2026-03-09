# ⚡ Cold Boot Checklist - 30 Second Version

**When:** Xavier restarts with no Docker running  
**Time:** ~30-40 minutes start-to-finish  
**Location:** `/home/reza/RobotArmServos/Humanoid`

📍 Path map first: [XAVIER_PATHS.md](XAVIER_PATHS.md)

---

## Phase 1: System (5 min)

```bash
cd /home/reza/RobotArmServos/Humanoid
git status  # Verify repo synced
```

## Phase 2: Docker & Riva (10 min)

```bash
# Start Docker
sudo systemctl start docker

# Check local Riva images first (skip pull if found)
docker images --format '{{.Repository}}:{{.Tag}}' | grep -Ei 'riva-speech|nvidia/riva' || true

# Only if missing, pull:
# docker pull nvcr.io/nvidia/riva/riva-speech:2.24.0-l4t-aarch64

# Start Riva from existing Xavier script (preferred)
cd /mnt/nvme/adrian/ChatBotRobot && ./scripts/start_riva.sh

# Verify running
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' | grep -E 'riva|speech' || true
```

## Phase 3: Hardware (10 min)

```bash
# Check USB
lsusb | grep -E "Arduino|FTDI|CH340"  # Should show 2 Arduinos

# Test Arduino #1 (Fingers)
python3 examples/test_scripts/test_finger_serial.py

# Test Arduino #2 (Motors)
python3 examples/test_scripts/test_motor_serial.py

# Find audio devices (write down indices!)
python3 examples/test_scripts/test_audio_devices.py
```

## Phase 4: Config (5 min)

```bash
# Update audio indices in config
nano robot_sync_app/config/config.yaml
# Set: input_device_index: <from step above>
# Set: output_device_index: <from step above>

# Check AWS credentials
cat ~/.aws/credentials  # Should show [bedrock] section
# If missing: aws configure
```

## Phase 5: First Run (2 min)

```bash
# Text mode (safest)
PYTHONPATH=robot_sync_app/src python3 -m robot_sync_app.main \
  --config robot_sync_app/config/config.yaml \
  --text "Hello, I am awake" \
  --intent chat

# Live voice mode
PYTHONPATH=robot_sync_app/src python3 -m robot_sync_app.main \
  --config robot_sync_app/config/config.yaml \
  --intent chat
# Press spacebar to talk, release to process
```

---

## 🚨 Stuck?

→ **Full guide:** [STARTUP.md](STARTUP.md)  
→ **Troubleshooting:** [STARTUP.md#troubleshooting](STARTUP.md#troubleshooting)

---

## Normal Shutdown

```bash
# Stop Python
Ctrl+C

# Stop Riva
docker stop riva-speech riva-models-extract riva-models-download 2>/dev/null || true

# Verify cleanup
docker ps  # Should show no Riva

# Safe to shutdown
sudo shutdown -h now
```
