# 🔗 Cross-Repository Integration Guide

**Complete mapping of how all five robot subsystems integrate into Humanoid.**

---

## Overview

The Humanoid platform unifies five separate GitHub repositories into a single, coherent robot system. This document explains the data flow, dependencies, and integration points for each component.

```
USER SPEAKS
    ↓
Microphone (Wireless GO II 48kHz)
    ↓
[ChatBotRobot] RivaMicASRAdapter → Transcription
    ↓
[ChatBotRobot] BedrockLLMAdapter → AI Response
    ↓
BehaviorPlanner → Gesture + Emotion Selection
    ↓
    ├─→ [RobotArmServos] ArduinoSerialAdapter (fingers)
    │
    ├─→ [ChatBotRobot] RivaSpeechAdapter (TTS speaker)
    │
    └─→ [FacialAnimation] LCDStubAdapter → LCD Renderer (future)
    
[LidarUnitree] (optional autonomy layer)
[VNC_Setup] (optional remote display)
```

---

## 1. ChatBotRobot Integration

**Repository:** https://github.com/rezashojaghiass/ChatBotRobot  
**Purpose:** Voice AI pipeline (ASR + LLM + TTS)  
**Status:** ✅ Fully integrated

### Files Used

| File | Purpose | Integration |
|------|---------|-------------|
| `src/voice_chat_riva_aws.py` | Reference implementation | Pattern for RivaMicASRAdapter + BedrockLLMAdapter |
| `docs/RIVA_GUIDE.md` | Riva setup | Container startup + port 50051 |
| `docs/AWS_BEDROCK.md` | Bedrock config | Model IDs, credentials, throttling |
| `scripts/start_riva.sh` | Docker launch | Start Riva before voice mode |
| `scripts/speak.py` | TTS utility | Integrated as RivaSpeechAdapter |

### Data Flow

```
1. AUDIO INPUT (Mic)
   └─ RivaMicASRAdapter (in robot_sync_app/adapters/asr/)
      ├─ Captures 48kHz via PyAudio (Wireless GO II)
      ├─ Voice Activity Detection (0.5s silence threshold)
      ├─ Resamples to 16kHz for Riva compatibility
      └─ Streams to Riva gRPC service @ localhost:50051
         └─ Returns: transcript (String)

2. LANGUAGE PROCESSING (LLM)
   └─ BedrockLLMAdapter (in robot_sync_app/adapters/llm/)
      ├─ Query: transcript + config.llm.system_prompt
      ├─ Target: AWS Bedrock API
      ├─ Model: us.meta.llama3-1-70b-instruct-v1:0 (or Claude 3.5)
      ├─ Throttling: 1.5s min cooldown, exponential backoff (max 10 retries)
      └─ Returns: LLM response (String)

3. SPEECH OUTPUT (TTS)
   └─ RivaSpeechAdapter (in robot_sync_app/adapters/speech/)
      ├─ Input: response text from LLM
      ├─ Target: Riva gRPC @ localhost:50051
      ├─ Output: 48kHz WAV stream
      └─ Playback: PyAudio → device 25 (KT USB Speaker)
```

### Configuration Points

**`robot_sync_app/config/config.yaml`:**
```yaml
speech:
  riva_server: localhost:50051      # Riva gRPC endpoint
  output_device_index: 25            # KT USB Audio device

asr:
  provider: riva_mic                 # ASR implementation
  input_device_name_hint: "Wireless GO II"  # Auto-find via name
  vad_threshold: 0.5                 # Silence detection (seconds)
  sample_rate: 48000                 # Microphone sampling rate

llm:
  provider: bedrock                  # LLM implementation
  aws_region: us-west-2              # AWS region
  aws_model_id: us.meta.llama3-1-70b-instruct-v1:0
  system_prompt: |                   # Buzz Lightyear persona
    You are Buzz Lightyear, Space Ranger Elite...
    Keep responses <100 words, kid-friendly, enthusiastic.
  min_cooldown_ms: 1500              # Minimum time between LLM queries
```

