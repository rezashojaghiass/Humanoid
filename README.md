# 🤖 Humanoid - Voice-Enabled Humanoid Robot with Synchronized Gestures & Facial Expressions

**Complete integration of robot arm control, speech AI, LiDAR autonomy, and LCD facial animation into a single unified system.**

---

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [First-Page Run & Config (Conversation App)](#-first-page-run--config-conversation-app)
3. [What Runs Where (Important)](#-what-runs-where-important)
4. [System Architecture](#system-architecture)
5. [Quick Start](#quick-start)
6. [Hardware Setup](#hardware-setup)
7. [Software Components](#software-components)
8. [Integration Details](#integration-details)
9. [Configuration Guide](#configuration-guide)
10. [Usage Examples](#usage-examples)
11. [Troubleshooting](#troubleshooting)
12. [Cross-Repository References](#cross-repository-references)

---

## 🎯 Project Overview

This project unifies five specialized robot subsystems into a single voice-enabled humanoid platform:

| Component | Repository | Purpose | Status |
|-----------|-----------|---------|--------|
| **Voice AI** | [ChatBotRobot](https://github.com/rezashojaghiass/ChatBotRobot) | ASR/TTS speech, Bedrock LLM, RAG | ✅ Integrated |
| **Arm Control** | [RobotArmServos](https://github.com/rezashojaghiass/RobotArmServos) | Hand gestures, arm movements, servo control | ✅ Integrated |
| **LCD Face** | [FacialAnimation](https://github.com/rezashojaghiass/FacialAnimation) | Buzz Lightyear facial expressions, lip-sync | 🔄 In Progress |
| **Remote Access** | [VNC_Setup](https://github.com/rezashojaghiass/VNC_Setup) | Headless VNC for Xavier display | ✅ Configured |
| **LiDAR Autonomy** | [LidarUnitree](https://github.com/rezashojaghiass/LidarUnitree) | ROS2 point cloud, navigation | 🔄 Scaffolded |

**Core Requirement:** When the robot speaks, hand gestures and facial expressions synchronize in real-time. Main arm servos are disabled by default (safety first), only fingers move.

---

## 🚀 First-Page Run & Config (Conversation App)

Primary run command:

```bash
cd /mnt/nvme/RobotArmServos/Humanoid/robot_sync_app
PYTHONPATH=src python3 -m robot_sync_app.main --config config/config.yaml --voice --intent chat
```

Primary config:
- `robot_sync_app/config/config.yaml`

Behavior summary:
- Starts in conversation mode.
- If movement intent is detected, it switches to the same calibration short-answer flow.
- Saying `quit` / `chat mode` in movement flow returns to conversation.

Movement entry phrases:
- `movement mode`
- `move mode`
- `control mode`

Short-answer movement pattern:
- `left` / `right`
- `elbow` / `shoulder 1` / `shoulder 2`
- `up` / `down`
- `some more` / `reverse` / `main menu` / `quit`

Finger commands:
- `fingers open`
- `fingers close`
- `fingers wave`
- Side variants like `left fingers open`, `right fingers close`

## ✅ What Runs Where (Important)

### Main application (run this from Xavier)

- Python orchestrator entry point: `robot_sync_app/src/robot_sync_app/main.py`
- This is the command you run each session.

### Arduino firmware (uploaded separately)

- Finger controller firmware: `arduino/finger_servos/finger_servos.ino`
- Motor base firmware: `arduino/motor_base/motor_control.ino`

### Critical clarification

- Running the Python app **does not upload** Arduino code.
- Arduino upload is a separate one-time action (or only when firmware changes).
- Rebooting Xavier does **not erase** Arduino firmware.

### When do you need Arduino upload again?

- Only if you changed `.ino` files
- Or replaced/reset an Arduino board

### How to verify upload already exists

- Run `examples/test_scripts/test_finger_serial.py`
- Run `examples/test_scripts/test_motor_serial.py`
- If both connect/respond, no upload is needed.

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    VOICE INPUT LAYER                         │
│  Microphone (Wireless GO II @ 48kHz) ──► VAD Detection     │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│              SPEECH RECOGNITION (RIVA ASR)                  │
│  Resamples 48kHz→16kHz ──► Riva gRPC ──► Text Output       │
│  Network: localhost:50051 (Docker)                          │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│         LANGUAGE UNDERSTANDING (AWS BEDROCK LLM)            │
│  Text ──► Bedrock API ──► Llama 3.1 70B/8B or Claude 3.5   │
│  Throttling: 1.5s cooldown, 10 retries with backoff         │
└──────────────────────────┬──────────────────────────────────┘
                           │
            ┌──────────────┼──────────────┐
            │              │              │
    ┌───────▼────┐  ┌─────▼──────┐ ┌────▼─────────┐
    │ TTS (RIVA) │  │  GESTURES  │ │ FACIAL EXPR. │
    │ 48kHz      │  │  Arduino   │ │ LCD Display  │
    │ Speaker    │  │ Servo Ctrl │ │ Blender rigs │
    │ USB Audio  │  │ /dev/ttyACM│ │ 30 frames    │
    │ Device 25  │  │ 115200 bps │ │ per emotion  │
    └────────────┘  └────────────┘ └──────────────┘
            │              │              │
            └──────────────┼──────────────┘
                           │
        ┌──────────────────▼──────────────────┐
        │    OPTIONAL: LiDAR AUTONOMY (ROS2) │
        │  Unitree L1 @ 4Hz ──► Navigation   │
        │  (Scaffolded - future integration)  │
        └───────────────────────────────────┘
```
- `storage.local_base_path: /mnt/nvme/adrian/robot_data`

Future AWS switch:
1. set `storage.backend: s3`
2. set `storage.s3_bucket`
3. set `storage.s3_prefix`

No orchestration code changes required.

---

## 4) Prerequisites

- Jetson Xavier with Docker and Riva available
- Arduino connected at `/dev/ttyACM0` (or update config)
- Python 3.8+
- Riva server running at `localhost:50051`

Optional checks:

```bash
docker ps | grep riva-speech
```

---

## ⚡ FIRST TIME SETUP?

**👉 START HERE: [STARTUP.md](STARTUP.md)**

If you want exact on-device locations first (Riva path, model path, scripts, credentials), read:

**👉 [XAVIER_PATHS.md](XAVIER_PATHS.md)**

This prevents unnecessary downloads and reinstall steps.

Returning users → [QUICKSTART.md](QUICKSTART.md) (2-5 min checklist)

---

## 5) Installation (only if dependencies are missing)

From repo root:

```bash
cd /path/to/Humanoid
python3 -m pip install -r robot_sync_app/requirements.txt
```

---

## 6) Audio output device check (for future sessions)

List output-capable devices:

```bash
python3 -c "import pyaudio as p; a=p.PyAudio(); [print(f'{i}: {a.get_device_info_by_index(i)[\"name\"]}') for i in range(a.get_device_count()) if a.get_device_info_by_index(i).get('maxOutputChannels',0)>0]; a.terminate()"
```

Set the selected index in:
- `robot_sync_app/config/config.yaml` → `speech.output_device_index`

Current known value in config:
- `25` (KT USB Audio)

---

## 7) Run commands

From repo root:

```bash
cd /path/to/Humanoid
PYTHONPATH=robot_sync_app/src python3 -m robot_sync_app.main \
  --config robot_sync_app/config/config.yaml \
  --text "Hello Adrian, welcome to quiz time!" \
  --intent quiz
```

Another example:

```bash
PYTHONPATH=robot_sync_app/src python3 -m robot_sync_app.main \
  --config robot_sync_app/config/config.yaml \
  --text "Great job! Let's do one more question." \
  --intent chat
```

---

## 8) What happens at runtime

1. `BehaviorPlanner` selects speech + gesture + face expression
2. TTS starts
3. Face expression set (e.g., `thinking`)
4. Finger gesture starts (e.g., `fingers_point`)
5. TTS audio plays through selected output device
6. Gesture stops
7. Face returns to `neutral`
8. Session metadata saved to storage backend

---

## 9) Troubleshooting

### No speech from speaker
- verify output index with the device listing command
- update `speech.output_device_index`
- verify Riva container is running

### Serial errors
- verify Arduino cable
- verify `gesture.serial_port` in config (`/dev/ttyACM0`)
- ensure no other app is holding the serial port

### Safety block errors
- expected if arm command is attempted while `enable_main_arms=false`
- keep disabled unless supervised and tested

---

## 10) Next extensions

- Replace `LCDStubFaceAdapter` with your real LCD renderer
- Add ASR + LLM conversation loop integration
- Add richer timeline scheduling (word-level gesture timing)
- Add cloud data migration with S3 backend
