# API Contract (v1)

## Gesture command envelope (Jetson -> Arduino)

JSON line messages:

```json
{"type":"gesture_start","name":"fingers_wave"}
{"type":"gesture_stop","name":"fingers_wave"}
```

## Allowed gesture names (default)

- `fingers_wave`
- `fingers_point`
- `fingers_open`
- `fingers_close`

## Safety policy

- Arm commands are rejected while `safety.enable_main_arms=false`.
- Finger gestures only are accepted in v1.

## Runtime flow

1. `SpeechPort.speak()` starts
2. `FacePort.set_expression()` to planned expression
3. `GesturePort.start_gesture()`
4. Speech playback
5. `GesturePort.stop_gesture()`
6. `FacePort.set_expression(neutral)`
7. Session metadata persisted through `StoragePort`