### Setup Steps

```bash
# 1. Start Riva Docker (from ChatBotRobot repo)
cd /mnt/nvme/adrian/ChatBotRobot
./scripts/start_riva.sh

# 2. Verify Riva listening on port 50051
docker ps | grep riva-speech
netstat -tlnp | grep 50051

# 3. Configure AWS credentials
aws configure
# Enter: Access Key, Secret Key, Region (us-west-2), Format (json)

# 4. Enable Bedrock models in AWS console
# Bedrock → Model access → Request access to Llama 3.1 70B and Claude 3.5

# 5. Update config.yaml with your AWS settings

# 6. Run voice mode
PYTHONPATH=robot_sync_app/src python3 -m robot_sync_app.main \
  --config robot_sync_app/config/config.yaml \
  --voice --intent chat
```

### Troubleshooting ChatBotRobot Integration

**Issue:** "Failed to connect to Riva on localhost:50051"
- Solution: `docker ps | grep riva-speech` should be running
- If not: `cd /mnt/nvme/adrian/ChatBotRobot && ./scripts/start_riva.sh`

**Issue:** "Bedrock API throttling (TooManyRequests)"
- Solution: Increase `llm.min_cooldown_ms` in config.yaml (e.g., 2000)
- Or request quota increase in AWS console

**Issue:** "No speech output (silent)"
- Solution: Check audio device index, run `python3 robot_sync_app/scripts/list_audio_devices.py`
- Update `speech.output_device_index` to correct device (usually 25 for KT USB)

---

## 2. RobotArmServos Integration

**Repository:** https://github.com/rezashojaghiass/RobotArmServos  
**Purpose:** Hardware control (finger servos + arm movements)  
**Status:** ✅ Fully integrated (fingers-only by default)

### Files Used

| File | Purpose | Integration |
|------|---------|-------------|
| `AllServosFeb10.ino` | Arduino firmware | Uploaded to /dev/ttyACM0 |
| `README.md` | Pin mapping + servo calibration | Reference for ArduinoSerialAdapter |
| `Servo.h` | Arduino servo library | Arduino IDE requirement |
| `PS2X_lib/` | PS2 controller library | Future: joystick gesture control |

### Pin Mapping

```
RIGHT HAND FINGERS:
├─ Thumb:  D2
├─ Index:  D3
├─ Middle: D4
├─ Ring:   D5
└─ Pinky:  D6

LEFT HAND FINGERS:
├─ Thumb:  D7
├─ Index:  D8
├─ Middle: D9
├─ Ring:   D10
└─ Pinky:  D11

ARM SERVOS (disabled by default):
├─ Left Shoulder 1:  Signal D17, Power D33
├─ Left Shoulder 2:  Signal D25, Power D35
├─ Left Elbow:       Signal D24, Power D34
├─ Right Shoulder 1: Signal D14, Power D30
├─ Right Shoulder 2: Signal D15, Power D31
└─ Right Elbow:      Signal D16, Power D32
```

### Communication Protocol

**Serial Port:** `/dev/ttyACM0` @ 115200 baud  
**Format:** JSON-line (each command ends with `\n`)

**Example Commands:**
```json
{"gesture": "wave"}
{"gesture": "thinking"}
{"gesture": "pointing"}
{"gesture": "open"}
{"gesture": "close"}
```

### Data Flow

```
ArduinoSerialGestureAdapter (robot_sync_app/adapters/gesture/)
    ├─ Input: gesture name from BehaviorPlanner
    ├─ Safety check: gesture in allowed_gestures list?
    ├─ Format: JSON command (e.g., {"gesture": "wave"})
    ├─ Serialize: Add newline terminator
    ├─ Send: Write to /dev/ttyACM0 @ 115200 baud
    └─ Receive: Acknowledge from Arduino (if implemented)
```

### Configuration

