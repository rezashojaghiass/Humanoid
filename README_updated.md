# 🤖 Humanoid — Verified Startup & Reference

**Written 2026-08-14 from a live debugging session on the Xavier.** Everything marked ✅ was executed and confirmed on this machine, not copied from older docs.

Read this instead of `STARTUP.md`, `QUICKSTART.md`, or `XAVIER_PATHS.md` for startup. Those three contain paths that do not exist on this device — see [What the old docs get wrong](#what-the-old-docs-get-wrong).

---

## 1. Cold start after reboot (the whole thing, ~2 minutes)

```bash
# 1. Riva  (Docker autostarts; the container does not)
docker start riva-speech

# 2. Wait for it to actually serve — takes ~35s
docker logs --since 2m riva-speech 2>&1 | grep "Riva Conversational AI Server listening"

# 3. Run the robot
cd /home/reza/Humanoid && bash run_robot.sh
```

That's it. If step 2 prints nothing after ~60 s, go to [Riva won't start](#riva-wont-start).

### Two traps in step 2 — both bit us

| Trap | Why it lies |
|---|---|
| Checking **port 50051** | Docker's proxy binds the port the instant the container starts, *before* the server loads models. The port opens even when Riva then dies. |
| `docker logs` **without `--since`** | Replays the whole history, including old successful sessions. Greping it for "listening" matches a run from weeks ago. |

Always use `--since` **and** grep the log. Never trust the port.

The strongest check is a real gRPC call:

```bash
python3 -c "
import riva.client
tts = riva.client.SpeechSynthesisService(riva.client.Auth(uri='localhost:50051'))
r = tts.synthesize(text='test', language_code='en-US',
                   encoding=riva.client.AudioEncoding.LINEAR_PCM,
                   sample_rate_hz=48000, voice_name='English-US.Male-1')
print('OK', len(r.audio), 'bytes')"
```

---

## 2. Ground truth — what lives where

| Thing | Real path |
|---|---|
| Repo | `/home/reza/Humanoid` |
| Entry script | `/home/reza/Humanoid/run_robot.sh` |
| Config it actually uses | `robot_sync_app/config/config_lipsync.yaml` |
| Riva image | `nvcr.io/nvidia/riva/riva-speech:2.14.0-l4t-aarch64` |
| Riva container | `riva-speech` (already created — start it, don't `docker run`) |
| Riva model repo | `/mnt/nvme/reza_backup/riva_quickstart_arm64_v2.14.0/model_repository/prebuilt` |
| Docker data root | `/mnt/nvme/docker` |
| Lip-sync frames (3/expression) | `/mnt/nvme/cropped_animation_frames_lipsync_3frames` |
| Full expression frames (30/expression) | `/mnt/nvme/FacialAnimation/cropped_animation_frames_30frames_full` |
| Finger Arduino | `/dev/ttyACM0` (user is in `dialout` ✅) |
| AWS credentials | `/home/reza/.aws/credentials` |
| System logs | `/var/log` → bind-mounted to `/mnt/nvme/log` |

### ⚠️ `riva.service` is disabled on purpose

The systemd unit runs `/mnt/nvme/riva/start_riva_v2_14.sh`, which is broken — it passes Riva's flags (`--riva-uri`, `--model-repo`) to `docker run` instead of to the container, has empty `-p`/`-v` values, and calls `docker rm -f` with no container name. With `Restart=always` and no delay it restarted every ~5 s for 79 days, writing 1.7 GB into `/var/log`.

**Do not `systemctl enable riva`** until that script is fixed. Use `docker start riva-speech`. A restart guard now exists at `/etc/systemd/system/riva.service.d/restart-guard.conf` so it can't spam-loop again.

---

## 3. The Python environment (the confusing part)

**No doc previously described this.** Every `PYTHONPATH` mention in the old docs refers to the *app source*, never the dependency trees.

`~/.bashrc:127` sets:

```bash
export PYTHONPATH="/mnt/nvme/python-packages:/mnt/nvme/reza_local/lib/python3.8/site-packages:/mnt/nvme/vision-python/site-packages:$PYTHONPATH"
```

Because it appends `$PYTHONPATH` to itself, nested shells duplicate it — the live value currently lists those three paths **three times**. Cosmetic, but a sign of drift.

### Five trees, four different `cryptography` versions

| Search order | Tree | Notable contents |
|---|---|---|
| 1 | `/mnt/nvme/python-packages` | cryptography **47.0.0**, urllib3 2.2.3 |
| 2 | `/mnt/nvme/reza_local/lib/python3.8/site-packages` | boto3/botocore 1.37.38, cryptography 41.0.7 |
| 3 | `/mnt/nvme/vision-python/site-packages` | boto3, cryptography 41.0.7 |
| 4 | `/opt/ros/foxy/lib/python3.8/site-packages` | ROS 2 |
| 5 | `/usr/lib/python3/dist-packages` | **pyOpenSSL 19.0.0**, cryptography 2.8 |

**`~/.local` is a symlink to `/mnt/nvme/reza_local`.** So `pip3 install --user` already installs to the NVMe. **That is the tree to standardise on.**

### The boto3 crash and its fix ✅

`import boto3` died with:

```
AttributeError: module 'lib' has no attribute 'X509_V_FLAG_CB_ISSUER_CHECK'
```

Chain: `main.py:9 → container.py:16 → bedrock_llm.py:5 → boto3 → botocore → urllib3.contrib.pyopenssl → OpenSSL`.

pyOpenSSL 19.0.0 (2019, apt) reads OpenSSL constants from the binding that `cryptography` ships. Modern cryptography bundles OpenSSL 3.x, which removed those constants — so the old wrapper explodes *at import time*.

**No PYTHONPATH ordering can fix it.** boto3 exists only in trees that carry cryptography 41; the only compatible cryptography (2.8) is in the system tree, which has no boto3. The pair does not coexist.

The real defect is in botocore:

```python
try:
    from urllib3.contrib.pyopenssl import orig_util_SSLContext as SSLContext
except ImportError:          # ← pyOpenSSL raises AttributeError, not ImportError
    from urllib3.util.ssl_ import SSLContext
```

Its own fallback is correct — it just never fires. Fix applied, **no packages installed**:

```
/mnt/nvme/reza_local/lib/python3.8/site-packages/usercustomize.py
```
```python
import sys
sys.modules.setdefault("urllib3.contrib.pyopenssl", None)
```

This forces the `ImportError` botocore already handles. To undo: delete the file.

> **Why `usercustomize`, not `sitecustomize`:** Debian ships `/usr/lib/python3.8/sitecustomize.py`, and only the *first* `sitecustomize` on `sys.path` is ever imported. Under `run_robot.sh` (which sets `PYTHONPATH=robot_sync_app/src`) the stdlib directory precedes user-site, so Debian's wins and ours is skipped. `usercustomize` is imported from user-site *after* `sitecustomize`, regardless of PYTHONPATH — so it always runs.

### Three OpenCV installs — and why the face froze ✅

The same tree sprawl bit the face. There are **three** `cv2` builds, and they do not behave the same:

| cv2 | Version | GUI backend |
|---|---|---|
| `/usr/lib/python3.8/dist-packages` (JetPack's) | 4.5.4 | **GTK2** |
| `/mnt/nvme/reza_local/lib/python3.8/site-packages` | 4.6.0 | QT5 |
| `/mnt/nvme/vision-python/site-packages` | 4.6.0 | QT5 |

`OpenCVLipSyncFaceAdapter` creates its window on the main thread, then draws from a background animation thread. **GTK tolerates that; Qt blocks on `cv2.imshow` forever.** Isolated test on this machine:

| Build | Background-thread `imshow` |
|---|---|
| GTK2 4.5.4 | 20/20 frames ✅ |
| QT5 4.6.0 | **0/20 — blocked** ❌ |

Symptom: the face loads its frames, displays the first one, and never updates. The animation queue fills and is never drained (39 frames queued, 0 consumed). Nothing in the app logs an error — the thread is simply parked inside `cv2.imshow` at `opencv_lipsync.py:385`.

The `~/.bashrc` PYTHONPATH puts the NVMe trees first, so the pip-installed Qt5 build wins over JetPack's GTK2 build. **`run_robot.sh` now prepends the system tree** so the GTK2 build is used:

```bash
SYSTEM_CV2="/usr/lib/python3.8/dist-packages"
PYTHONPATH="$SYSTEM_CV2:$PYTHON_PATH" python3 -m robot_sync_app.main ...
```

That tree holds only `cv2`, `numpy`, `tensorrt`, and a few NVIDIA tools, so the shadowing is contained — all seven app dependencies still import.

⚠️ **This will come back** if anything reorders PYTHONPATH or re-installs `opencv-python`. The durable fix is removing the Qt5 OpenCV from `reza_local`, but it may be there for vision work, so it was left alone.

---

## 4. Riva won't start

Riva fails with **CUDA out of memory** when the Xavier's memory is fragmented — even with 8 GB free:

```
Error Code 1: Cuda Runtime (out of memory)
failed to load 'riva-trt-conformer-en-US-asr-streaming-am-streaming'
error: creating server: Internal - failed to load all models
```

TTS loads fine; only the Conformer ASR TensorRT engine fails. GPU memory is shared with system RAM, and TensorRT needs a large **contiguous** block.

**Diagnose with `lfb` (largest free block):**

```bash
tegrastats --interval 500 | head -1
```

| Observed | Result |
|---|---|
| `lfb 140x4MB` | ❌ fails |
| `lfb 1915x4MB` (fresh reboot) | ✅ loads in 34 s |

**Fix: reboot.** That is the reliable cure. Before rebooting, the memory hogs were VS Code (~1.6 GB across 6 processes), gnome-shell, gnome-software, and Xtigervnc — closing those may work without a reboot, but a reboot is faster and always works.

`VOICE_SETUP.md:262` suggests `-e RIVA_GPU_MEMORY_FRACTION=0.5`; untested here, and it would need a fresh `docker run`, not the existing container.

---

## 5. Console output and error visibility ✅

`run_robot.sh` **used to end its python line with `2>/dev/null`**, discarding every traceback. The app would print the banner then "Robot session ended" with no explanation — that hid the boto3 crash for two full runs. It has been removed.

In its place, stderr is now filtered rather than discarded, so ALSA's chatter is hidden but real errors are not:

```bash
2> >(grep -vE "^ALSA lib|^Cannot connect to server|^jack server|^JackShmReadWritePtr" >&2)
```

`main.py` also logs at **WARNING** instead of INFO, which removes the internal chatter (`PyAudio initialized`, `Opening stream...`, `Stream opened successfully`, `Writing N bytes to stream`). The user-facing `print()` status lines (🔊 / ⏱️ / ▶️ / ✓) are unaffected.

To debug with everything visible, run the underlying command directly:

```bash
cd /home/reza/Humanoid
DISPLAY=:0 PYTHONPATH=/usr/lib/python3.8/dist-packages:robot_sync_app/src \
  python3 -u -m robot_sync_app.main \
  --config robot_sync_app/config/config_lipsync.yaml \
  --voice --intent chat
```

---

## 6. Known defects (found by reading, not yet fixed)

### ~~Face renders nothing — asset paths are stale~~ ✅ FIXED

The frames were moved to the NVMe and the config wasn't updated, so the app logged `Assets path not found` and ran on with `Loaded expressions: []`. All paths now point at the NVMe, and the two asset sets are configured independently:

| Mode | Config key | Folder | Frames |
|---|---|---|---|
| Lip-sync (during speech) | `face.assets_path` | `/mnt/nvme/cropped_animation_frames_lipsync_3frames` | 3 per expression |
| Facial expression mode | `face.full_assets_path` | `/mnt/nvme/FacialAnimation/cropped_animation_frames_30frames_full` | 30 per expression |

`full_assets_path` used to be hardcoded in `opencv_lipsync.py`; it is now a constructor argument fed from config, so the two sets can differ.

**Frame indices are positions in the loaded list, not filename numbers.** The lip-sync files are `frame_0001/0004/0009.png` → positions 1, 2, 3. Expression mode uses the 30-frame set and requests `range(1, 31)` — all valid. If you ever repoint `full_assets_path` at the 3-frame set, `voice_session_service.py:634` must narrow to `[1, 2, 3]` or you get 27 "Frame index out of range" lines per emotion.

⚠️ Expression mode depends on `/mnt/nvme/FacialAnimation/` — a separate git checkout. Move or clean that directory and expression mode goes quiet (`Expression not pre-loaded`).

### Double-escaped newlines — same typo, two files

`"\\n"` in a normal Python string is a literal backslash + `n`, not a newline.

- **`bedrock_llm.py:55-61`** — the Llama 3.1 prompt template needs real newlines after `<|end_header_id|>`. The model receives a malformed prompt, and the stop sequences `"\\nUser:"` / `"\\n\\n"` can never match. Degrades reply quality silently.
- **`arduino_serial.py:93`** (`_send`) — firmware reads with `Serial.readStringUntil('\n')`, so the terminator never arrives and it blocks for the ~1 s serial timeout. It still works only because `processLine` matches with `indexOf`. Costs ~1 s per gesture start/stop — i.e. it degrades the speech↔gesture sync this project exists to provide. `finger_command`, `arm_calibration_step`, and `STOP_ALL` use a correct `"\n"`; only `_send` is wrong.

### Greedy intent matching

- Quit fires on `"stop"` appearing *anywhere* in a sentence. **Observed live:** a session ended because ASR returned "Quit."
- `_is_movement_intent` matches bare `"more"`, `"hand"`, `"arm"` — so "tell me more" drops you into movement mode mid-conversation.

### Smaller

- `face.default_expression: neutral` never matches the planner's `EE` / `Smile` / `Surprise` keys → "Expression not found" after every utterance.
- `_handle_chat_movement` (~95 lines) and `_parse_chat_arm_command` are dead code.
- Orchestrator reaches across the port boundary: `self._speech._last_audio_duration`, `self._orchestrator._face`.
- `OpenCVLCDFaceAdapter.__del__` calls `cleanup()` — can throw at interpreter shutdown.
- `.pyc` files still tracked in git despite two `.gitignore` commits.
- Both configs set `safety.enable_main_arms: true` while README claims arms are disabled by default.

---

## 7. Audio devices — use the name hint, never the index

**The index is not stable.** KT USB Audio was index **0** in one check and index **1** minutes later in the app.

Both configs correctly use `output_device_index: null` with `output_device_name_hint: "KT USB Audio"`, and auto-detection worked ✅. **Leave the index `null`.** Old docs telling you to hardcode 25/26 are wrong and will break on reboot.

---

## 8. What the old docs get wrong

| Doc | Claim | Reality |
|---|---|---|
| `XAVIER_PATHS.md` | Repo at `/home/reza/RobotArmServos/Humanoid` | `/home/reza/Humanoid` |
| `XAVIER_PATHS.md` | Riva 2.19.0 at `/mnt/nvme/adrian/riva/...` | 2.14.0 at `/mnt/nvme/reza_backup/...` |
| `XAVIER_PATHS.md` | Image `2.24.0-l4t-aarch64` is cached | Only `2.14.0` exists |
| `STARTUP.md` | Start via `/mnt/nvme/adrian/ChatBotRobot/scripts/start_riva.sh` | Path doesn't exist — use `docker start riva-speech` |
| `STARTUP.md` | Hardcode audio indices 8 / 25 | Indices shift; use the name hint |
| `README.md` | Primary config `config.yaml` | `run_robot.sh` uses `config_lipsync.yaml` |
| `README.md` | Main arms disabled by default | Both configs set `enable_main_arms: true` |
| `VOICE_SETUP.md` | `from riva.client import Client` | Real API: `riva.client.Auth` + `ASRService` / `SpeechSynthesisService` |
| `VOICE_SETUP.md` | Xavier has 8 GB unified memory | 14.9 GB |

None of them mention CUDA OOM, the Python tree layout, or that `run_robot.sh` swallows stderr.

---

## 9. Verified working end-to-end (2026-08-14)

```
✓ docker daemon active
✓ Riva 2.14 serving — ASR (conformer-en-US-asr-streaming) + TTS (fastpitch_hifigan_ensemble)
✓ Riva ready 34s after `docker start`; real TTS gRPC call returned 142,108 bytes
✓ boto3 / botocore 1.37.38 import (via usercustomize.py)
✓ riva.client, pyaudio, cv2, yaml, serial, numpy all import
✓ KT USB Audio auto-detected by name hint
✓ Voice session: greeting spoken → mic recorded → ASR transcribed → clean exit
✓ /dev/ttyACM0 present, user in dialout
✓ /var/log on NVMe, survives reboot
✓ Face renders and animates — 6 lip-sync expressions x 3 frames + neutral,
  3 expression-mode sets x 30 frames; animation queue drains 39/39
```

**Known latency, not yet addressed:** `pyaudio.PyAudio()` takes **~640 ms** (it enumerates 35 ALSA devices) and is constructed twice per conversational turn — once in `riva_speech.speak()`, once in `riva_mic_asr._record_with_vad()`. That is ~1.3 s of pure overhead per exchange. Reusing one process-wide instance would remove it; the adapters currently build and tear one down per call.

---

## 10. Quick triage

| Symptom | Cause | Action |
|---|---|---|
| "Robot session ended" instantly | An exception before the voice loop | Run the python command directly (§5) |
| `AttributeError: X509_V_FLAG_*` | pyOpenSSL/cryptography mismatch | Confirm `usercustomize.py` exists in `reza_local` (§3) |
| Riva port open but nothing works | docker-proxy binds early | Check the log with `--since`, not the port (§1) |
| `failed to load all models` | CUDA OOM from fragmentation | Check `lfb`; reboot (§4) |
| **Face loads but never animates** | **Qt5 OpenCV won over GTK2** | Confirm `run_robot.sh` prepends `/usr/lib/python3.8/dist-packages` (§3) |
| `[FACE] Assets path not found` | Asset path drifted again | §6 |
| `Frame index N out of range` | `full_assets_path` vs frame range mismatch | §6 |
| Session quits on its own | `"stop"`/`"quit"` substring match | §6 |
| `Expression 'neutral' not found` | Name mismatch with planner | §6 |

---

## 11. Suggested next fixes, in order

1. ~~**Asset paths**~~ ✅ done
2. ~~**Remove `2>/dev/null`**~~ ✅ done — replaced with an ALSA filter
3. **Reuse one `PyAudio` instance** — removes ~1.3 s per turn (§9)
4. **`\\n` → `\n`** in `bedrock_llm.py` and `arduino_serial.py` — better replies, ~1 s faster gestures
5. **Tighten quit/movement matching** to whole-word or exact-phrase
6. **Fix `start_riva_v2_14.sh`**, then re-enable `riva.service` for autostart
7. **Consolidate Python packages** into `/mnt/nvme/reza_local`, de-duplicate `~/.bashrc:127`, and remove the Qt5 OpenCV so §3's cv2 workaround is no longer needed
