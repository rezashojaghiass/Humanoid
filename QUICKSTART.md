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

## 3) Run orchestrator with display control (RECOMMENDED)

**Easiest method - automatic display management:**

```bash
bash run_robot.sh
```

This script automatically:
- ✅ Turns **ON** the LCD display
- ✅ Runs the robot app
- ✅ Turns **OFF** the LCD display when you exit (power saving mode)

**Manual run (if you need custom config):**

```bash
PYTHONPATH=robot_sync_app/src python3 -m robot_sync_app.main \
  --config robot_sync_app/config/config.yaml \
  --text "Hello Adrian!" \
  --intent chat
```

## 4) Auto-start Riva + continuous conversation mode

```bash
bash run_robot.sh
```

Now:
- **Press spacebar** to start listening (green indicator)
- **Speak your message** (robot should echo it back)
- **Release spacebar** to process
- **Wait 2-3 seconds** for AWS Bedrock LLM response
- **Hear robot speak** and see finger gestures sync

To exit: Press `Ctrl+C` or say "quit"

Or manually:

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

## 6) Display Control (New Feature)

### What happens automatically with `bash run_robot.sh`:
- **Display ON** → App starts → Display OFF (blank screen when idle)
- **Timeout:** 5 seconds of inactivity before LCD blanks
- **Purpose:** Power saving mode - LCD consumes significant power

### Test display control manually:

```bash
bash test_display.sh
```

This will:
1. Turn display OFF (blank screen)
2. Wait 3 seconds
3. Turn display ON

### Manual display control:

```bash
# Turn display ON
export DISPLAY=:0
xset s off
xset s noblank
xset s reset

# Turn display OFF (blank after 5 seconds)
export DISPLAY=:0
xset s blank
xset s 5 5
xset s activate
```

See [run_robot.sh](run_robot.sh) for implementation details.

## 7) Arm calibration mode

Use the repo launcher:

```bash
./start_humanoid_calibration.sh
```

This uses `robot_sync_app/config/config.calibration.yaml` (with fallback to `config.yaml`).

Riva note:
- Use the v2.19 quickstart folder, configured for 2.14.0 images/models.

## 8) Calibration behavior contract (important)

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

## 📚 Documentation Index

For complete guides, see **[README.md](README.md)** which has:
- Full documentation table of contents
- Quick navigation by task
- System architecture diagrams
- Hardware setup details

Or visit [INDEX.md](INDEX.md) for complete file navigation.