**`robot_sync_app/config/config.yaml`:**
```yaml
gesture:
  serial_port: /dev/ttyACM0         # Arduino serial port
  baud_rate: 115200                 # Must match Arduino code
  timeout_ms: 500                    # Response timeout

safety:
  enable_main_arms: false            # IMPORTANT: Keep false!
  enable_wheels: false               # Future: omni base control
  enable_autonomy: false             # Future: LiDAR navigation
  allowed_gestures:                  # Whitelist for safety
    - wave
    - thinking
    - pointing
    - open
    - close
```

### Setup Steps

```bash
# 1. Verify Arduino is connected
ls -la /dev/ttyACM0
# Should show: crw-rw---- 1 root dialout ...

# 2. Add user to dialout group (if permission denied)
sudo usermod -aG dialout $USER
newgrp dialout

# 3. Install Arduino CLI
sudo apt-get install arduino-cli

# 4. Upload servo sketch
arduino-cli board list  # Find your board FQBN
arduino-cli upload -p /dev/ttyACM0 --fqbn arduino:avr:mega \
  /home/reza/RobotArmServos/AllServosFeb10.ino

# 5. Verify upload
# Serial monitor should show servo initialization messages

# 6. Test gesture
PYTHONPATH=src python3 << 'EOF'
from robot_sync_app.ports.gesture_port import GesturePort
from robot_sync_app.adapters.gesture.arduino_serial import ArduinoSerialGestureAdapter
import yaml

with open('robot_sync_app/config/config.yaml') as f:
    config = yaml.safe_load(f)

adapter = ArduinoSerialGestureAdapter(config['gesture'], config['safety'])
adapter.start_gesture('wave')
adapter.stop_gesture('wave')
EOF
```

### Troubleshooting RobotArmServos Integration

**Issue:** "Permission denied" on /dev/ttyACM0
- Solution: `sudo usermod -aG dialout $USER` then logout/login

**Issue:** Fingers don't move after upload
- Solution: Check servo power supply, verify pins D2-D11 have 5V
- Check serial communication: `python3 robot_sync_app/scripts/test_arduino.py`

**Issue:** Arduino sketch won't upload
- Solution: Check board FQBN: `arduino-cli board list`
- Verify board type: Should be "Arduino Mega 2560" not clone

**Issue:** Arm servos move despite `enable_main_arms: false`
- Solution: Safety enforcement is in adapter, not Arduino firmware
- Check config.yaml: `allow_gestures` list should NOT include arm gestures

---

## 3. FacialAnimation Integration

**Repository:** https://github.com/rezashojaghiass/FacialAnimation  
**Purpose:** LCD facial expressions with Buzz Lightyear character  
**Status:** 🔄 Scaffolded (LCD driver integration needed)

### Assets Available

```
FacialExpressionBuzzLightYear/
├─ Smile/          → 30-frame PNG sequence (happy emotion)
├─ Sad/            → 30-frame PNG sequence (sad emotion)
├─ Surprise/       → 30-frame PNG sequence (surprised emotion)
├─ AA/             → 30-frame PNG sequence (mouth shape AA)
├─ EE/             → 30-frame PNG sequence (mouth shape EE)
└─ OO/             → 30-frame PNG sequence (mouth shape OO)

Rigging/
├─ XP_Buzz_Lightyear_Rig_Blender.blend
├─ XP_Buzz_Lightyear_rig_ui_BLENDER_4.0x_.py
└─ XP_Buzz_Lightyear_rig_ui_BLENDER_3.6x_.py
```

### Current Implementation

**`LCDStubFaceAdapter`** (robot_sync_app/adapters/face/)
```python
class LCDStubFaceAdapter(FacePort):
    def set_expression(self, emotion: str) -> None:
        print(f"[LCD] Setting expression: {emotion}")
        # Future: Load emotion/*/frame_*.png sequence
        # Future: Send to LCD driver / GPIO / I2C display
```

### Data Flow (Current)

