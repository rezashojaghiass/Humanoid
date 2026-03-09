# 📑 Humanoid Project - File Index & Documentation Guide

**Quick navigation for all project documentation and configuration files.**

---

## 🚀 Start Here

1. **[README.md](README.md)** - Project overview, quick start, hardware setup
   - Read this first for system overview
   - Contains 4-step quick start guide
   - Hardware component list with pinouts

2. **[INTEGRATION_SUMMARY.md](INTEGRATION_SUMMARY.md)** - Complete summary for next session
   - What was accomplished (6 points)
   - Status of all components
   - Next-session checklist
   - Troubleshooting quick reference

3. **[docs/INTEGRATION.md](docs/INTEGRATION.md)** - Detailed cross-repository guide
   - ChatBotRobot voice AI integration (§1)
   - RobotArmServos hardware control (§2)
   - FacialAnimation LCD expressions (§3)
   - VNC_Setup remote access (§4)
   - LidarUnitree autonomy (§5)

---

## 🏗️ Software Architecture

**Location:** `robot_sync_app/`

### Source Code

```
robot_sync_app/src/robot_sync_app/
├── domain/                          # Business models
│   ├── models.py                   # Utterance, BehaviorPlan dataclasses
│   └── events.py                   # TimelineEvent, EventType
│
├── ports/                           # Interface contracts
│   ├── speech_port.py              # SpeechPort (TTS)
│   ├── gesture_port.py             # GesturePort (servo control)
│   ├── face_port.py                # FacePort (emotions)
│   ├── storage_port.py             # StoragePort (JSON/S3)
│   ├── asr_port.py                 # ASRPort (speech recognition) [NEW]
│   ├── llm_port.py                 # LLMPort (language models) [NEW]
│   ├── localization_port.py        # LocalizationPort (ROS2/LiDAR) [FUTURE]
│   ├── perception_port.py          # PerceptionPort (obstacle detection) [FUTURE]
│   └── wheel_port.py               # WheelPort (motor control) [FUTURE]
│
├── adapters/                        # Implementations
│   ├── speech/riva_speech.py       # Riva TTS implementation
│   ├── asr/riva_mic_asr.py         # Riva ASR + VAD + mic capture [NEW]
│   ├── gesture/arduino_serial.py   # Arduino serial + safety enforcement
│   ├── face/lcd_stub.py            # LCD stub (ready for driver)
│   ├── llm/bedrock_llm.py          # AWS Bedrock with throttling [NEW]
│   ├── llm/simple_llm.py           # Stub LLM for testing
│   ├── storage/local_storage.py    # Local NVMe storage
│   ├── storage/s3_storage.py       # S3 storage adapter (ready)
│   ├── perception/unitree_lidar_stub.py  # LiDAR stub [FUTURE]
│   └── localization/ros2_stub.py   # ROS2 localization stub [FUTURE]
│
├── application/                     # Use cases
│   ├── behavior_planner.py         # Maps text → gesture + emotion
│   ├── orchestrator.py             # Single-turn orchestration
│   └── voice_session_service.py    # Multi-turn voice loop [NEW]
│
├── bootstrap/                       # Dependency injection
│   └── container.py                # build_orchestrator(), build_voice_session()
│
└── main.py                          # CLI entry point
    └── Modes: --text (manual) or --voice (loop)
```

### Configuration

- **[config/config.yaml](robot_sync_app/config/config.yaml)** - All runtime settings
  - Speech device configuration
  - ASR (Riva mic, VAD settings)
  - LLM (Bedrock, system prompt, throttling)
  - Gesture (Arduino port, baud)
  - Safety (arm disable, gesture whitelist)
  - Storage (local path)

### Documentation

- **[QUICKSTART.md](robot_sync_app/QUICKSTART.md)** - Daily setup guide
- **[API_CONTRACT.md](robot_sync_app/API_CONTRACT.md)** - Message protocols
- **[FUTURE_INTEGRATIONS.md](robot_sync_app/FUTURE_INTEGRATIONS.md)** - Roadmap

---

## 🔧 Configuration Files

### Main Configuration
- **[robot_sync_app/config/config.yaml](robot_sync_app/config/config.yaml)**
  - Audio device indices
  - Riva server address (localhost:50051)
  - AWS Bedrock credentials & model ID
  - Arduino serial port & baud rate
  - Safety settings (main arm disable, gesture allowlist)
  - System prompt (Buzz Lightyear persona)

### Arduino Sketches
- **`/home/reza/RobotArmServos/AllServosFeb10.ino`** - Servo control firmware
  - Upload to: Arduino Mega @ `/dev/ttyACM0` (115200 baud)
  - Controls: 10 finger servos + 6 arm servos

### System Files (Xavier)
- **`/etc/X11/xorg.conf`** - Dual display setup (from VNC_Setup)
  - Physical HDMI (DP-0)
  - Headless virtual (DFP-0) for VNC

---

## 🔗 Cross-Repository Links

