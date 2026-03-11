# Robot Sync App (Clean Architecture)

This is a clean-architecture orchestrator for:
- Speech (Riva)
- Finger gestures (Arduino)
- Face expressions (LCD adapter)

Main arm servos are safety-disabled by default.

## Safety

In [config/config.yaml](config/config.yaml):
- `safety.enable_main_arms: false`

This blocks arm-related gesture commands in the gesture adapter.

## Structure

- `src/robot_sync_app/domain`: core models/events
- `src/robot_sync_app/ports`: interfaces
- `src/robot_sync_app/application`: orchestration logic
- `src/robot_sync_app/adapters`: infrastructure implementations
- `src/robot_sync_app/bootstrap`: dependency wiring
- `config/config.yaml`: environment config

## Storage backends

Current: local NVMe path (default):
- `/mnt/nvme/adrian/robot_data`

Future: switch to S3 by setting:
- `storage.backend: s3`
- `storage.s3_bucket`
- `storage.s3_prefix`

## Run

From [robot_sync_app](.):

```bash
pip3 install -r requirements.txt
PYTHONPATH=src python3 -m robot_sync_app.main --config config/config.yaml --text "Hello Adrian, welcome to quiz time!" --intent quiz
```

## Notes

- `ArduinoSerialGestureAdapter` sends JSON lines over serial.
- Replace `LCDStubFaceAdapter` with your real Jetson LCD drawing adapter.
- Keep gesture names to allowed finger presets from config.


## Arm calibration mode

This mode uses a dedicated config file:
- `config/config.calibration.yaml`

It enables main arm controls for calibration:
- `safety.enable_main_arms: true`

From repository root:

```bash
./start_humanoid_calibration.sh
```

Expected behavior:
- App runs a dedicated calibration dialogue with short answers:
	- `left` / `right`
	- `elbow` / `shoulder 1` / `shoulder 2`
	- `up` / `down`
	- `main menu` / `quit`
- `some more` repeats the previous move.
- `reverse` applies previous move in opposite direction.
- `quit` ends calibration and sends a hard stop command to Arduino.

Safety rules in this mode:
- No finger gesture loop during calibration speech.
- Arm steps are one-shot (`ARM_CAL`) and capped to 0.5s in Arduino firmware.

If the calibration config is missing, the launcher falls back to `config/config.yaml`.