```
BehaviorPlanner
    └─ Selects emotion (smile, sad, surprise, neutral)
       └─ LCDStubFaceAdapter.set_expression(emotion)
          └─ Prints to console: "[LCD] Setting expression: smile"
```

### Data Flow (Future - with LCD Driver)

```
BehaviorPlanner
    └─ Selects emotion (smile, sad, surprise)
       └─ LCDStubFaceAdapter.set_expression(emotion)
          ├─ Load frame sequence: FacialExpressionBuzzLightYear/{emotion}/*.png
          ├─ Cycle frames with timing:
          │  ├─ Frame 0-5: 100ms per frame (expression introduction)
          │  ├─ Frame 6-25: 200ms per frame (sustained expression)
          │  └─ Frame 26-29: 100ms per frame (expression fade)
          └─ Send to LCD hardware (GPIO, I2C, HDMI overlay, etc.)
```

### Integration Steps (Future)

#### Step 1: Implement LCD Driver Adapter

```python
# robot_sync_app/adapters/face/lcd_driver.py
from robot_sync_app.ports.face_port import FacePort
import cv2
import numpy as np
from pathlib import Path

class LCDDriverFaceAdapter(FacePort):
    def __init__(self, lcd_device, emotion_base_path):
        self.lcd = lcd_device  # GPIO, I2C display object
        self.emotion_base = Path(emotion_base_path)
        
    def set_expression(self, emotion: str) -> None:
        frames_dir = self.emotion_base / emotion
        if not frames_dir.exists():
            print(f"Warning: Emotion {emotion} not found")
            return
        
        # Load frame sequence
        frames = sorted([f for f in frames_dir.glob("*.png")])
        for i, frame_path in enumerate(frames):
            img = cv2.imread(str(frame_path))
            # Display on LCD (implementation depends on hardware)
            self._display_frame(img)
            
            # Timing varies by frame index
            if i < 5:
                time.sleep(0.1)  # 100ms intro
            elif i < 26:
                time.sleep(0.2)  # 200ms sustain
            else:
                time.sleep(0.1)  # 100ms fade
    
    def _display_frame(self, img):
        # Implementation depends on LCD hardware:
        # - GPIO framebuffer: mmap and write pixel data
        # - I2C OLED: Send image via I2C protocol
        # - HDMI overlay: Use pygame or PIL
        # - Serial LCD: Send via UART
        pass
```

#### Step 2: Add LCD Hardware Configuration

```yaml
# In config/config.yaml
lcd:
  type: gpio_framebuffer  # or: i2c_oled, hdmi_overlay, serial_uart
  device: /dev/fb0
  width: 1920
  height: 1080
  emotion_base_path: /home/reza/RobotArmServos/FacialAnimation/FacialExpressionBuzzLightYear
```

#### Step 3: Wire LCD Adapter in Bootstrap

```python
# In bootstrap/container.py
def build_orchestrator(...):
    # ... existing code ...
    
    # Choose LCD adapter based on config
    if config.get('lcd.type') == 'gpio_framebuffer':
        face_adapter = LCDDriverFaceAdapter(
            lcd_device=setup_gpio_framebuffer(config['lcd.device']),
            emotion_base_path=config['lcd.emotion_base_path']
        )
    else:
        face_adapter = LCDStubFaceAdapter()  # Fallback to stub
    
    # ... rest of wiring ...
```

### Current Status

✅ **Done:**
- Asset folder structure created
- 30-frame PNG sequences for each emotion
- Blender rig available for future animations

🔄 **TODO:**
- Implement LCD hardware driver (depends on display type)
- Wire adapter in bootstrap container
- Test end-to-end emotion display
- Implement lip-sync (phoneme → mouth shape timing)

---

## 4. VNC_Setup Integration

**Repository:** https://github.com/rezashojaghiass/VNC_Setup  
**Purpose:** Remote desktop access for headless Jetson  
**Status:** ✅ Configured (separate from voice pipeline)

### Configuration

