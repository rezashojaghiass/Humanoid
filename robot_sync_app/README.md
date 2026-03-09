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
