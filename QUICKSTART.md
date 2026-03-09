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

## 4) Safety check

Keep this value:
- `safety.enable_main_arms: false`

This ensures fingers-only operation.