**Files Modified on Xavier:**
```
/etc/X11/xorg.conf         # Dual display setup
~/.bashrc                  # VNC server auto-start
/etc/systemd/system/       # VNC service definition
```

### Display Mapping

```
Display :0 (Physical HDMI)
├─ Monitor: DP-0 (HDMI output port)
├─ Resolution: 1920x1080
└─ Position: X=0, Y=0

Display :1 (Headless Virtual)
├─ Monitor: DFP-0 (virtual framebuffer)
├─ Resolution: 1920x1080
└─ Position: X=1920, Y=0 (extends right of physical)
```

### Data Flow

```
Remote Client (laptop)
    └─ VNC Viewer connected to <Xavier_IP>:5901
       └─ Transmits VNC protocol frames
          └─ Received by: vncserver :1 running on Xavier
             └─ Rendered on: Display :1 (DFP-0 virtual)
                └─ Also displayed on: Display :0 (DP-0 HDMI if monitor connected)
```

### Connection

```bash
# From remote machine:
vncviewer <Xavier_IP>:5901

# Example:
vncviewer 192.168.1.100:5901

# Or command line:
vncviewer -encodings hextile <Xavier_IP>:5901
```

### Integration with Voice Pipeline

**No direct integration.** VNC_Setup provides:
- Remote access to Xavier desktop
- Alternative to HDMI monitor when display not available
- Ability to monitor voice session logs via remote terminal

**Voice pipeline remains independent:**
- Speech, ASR, LLM all run on Xavier locally
- Audio still routes to KT USB Speaker (device 25)
- Gesture commands still sent to Arduino on /dev/ttyACM0
- VNC just provides remote visibility

---

## 5. LidarUnitree Integration

**Repository:** https://github.com/rezashojaghiass/LidarUnitree  
**Purpose:** 4D LiDAR for autonomous navigation  
**Status:** 🔄 Scaffolded (ROS2 bridge needed)

### Current Status

**Created but NOT integrated:**
- `robot_sync_app/ports/localization_port.py` - Interface for LiDAR data
- `robot_sync_app/ports/perception_port.py` - Interface for obstacle detection
- `robot_sync_app/adapters/perception/unitree_lidar_stub.py` - Stub adapter
- `robot_sync_app/adapters/localization/ros2_stub.py` - Stub adapter

### Available Hardware

```
Unitree L1 4D LiDAR
├─ Connection: /dev/ttyUSB0 @ 2000000 baud
├─ Coverage: 360° horizontal × 90° vertical
├─ ROS2 Topic: /unilidar/cloud (PointCloud2 @ 4Hz)
├─ ROS2 Installation: /mnt/nvme/unilidar_sdk/unitree_lidar_ros2/
└─ Status: ROS2 driver built and tested separately
```

### Future Data Flow

```
Step 1: LiDAR Data Acquisition
    └─ ROS2 Driver (from LidarUnitree)
       └─ Publishes: /unilidar/cloud (PointCloud2)

Step 2: Perception Processing
    └─ PerceptionPort (adapter to subscribe to /unilidar/cloud)
       └─ Processes: 3D point cloud
       └─ Outputs: obstacles[], floor_plane, ceiling_height, etc.

Step 3: Voice Context Injection
    └─ BehaviorPlanner receives:
       ├─ User: "Can you see the door?"
       ├─ LiDAR: {obstacle_distance: 2.5m, class: "door"}
       └─ LLM Prompt: "Based on LiDAR perception: " + obstacle_info

Step 4: Gesture Integration
    └─ Response: "I see the door 2.5 meters away"
       ├─ Gesture: pointing gesture toward detected object
       └─ TTS: Says response with gesture timing

Step 5: Autonomous Navigation (Future)
    └─ Voice Command: "Go explore"
       ├─ LocalizationPort: Subscribe to /unilidar/cloud
       ├─ OmniWheelPort: Send motor commands to Arduino #2
       └─ Loop: Obstacle avoidance + navigation until "stop"
```

