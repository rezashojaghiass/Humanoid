# Quickstart (Daily Use)

## Start here

```bash
cd /path/to/Humanoid
```

## 1) Confirm Riva

```bash
docker ps | grep riva-speech
```

If not running, start it using your Riva quickstart scripts.

## 2) Verify speaker output index (if needed)

```bash
python3 -c "import pyaudio as p; a=p.PyAudio(); [print(f'{i}: {a.get_device_info_by_index(i)[\"name\"]}') for i in range(a.get_device_count()) if a.get_device_info_by_index(i).get('maxOutputChannels',0)>0]; a.terminate()"
```

Then update:
- `robot_sync_app/config/config.yaml` → `speech.output_device_index`

## 3) Run orchestrator

```bash
PYTHONPATH=robot_sync_app/src python3 -m robot_sync_app.main \
  --config robot_sync_app/config/config.yaml \
  --text "Hello Adrian!" \
  --intent chat
```

## 4) Auto-start Riva + continuous conversation mode

```bash
PYTHONPATH=robot_sync_app/src python3 -m robot_sync_app.main \
  --config robot_sync_app/config/config.yaml \
  --voice \
  --intent chat
```

Notes:
- App auto-checks/starts Docker + Riva (using `riva_startup` config)
- Conversation keeps running until you say: `QUIT`

## 5) Safety check

Keep this value:
- `safety.enable_main_arms: false`

This ensures fingers-only operation.


## 6) Arm calibration mode

Use the repo launcher:

```bash
./start_humanoid_calibration.sh
```

This uses `robot_sync_app/config/config.calibration.yaml` (with fallback to `config.yaml`).

Riva note:
- Use the v2.19 quickstart folder, configured for 2.14.0 images/models.

## 7) Calibration behavior contract (important)

When running calibration, the expected behavior is:

- Finger gestures are disabled in calibration prompts.
- Main menu is short-answer guided:
  - `left` / `right`
  - `elbow` / `shoulder 1` / `shoulder 2`
  - `up` / `down`
  - `main menu` / `quit`
- `some more` repeats last move.
- `reverse` applies opposite direction of last move.
- `quit` sends a hard stop command (`STOP_ALL`) to Arduino.
- Arduino calibration move is one-shot and time-limited to 0.5s per step.

Do not re-enable finger animation in calibration mode.
