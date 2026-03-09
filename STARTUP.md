# 🚀 STARTUP GUIDE - Cold Boot from Scratch

**Use this guide when you restart your Xavier and have no Docker running.**

This guide assumes a fresh boot or clean state and takes you from nothing to a fully operational robot voice system.

---

## Table of Contents

1. [Pre-Startup Checklist](#pre-startup-checklist)
2. [Phase 1: System Verification (5 min)](#phase-1-system-verification-5-min)
3. [Phase 2: Docker & Riva Setup (10 min)](#phase-2-docker--riva-setup-10-min)
4. [Phase 3: Hardware Verification (10 min)](#phase-3-hardware-verification-10-min)
5. [Phase 4: Python Environment (5 min)](#phase-4-python-environment-5-min)
6. [Phase 5: First Run (2 min)](#phase-5-first-run-2-min)
7. [Troubleshooting](#troubleshooting)

---

## Pre-Startup Checklist

### Know your Xavier paths first (important)

Before doing any install/pull actions, read:

- [XAVIER_PATHS.md](XAVIER_PATHS.md)

This tells you exactly where Riva, models, scripts, credentials, and project files live on your current Jetson.

Before you begin, verify hardware is connected:

```bash
# Check USB connections
lsusb | grep -E "Arduino|FTDI|CH340"
# Should see:
#   Arduino Mega #1 (FTDI) at /dev/ttyACM0
#   Arduino Mega #2 (CH340) at /dev/ttyUSB0

# Check audio devices
arecord -l | head -5
aplay -l | head -5
# Should see:
#   Wireless GO II microphone (input)
#   KT USB Speaker (output)
```

If devices missing, check physical connections and restart Xavier.

---

## Phase 1: System Verification (5 min)

Navigate to the Humanoid directory:

```bash
cd /home/reza/RobotArmServos/Humanoid
pwd
# Should output: /home/reza/RobotArmServos/Humanoid
```

Verify repo is synced:

```bash
git status
# Should show: "Your branch is up to date with 'origin/master'"
git log --oneline -3
# Should show recent commits including consolidation work
```

---

## Phase 2: Docker & Riva Setup (10 min)

### Step 1: Verify Docker is Running

```bash
docker ps
# If output is empty or shows error, Docker isn't running
```

**If Docker isn't running:**

```bash
# Start Docker daemon
sudo systemctl start docker
sudo systemctl status docker
# Should show "active (running)"

# Add user to docker group (permanent, one-time only)
sudo usermod -a -G docker $USER
newgrp docker
```

### Step 2: Pull Latest Riva Container

⚠️ **Do not pull first. Check first.**

```bash
# If you already see riva-speech images, skip docker pull
docker images --format '{{.Repository}}:{{.Tag}}' | grep -Ei 'riva-speech|nvidia/riva' || true
```

Only if no Riva image is present:

```bash
docker pull nvcr.io/nvidia/riva/riva-speech:2.24.0-l4t-aarch64
```

This downloads the speech recognition/synthesis engine (~8GB). May take 5-10 min depending on network.

**Important:** If this fails with network error, ensure Xavier has internet access:

```bash
ping 8.8.8.8
# Should show responses, not "Network unreachable"
```

### Step 3: Start Riva Server

Use your existing Xavier startup script first (preferred):

```bash
cd /mnt/nvme/adrian/ChatBotRobot
./scripts/start_riva.sh
```

This script points to your local quickstart directory and local model repository:

- `/mnt/nvme/adrian/riva/riva_quickstart_arm64_v2.19.0`
- `/mnt/nvme/adrian/riva/riva_quickstart_arm64_v2.19.0/model_repository`

Only use the generic `docker run` fallback if your script path is missing.

Fallback command:

```bash
# Start Riva on port 50051 with GPU support
docker run --rm --gpus all \
  -p 50051:50051 \
  nvcr.io/nvidia/riva/riva-speech:2.24.0-l4t-aarch64 \
  riva_start.sh
```

Watch the output. **Wait for this message:**

```
[riva_server.cc:main] Started server ...
[riva_server.cc:main] Accepting requests at port 50051
```

**Then press Ctrl+Z to background it** (it will continue running):

```
^Z
[1]+  Stopped   docker run ...
bg
# Now Riva runs in background while you continue
```

### Step 4: Verify Riva is Accessible

Open **a new terminal** and test:

```bash
python3 -c "from riva.client import Client; c = Client('localhost'); print(c.get_version())"
# Should output version info, not connection errors
```

**If this fails:**

```bash
# Check container is still running
docker ps | grep riva
# Should show the running container

# Check port is open
netstat -tuln | grep 50051
# Should show LISTEN on 50051
```

---

## Phase 3: Hardware Verification (10 min)

### Step 1: Check Serial Connections

```bash
# List all serial ports
ls -la /dev/ttyACM* /dev/ttyUSB* 2>/dev/null
```

Expected output:

```
/dev/ttyACM0    ← Arduino Mega #1 (FTDI Official)
/dev/ttyUSB0    ← Arduino Mega #2 (CH340 Clone)
```

**If either is missing:**

1. Check USB cable physical connection
2. Verify Arduino has power
3. Check for LED indicators on Arduino boards
4. Restart Arduino with: `sudo systemctl restart systemd-udevd`

### Step 2: Test Arduino #1 (Finger Servos)

```bash
python3 examples/test_scripts/test_finger_serial.py
```

Expected output:

```
✓ Arduino #1 connected at /dev/ttyACM0 (115200 baud)
✓ Firmware: Finger Servo Controller v1.0
✓ All 10 servos detected
Ready to receive gesture commands
```

**If it fails:**

See [Troubleshooting: Arduino Serial Errors](#arduino-serial-errors)

### Step 3: Test Arduino #2 (Motor Base)

```bash
python3 examples/test_scripts/test_motor_serial.py
```

Expected output:

```
✓ Arduino #2 connected at /dev/ttyUSB0 (9600 baud)
✓ Motor controller initialized
✓ Waiting for PS2 controller input...
```

**If it fails:**

See [Troubleshooting: Motor Connection Issues](#motor-connection-issues)

### Step 4: Verify Audio Devices

```bash
python3 examples/test_scripts/test_audio_devices.py
```

Expected output:

```
INPUT DEVICES:
  Device 8: Wireless GO II Mic (48000 Hz) ← Microphone
  Device 12: Internal Audio (48000 Hz)

OUTPUT DEVICES:
  Device 25: KT USB Speaker (48000 Hz) ← Speaker
  Device 26: Internal Audio (48000 Hz)
```

Make note of the device indices (8, 25 in example above). You'll need these next.

---

## Phase 4: Python Environment (5 min)

### Step 1: Update Audio Config

Based on output from Phase 3 Step 4, update audio device indices:

```bash
nano robot_sync_app/config/config.yaml
```

Find and update these lines:

```yaml
speech:
  audio:
    input_device_index: 8      # ← From test_audio_devices.py output
    output_device_index: 25    # ← From test_audio_devices.py output
    sample_rate: 48000
```

Save with: `Ctrl+X`, then `Y`, then `Enter`

### Step 2: Verify AWS Bedrock Credentials

Check if credentials are already configured:

```bash
cat ~/.aws/credentials
# Should show [bedrock] or [default] section with aws_access_key_id
```

**If missing, configure now:**

```bash
aws configure
# Enter AWS credentials when prompted
# Or set environment variables:
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="us-west-2"
```

### Step 3: Install/Update Python Dependencies

```bash
cd /home/reza/RobotArmServos/Humanoid
pip3 install -r robot_sync_app/requirements.txt
```

This installs:
- `boto3` (AWS SDK)
- `riva-client` (Riva gRPC)
- `pyaudio` (microphone/speaker)
- `pyyaml` (config files)

---

## Phase 5: First Run (2 min)

### Simple Test: Text-Only Mode

```bash
cd /home/reza/RobotArmServos/Humanoid
PYTHONPATH=robot_sync_app/src python3 -m robot_sync_app.main \
  --config robot_sync_app/config/config.yaml \
  --text "Hello, I am awake" \
  --intent chat
```

Expected behavior:

1. ✓ Python script starts
2. ✓ Riva synthesizes the text (1-2 sec)
3. ✓ Speaker plays audio
4. ✓ Finger gestures activate

**If this works, proceed to live voice mode.**

### Live Voice Mode: Press-to-Talk

```bash
cd /home/reza/RobotArmServos/Humanoid
PYTHONPATH=robot_sync_app/src python3 -m robot_sync_app.main \
  --config robot_sync_app/config/config.yaml \
  --intent chat
```

Now:
1. **Press spacebar** to start listening (green indicator)
2. **Speak your message** (robot should echo it back)
3. **Release spacebar** to process
4. **Wait 2-3 seconds** for AWS Bedrock LLM response
5. **Hear robot speak** and see finger gestures sync

To exit: Press `Ctrl+C`

---

## Shutdown Sequence

When done:

```bash
# 1. Stop Python app (if running)
# Press Ctrl+C

# 2. Stop Riva Docker
docker stop $(docker ps -q --filter ancestor=nvcr.io/nvidia/riva:latest)

# 3. Verify cleanup
docker ps
# Should show no Riva container

# 4. Safe to shut down Xavier
sudo shutdown -h now
```

---

## Troubleshooting

### Docker Won't Start

**Symptom:** `Cannot connect to Docker daemon`

```bash
# Check Docker service
systemctl status docker

# If inactive, start it
sudo systemctl start docker

# If that fails, restart Docker
sudo systemctl restart docker

# Check logs
journalctl -u docker -n 20
```

### Riva Container Won't Pull

**Symptom:** `docker pull nvcr.io/nvidia/riva:latest` fails

```bash
# Check internet connection
ping google.com

# Check Docker can access internet
docker run --rm alpine ping -c 3 google.com

# If Xavier can't reach outside, configure proxy (if on corporate network)
# Or use local Riva image if pre-cached
docker images | grep riva
```

### Riva Connection Error

**Symptom:** `Could not connect to gRPC server at localhost:50051`

```bash
# 1. Verify container is running
docker ps | grep riva
# If no output, container crashed

# 2. Check container logs
docker logs <container_id>
# Look for startup errors

# 3. Verify port is bound
netstat -tuln | grep 50051
# Should show LISTEN

# 4. Verify gRPC is responding
python3 -c "import grpc; print('gRPC OK')"
# If import fails, install: pip3 install grpcio
```

### Arduino Serial Errors

**Symptom:** `Permission denied: /dev/ttyACM0` or connection timeout

```bash
# Check device exists
ls -la /dev/ttyACM0

# If permission denied, fix permissions
sudo usermod -a -G dialout $USER
newgrp dialout

# Check device is not in use
lsof /dev/ttyACM0
# If another process owns it, kill it or restart Arduino

# Reset Arduino connection
sudo systemctl restart systemd-udevd
ls -la /dev/ttyACM0
# Should show read+write permissions for user
```

**Symptom:** `Serial port not found at /dev/ttyACM0`

```bash
# Check what ports exist
ls /dev/tty*

# List connected USB devices
lsusb -v | grep -A5 Arduino

# Arduino might be on different port (ttyUSB0, ttyACM1, etc.)
# Update config.yaml with correct port
nano robot_sync_app/config/config.yaml
# Change: serial.finger_port: /dev/ttyACM0 (or whatever you found)
```

### Motor Connection Issues

**Symptom:** `Failed to connect to motor controller`

```bash
# Check Arduino #2 is accessible
ls -la /dev/ttyUSB0

# If missing, it might be on ttyACM1
ls /dev/tty* | grep -E "ACM|USB"

# Arduino #2 uses 9600 baud (not 115200)
# Verify config.yaml has:
grep -A2 "motor_port:" robot_sync_app/config/config.yaml
# Should show: baud_rate: 9600

# Test with minicom
sudo apt-get install minicom
minicom -D /dev/ttyUSB0 -b 9600
# Should show motor status, Ctrl+A Q to exit
```

### Audio Device Not Found

**Symptom:** `Could not find audio input/output device`

```bash
# List all audio devices
python3 examples/test_scripts/test_audio_devices.py

# If Wireless GO II missing, check USB connection
lsusb | grep -i audio

# If KT Speaker missing, ensure powered on and USB connected
# Restart audio system
pulseaudio -k  # Kill pulseaudio daemon
sleep 2
pulseaudio --daemonize  # Restart it

# Re-test devices
python3 examples/test_scripts/test_audio_devices.py
```

### Python Dependencies Missing

**Symptom:** `ModuleNotFoundError: No module named 'riva'` or similar

```bash
# Reinstall all dependencies
pip3 install --upgrade pip
pip3 install -r robot_sync_app/requirements.txt

# For specific missing modules:
pip3 install boto3 riva-client pyaudio pyyaml

# If riva-client fails, try:
pip3 install --no-cache-dir riva-client

# Verify installation
python3 -c "import riva.client; print('riva-client OK')"
```

### AWS Bedrock Access Denied

**Symptom:** `An error occurred (AccessDenied) when calling the InvokeModel operation`

```bash
# Check AWS credentials are set
env | grep AWS_

# Verify credentials are valid
aws sts get-caller-identity
# Should show your AWS account ID

# Check Bedrock model access
aws bedrock list-foundation-models --region us-west-2 | grep -i claude
# Should show available models

# If empty, you haven't requested model access yet
# Go to: https://console.aws.amazon.com/bedrock/
# Click "Model access" → Request access to Claude 3.5 or Llama
```

### Voice Not Syncing with Gestures

**Symptom:** Finger servos move but don't match speech timing

```bash
# This is expected - check timing is reasonable
# Voice should start within 1-2 seconds of gesture command

# If severely out of sync:
# 1. Check Arduino #1 is getting commands
python3 examples/test_scripts/test_finger_serial.py
# Manually send gesture: wave

# 2. Check serial latency
time echo '{"type":"gesture","gesture":"wave"}' > /dev/ttyACM0
# Should be <100ms round trip

# 3. Increase gesture duration in config
nano robot_sync_app/config/config.yaml
# Increase: gestures.default_duration_ms: 2000 (from 1500)
```

---

## Quick Reference: What Gets Started

| Component | Command | Port | Check |
|-----------|---------|------|-------|
| **Docker Daemon** | `sudo systemctl start docker` | - | `docker ps` |
| **Riva Server** | `docker run ... riva:latest` | 50051 | `netstat -tuln \| grep 50051` |
| **Arduino #1** | Connected at startup | /dev/ttyACM0 | `python3 test_finger_serial.py` |
| **Arduino #2** | Connected at startup | /dev/ttyUSB0 | `python3 test_motor_serial.py` |
| **Microphone** | PyAudio auto-detects | - | `python3 test_audio_devices.py` |
| **Speaker** | PyAudio auto-detects | - | `python3 test_audio_devices.py` |
| **Python App** | `python3 -m robot_sync_app.main` | stdin | Console output |

---

## Next Steps After Startup

Once the robot is running:

1. **Test Gestures:** See [examples/gesture_patterns/GESTURES.md](examples/gesture_patterns/GESTURES.md)
2. **Configure Responses:** Edit `robot_sync_app/config/prompts.yaml`
3. **Add Facial Expressions:** Populate `assets/facial_expressions/`
4. **Enable Arm Servos:** Change `safety.enable_main_arms: true` in config (dangerous!)
5. **Integrate LiDAR:** Follow [references/lidar_unitree/LIDAR_ROS2_GUIDE.md](references/lidar_unitree/LIDAR_ROS2_GUIDE.md)

---

## Support

If you get stuck:

1. **Check the Logs:** Python logs go to stdout, Docker logs visible with `docker logs <container>`
2. **Review Hardware Docs:** [hardware/pinouts/PIN_MAPPING.md](hardware/pinouts/PIN_MAPPING.md)
3. **Examine Config:** [robot_sync_app/config/config.yaml](robot_sync_app/config/config.yaml)
4. **Run Tests:** All three `examples/test_scripts/*.py` files are your friends
5. **Check Troubleshooting Above:** 90% of issues covered

---

**Good luck! Your robot is ready to talk. 🎙️🤖**