### Integration Steps (Future)

#### Step 1: Start ROS2 Infrastructure

```bash
# Terminal 1: Start Riva (already needed for voice)
cd /mnt/nvme/adrian/ChatBotRobot
./scripts/start_riva.sh

# Terminal 2: Start LiDAR driver
cd /mnt/nvme/unilidar_sdk/unitree_lidar_ros2
source install/setup.bash
ros2 launch unitree_lidar_ros2 launch.py

# Terminal 3: Start voice loop
cd /home/reza/RobotArmServos/Humanoid/robot_sync_app
PYTHONPATH=src python3 -m robot_sync_app.main \
  --config config/config.yaml \
  --voice --intent explore
```

#### Step 2: Implement ROS2 Perception Adapter

```python
# robot_sync_app/adapters/perception/ros2_lidar.py
import rclpy
from sensor_msgs.msg import PointCloud2
from robot_sync_app.ports.perception_port import PerceptionPort

class ROS2LidarAdapter(PerceptionPort):
    def __init__(self, ros2_node):
        self.node = ros2_node
        self.latest_cloud = None
        
        # Subscribe to LiDAR topic
        self.subscription = self.node.create_subscription(
            PointCloud2,
            '/unilidar/cloud',
            self._point_cloud_callback,
            10
        )
    
    def _point_cloud_callback(self, msg: PointCloud2):
        self.latest_cloud = msg
        # Parse PointCloud2, extract obstacles, walls, etc.
        obstacles = self._extract_obstacles(msg)
        # Emit event: PerceptionEvent(obstacles=obstacles)
    
    def get_obstacles(self) -> list:
        if not self.latest_cloud:
            return []
        return self._extract_obstacles(self.latest_cloud)
```

#### Step 3: Update BehaviorPlanner for LiDAR Context

```python
# robot_sync_app/application/behavior_planner.py
def plan_behavior(self, text: str, obstacles: list = None) -> BehaviorPlan:
    # Original logic
    gesture = self._select_gesture(text)
    emotion = self._select_emotion(text)
    
    # NEW: Incorporate LiDAR perception
    if obstacles:
        # Adjust gesture based on obstacles
        if "door" in text.lower() and obstacles:
            # Point toward nearest obstacle
            gesture = self._pointing_gesture(obstacles[0].angle)
    
    return BehaviorPlan(gesture=gesture, emotion=emotion, ...)
```

#### Step 4: Enable Wheels in Arduino #2

```yaml
# In config/config.yaml
safety:
  enable_wheels: true  # Activate motor commands
  
motors:
  serial_port: /dev/ttyUSB0  # Arduino #2 (base control)
  baud_rate: 115200
```

### Roadmap

| Phase | Timeline | Task |
|-------|----------|------|
| 1 | Now | Stub adapters in place, LiDAR driver separate |
| 2 | Next | ROS2 node integration, point cloud parsing |
| 3 | Future | Behavior planner LiDAR context injection |
| 4 | Future | Autonomous navigation with obstacle avoidance |
| 5 | Future | Game mode with voice + LiDAR perception |

---

## Cross-Component Data Flow: Complete Example

### Scenario: "Can you wave and tell me what you see?"

**Timeline:**

