# Humanoid Robot Software

This repository contains the synchronized robot runtime application:
- Speech (NVIDIA Riva TTS)
- Finger gestures (Arduino over serial)
- Face expressions (LCD adapter interface)

> Safety-first default: **main arm servos are disabled**. Only finger gestures are allowed.

---

## 1) Project layout

- `robot_sync_app/`
  - `config/config.yaml` → runtime configuration
  - `docs/API_CONTRACT.md` → Jetson↔Arduino message contract
  - `src/robot_sync_app/` → clean architecture source code
  - `requirements.txt` → Python dependencies

Architecture layers:
- `domain` → models/events
- `ports` → interfaces
- `application` → orchestration logic
- `adapters` → infrastructure (Riva, serial, storage)
- `bootstrap` → dependency wiring from config

---

## 2) Safety controls (important)

Open `robot_sync_app/config/config.yaml`:

- `safety.enable_main_arms: false`

With this value:
- arm commands are blocked in the gesture adapter
- only whitelisted finger gestures are accepted

Allowed finger gestures are defined under:
- `gesture.allowed_finger_gestures`

---

## 3) Storage backends

Current backend:
- local NVMe path: `/mnt/nvme/adrian/robot_data`

Configured in:
- `storage.backend: local`
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

## 5) Installation

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