| Repo | Purpose | Key File | Status |
|------|---------|----------|--------|
| [ChatBotRobot](https://github.com/rezashojaghiass/ChatBotRobot) | Voice AI | `src/voice_chat_riva_aws.py` | ✅ Integrated |
| [RobotArmServos](https://github.com/rezashojaghiass/RobotArmServos) | Hardware | `AllServosFeb10.ino` | ✅ Integrated |
| [FacialAnimation](https://github.com/rezashojaghiass/FacialAnimation) | LCD | `FacialExpressionBuzzLightYear/` | 🔄 Scaffolded |
| [VNC_Setup](https://github.com/rezashojaghiass/VNC_Setup) | Remote Display | `/etc/X11/xorg.conf` | ✅ Configured |
| [LidarUnitree](https://github.com/rezashojaghiass/LidarUnitree) | Autonomy | `unitree_lidar_ros2/` | 🔄 Scaffolded |

---

## 📍 File Locations on Xavier

### Project Root
```
/home/reza/RobotArmServos/Humanoid/
├── robot_sync_app/              # Main application
├── README.md                    # Project overview
├── INTEGRATION_SUMMARY.md       # Completed work summary
├── INDEX.md                     # This file
└── docs/INTEGRATION.md          # Detailed integration guide
```

### Data & Configuration
```
/mnt/nvme/adrian/robot_data/            # Session storage
robot_sync_app/config/config.yaml       # Runtime settings
```

### External Repositories (Linked)
```
/mnt/nvme/adrian/ChatBotRobot/          # Voice AI system
  └── scripts/start_riva.sh             # Start Riva Docker

/home/reza/RobotArmServos/              # Hardware sketches
  └── AllServosFeb10.ino                # Servo control

/mnt/nvme/unilidar_sdk/                 # LiDAR ROS2 driver
  └── unitree_lidar_ros2/install/
```

---

## 🎯 Usage Examples

### Text Mode (Manual)
```bash
cd /home/reza/RobotArmServos/Humanoid/robot_sync_app
PYTHONPATH=src python3 -m robot_sync_app.main \
  --config config/config.yaml \
  --text "Hello Adrian, I am Buzz Lightyear!"
```

### Voice Mode (Interactive Loop)
```bash
PYTHONPATH=src python3 -m robot_sync_app.main \
  --config config/config.yaml \
  --voice \
  --intent chat \
  --max-turns 10
```

See **[QUICKSTART.md](robot_sync_app/QUICKSTART.md)** for more examples.

---

## 📊 Status Dashboard

| Component | Filename | Status | Tested |
|-----------|----------|--------|--------|
| Voice Input | `asr/riva_mic_asr.py` | ✅ Complete | Yes |
| LLM Processing | `llm/bedrock_llm.py` | ✅ Complete | Yes |
| Speech Output | `speech/riva_speech.py` | ✅ Complete | Yes |
| Gesture Control | `gesture/arduino_serial.py` | ✅ Complete | Yes |
| Facial Expressions | `face/lcd_stub.py` | 🔄 Stub | No |
| Voice Loop | `voice_session_service.py` | ✅ Complete | Yes |
| Storage | `storage/local_storage.py` | ✅ Complete | Yes |
| LiDAR Integration | `perception/unitree_lidar_stub.py` | 🔄 Stub | No |

---

## 🔐 Important Configs

### Must Have Before Running
1. **AWS Credentials** → `~/.aws/credentials`
   ```bash
   aws configure
   ```

2. **Riva Running** → `docker ps | grep riva-speech`
   ```bash
   cd /mnt/nvme/adrian/ChatBotRobot && ./scripts/start_riva.sh
   ```

3. **Audio Device Correct** → `config.yaml`
   ```bash
   python3 robot_sync_app/scripts/list_audio_devices.py
   # Find your speaker, update output_device_index
   ```

4. **Arduino Connected** → `/dev/ttyACM0`
   ```bash
   ls -la /dev/ttyACM0
   ```

---

## 📚 Reading Order

**For New Users:**
1. [README.md](README.md) - Overview + quick start
2. [INTEGRATION_SUMMARY.md](INTEGRATION_SUMMARY.md) - What was built
3. [robot_sync_app/QUICKSTART.md](robot_sync_app/QUICKSTART.md) - Daily setup

**For Deep Dive:**
1. [docs/INTEGRATION.md](docs/INTEGRATION.md) - Component details
2. `robot_sync_app/src/robot_sync_app/main.py` - Entry point
3. `robot_sync_app/src/robot_sync_app/bootstrap/container.py` - DI wiring
4. `robot_sync_app/src/robot_sync_app/application/voice_session_service.py` - Voice loop logic

**For Hardware Setup:**
1. [README.md](README.md#-hardware-setup) - Device list
2. [docs/INTEGRATION.md](docs/INTEGRATION.md#2-robotarmservos-integration) - Pin mapping
3. `/home/reza/RobotArmServos/README.md` - Arduino setup details

**For Troubleshooting:**
1. [README.md](README.md#-troubleshooting) - 5 common issues
2. [INTEGRATION_SUMMARY.md](INTEGRATION_SUMMARY.md#-if-something-breaks) - Quick fixes
3. [docs/INTEGRATION.md](docs/INTEGRATION.md) - Per-component solutions

---

## 🔗 Quick Links

- **GitHub (Humanoid):** https://github.com/rezashojaghiass/Humanoid
- **GitHub (ChatBotRobot):** https://github.com/rezashojaghiass/ChatBotRobot
- **GitHub (RobotArmServos):** https://github.com/rezashojaghiass/RobotArmServos
- **GitHub (FacialAnimation):** https://github.com/rezashojaghiass/FacialAnimation
- **GitHub (VNC_Setup):** https://github.com/rezashojaghiass/VNC_Setup
- **GitHub (LidarUnitree):** https://github.com/rezashojaghiass/LidarUnitree

---

## ✅ Next Steps

- [ ] Read [INTEGRATION_SUMMARY.md](INTEGRATION_SUMMARY.md)
- [ ] Verify [config/config.yaml](robot_sync_app/config/config.yaml) audio device
- [ ] Start Riva: `./scripts/start_riva.sh`
- [ ] Run voice test: `python3 main.py --config config/config.yaml --voice --max-turns 3`
- [ ] Check gestures work (fingers wave)
- [ ] Review docs/INTEGRATION.md for implementation details

---

**Last Updated:** March 9, 2026  
**Commit:** 5688554  
**Status:** Complete documentation, ready for testing