```
T=0ms:      User speaks: "Can you wave and tell me what you see?"

T=200ms:    [ASR] RivaMicASRAdapter
            ├─ Transcript: "Can you wave and tell me what you see?"

T=500ms:    [LLM] BedrockLLMAdapter
            ├─ Query: transcript + system_prompt → Bedrock
            ├─ Query parameters: intent=chat, obstacles=[...] (if LiDAR active)
            └─ Response: "Sure! I see a red box 1.5 meters away. Here, watch me wave!"

T=800ms:    [Plan] BehaviorPlanner
            ├─ Analyzes: "wave" keyword → gesture="wave"
            ├─ Analyzes: "excited" tone → emotion="smile"
            ├─ Checks: Obstacles available? → obstacle_context for next LLM query
            └─ Plan: { gesture: "wave", emotion: "smile" }

T=900ms:    [Execute] OrchestratorService
            ├─ Start gesture: ArduinoSerialAdapter.start_gesture("wave")
            │  └─ Sends: {"gesture": "wave"}\n to /dev/ttyACM0
            │
            ├─ Set emotion: LCDStubFaceAdapter.set_expression("smile")
            │  └─ Prints: "[LCD] Setting expression: smile"
            │
            └─ Start TTS: RivaSpeechAdapter.speak(
                   text="Sure! I see a red box...",
                   on_start=on_audio_start,
                   on_end=on_audio_end
               )

T=1000ms:   [Audio] TTS Playback Starts
            ├─ Riva streams 48kHz WAV to PyAudio
            └─ PyAudio sends to device 25 (KT USB Speaker)
            
T=1100ms:   Callback: on_audio_start()
            └─ Locks gesture until TTS completes
               (fingers continue waving while speaking)

T=3500ms:   [Audio] TTS Playback Ends
            └─ 2.5 seconds of audio streamed and played

T=3600ms:   Callback: on_audio_end()
            ├─ Stop gesture: ArduinoSerialAdapter.stop_gesture("wave")
            │  └─ Sends: {"gesture": "neutral"}\n
            │
            ├─ Reset emotion: LCDStubFaceAdapter.set_expression("neutral")
            │
            └─ Save session: StorageAdapter.put_json(
                   "latest_turn.json",
                   {
                       "user_input": "Can you wave and tell me what you see?",
                       "transcribed": "Can you wave and tell me what you see?",
                       "llm_response": "Sure! I see a red box...",
                       "gesture": "wave",
                       "emotion": "smile",
                       "duration_ms": 3600,
                       "timestamp": "2026-03-09T15:30:00Z"
                   }
               )

T=3700ms:   [Loop] Ready for next turn or exit
            └─ If max_turns not reached:
               ├─ Return to T=0 (waiting for next voice input)
               └─ Else: Exit gracefully
```

---

## Dependency Verification

### Required Services Before Voice Mode

```bash
# Check each prerequisite
docker ps | grep riva-speech          # ✅ Riva must be running
aws sts get-caller-identity           # ✅ AWS credentials valid
ls -la /dev/ttyACM0                   # ✅ Arduino connected
python3 -c "import boto3"              # ✅ boto3 installed
python3 -c "import pyaudio"            # ✅ PyAudio installed
```

### Optional Services for Extended Features

```bash
# LiDAR autonomy
ls -la /dev/ttyUSB0                   # LiDAR connected (optional)
ros2 topic list | grep unilidar       # ROS2 driver running (optional)

# Remote access
vncserver -list                       # VNC server running (optional)

# LCD display
ls -la /dev/fb0                       # Framebuffer display (optional)
```

---

## Summary: Integration Status

| Component | Status | Notes |
|-----------|--------|-------|
| ChatBotRobot (Voice AI) | ✅ Ready | Fully integrated, tested |
| RobotArmServos (Gestures) | ✅ Ready | Fingers-only, safe defaults |
| FacialAnimation (LCD) | 🔄 Scaffolded | Stub ready, LCD driver pending |
| VNC_Setup (Remote) | ✅ Ready | Separate, optional layer |
| LidarUnitree (Autonomy) | 🔄 Scaffolded | Stub adapters ready, ROS2 bridge pending |

**Next Steps:**
1. Test voice loop end-to-end (ChatBotRobot + RobotArmServos)
2. Implement LCD driver (FacialAnimation)
3. Integrate ROS2 node for perception (LidarUnitree)
4. Enable wheel motor commands (Arduino #2 + autonomy)

---

**Author:** Reza Shojaghias  
**Date:** March 9, 2026  
**Platform:** Jetson AGX Xavier, Ubuntu 20.04 LTS
