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

**Quick-start (from home folder):**

```bash
~/run_conversation_app.sh
```

Or manually from repo:

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
┌──────────────────────────────────────────────────────────────┐
│                DISPLAY MANAGEMENT (NEW)                      │
│  xset screen blanking: ON when app runs, OFF when idle      │
│  Timeout: 5s → LCD blanks (power saving mode)               │
└──────────────────────────┬───────────────────────────────────┘
                           │ (Display enabled)
┌──────────────────────────▼──────────────────────────────────┐
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

**Display Control Details:**
- **Mechanism:** `xset s blank` and `xset s noblank` commands (X11 screen blanking)
- **Why not DPMS?** DPMS not available on Jetson Xavier
- **Script:** [run_robot.sh](run_robot.sh) lines 43-56 (display ON) and 75-83 (display OFF)
- **Test:** Run `bash test_display.sh` to verify display control works

---
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

---

## 📚 Documentation Files Guide

**All markdown files in this project with their purposes:**

| File | Purpose | Read When | Time |
|------|---------|-----------|------|
| **[README.md](README.md)** | 📖 **START HERE** - Project overview, architecture, quick start | First time using the robot | 5 min |
| **[QUICKSTART.md](QUICKSTART.md)** | ⚡ Daily use checklist - Riva, audio, run app | Every session (after cold boot) | 2 min |
| **[STARTUP.md](STARTUP.md)** | 🚀 Complete cold boot guide - Docker, Riva, hardware, Python | Xavier restarted or first setup | 30 min |
| **[XAVIER_PATHS.md](XAVIER_PATHS.md)** | 🗺️ Exact file locations on Jetson - models, config, scripts | Before any install/download | 5 min |
| **[INDEX.md](INDEX.md)** | 📑 Navigation guide & file directory | Need to find a specific file | 3 min |
| **[INTEGRATION_SUMMARY.md](INTEGRATION_SUMMARY.md)** | ✅ Session summary - what was done, status, next steps | End of session or session handoff | 10 min |
| **[docs/INTEGRATION.md](docs/INTEGRATION.md)** | 🔗 Cross-repository integration details (5 external repos) | Understanding overall system architecture | 15 min |
| **[docs/SERVO_LOGIC.md](docs/SERVO_LOGIC.md)** | 🎮 Servo control logic - movement patterns, calibration | Debugging servo behavior or calibration | 10 min |
| **[docs/SERVO_QUICK_REFERENCE.md](docs/SERVO_QUICK_REFERENCE.md)** | 📋 Quick servo command reference | Testing individual servo movements | 3 min |
| **[CONSOLIDATION_COMPLETE.md](CONSOLIDATION_COMPLETE.md)** | 📦 Integration completion summary | Understanding what was consolidated | 10 min |
| **[MULTIPROCESSING_FIX.md](MULTIPROCESSING_FIX.md)** | 🔧 Multiprocessing bug fix details | Troubleshooting voice/gesture sync issues | 5 min |
| **[COLDBOOT.md](COLDBOOT.md)** | ❄️ Cold boot procedures & recovery | System recovery after unexpected shutdown | 10 min |
| **[UPDATES_FROM_CHATBOT.md](UPDATES_FROM_CHATBOT.md)** | 🔄 Updates synchronized from ChatBotRobot repo | Tracking cross-repo changes | 5 min |
| **[robot_sync_app/README.md](robot_sync_app/README.md)** | 🤖 App-specific documentation | Understanding app internals | 15 min |

---

## 🎮 Quick Navigation by Task

### "I want to run the robot"
1. Read: [QUICKSTART.md](QUICKSTART.md) (2 min)
2. Run: `bash run_robot.sh`
3. Done!

### "I just got a Jetson Xavier with no Docker"
1. Read: [STARTUP.md](STARTUP.md) (30 min complete guide)
2. Follow every step
3. At the end: Your robot is ready!

### "I need to find where Riva lives on Xavier"
- Read: [XAVIER_PATHS.md](XAVIER_PATHS.md)
- Shows exact paths for: Riva, models, config, credentials, scripts

### "My servo doesn't move - need to debug"
1. Read: [docs/SERVO_QUICK_REFERENCE.md](docs/SERVO_QUICK_REFERENCE.md) (quick test commands)
2. If still stuck: [docs/SERVO_LOGIC.md](docs/SERVO_LOGIC.md) (detailed logic)

### "I want to understand the full system"
1. [README.md](README.md) - High-level overview
2. [docs/INTEGRATION.md](docs/INTEGRATION.md) - How 5 repos fit together
3. [STARTUP.md](STARTUP.md) - What actually runs

---

## 💡 Display Control (New)

The robot now automatically manages the LCD display:

**What happens:**
- ✅ Display turns **ON** when you run `bash run_robot.sh`
- ✅ App runs with display active
- ✅ Display turns **OFF** (blank screen) when app exits → **Power saving mode**

**Timeout:** 5 seconds of inactivity before LCD blanks

**Manual control available:**
- Turn display ON: `bash test_display.sh` (test script)
- See [run_robot.sh](run_robot.sh) lines 43-56 (display ON) and 75-83 (display OFF)

---

