# Gesture Pattern Definitions

This directory contains gesture pattern definitions used for coordinated hand and finger movements.

## Gesture Types

### Single Hand Gestures
- `wave` - Waving motion (fingers open/close sequentially)
- `open_hand` - All fingers extended
- `close_hand` - All fingers closed into fist
- `point` - Index finger extended, others closed
- `peace` - Index and middle fingers extended
- `thumbs_up` - Thumb extended, fingers closed
- `thumbs_down` - Thumb extended down, fingers closed
- `ok_sign` - Thumb and index forming circle, others extended

### Two-Hand Gestures  
- `clap` - Both hands coming together
- `surrender` - Both hands open above head
- `timeout` - One hand flat, other vertical (T-shape)
- `hug` - Both arms coming in

### Expression Gestures
- `celebrate` - Both arms raised, hands opening/closing
- `think` - Hand to chin (requires arm integration)
- `confused` - Hands up in questioning motion

## JSON Command Format

All gestures are sent to Arduino as JSON commands:

```json
{
  "type": "gesture",
  "gesture": "wave",
  "hand": "right",
  "duration_ms": 3000,
  "speed": 1.0,
  "repeat": 1
}
```

### Parameters

- `type` (string): Always "gesture"
- `gesture` (string): Gesture name from list above
- `hand` (string): "left", "right", or "both"
- `duration_ms` (integer): Total execution time
- `speed` (float): 0.5-2.0, where 1.0 is normal speed
- `repeat` (integer): Number of times to repeat (optional, default=1)

## Examples

### Wave greeting
```json
{"type": "gesture", "gesture": "wave", "hand": "right", "duration_ms": 2000}
```

### Quick double thumbs up
```json
{"type": "gesture", "gesture": "thumbs_up", "hand": "both", "repeat": 2}
```

### Extended peace sign
```json
{"type": "gesture", "gesture": "peace", "hand": "left", "duration_ms": 3000, "speed": 0.8}
```

## Servo Timing

Each gesture is timed using the finger servo calibration values:
- `THUMB_OPEN=1500, THUMB_CLOSE=2300`
- `INDEX_OPEN=2000, INDEX_CLOSE=700`
- (See hardware/calibration/CALIBRATION.md for complete list)

Movement timing parameters:
- `PHASE_DELAY=120ms` - Spacing between fingers (for wave effect)
- `HALF_MOVE=800ms` - Time for one direction of motion
- `UPDATE_MS=20ms` - Control loop frequency

## Gesture Implementation (Arduino)

In `finger_servos.ino`, gestures are implemented as servo position sequences:

```cpp
// Example: wave gesture
void waveGesture(String hand) {
  // Set up timing for all 5 fingers in sequence
  // Use wavePos() function for smooth interpolation
  // Track elapsed time and update all servos
}
```

## Customizing Gestures

To create a new gesture:

1. Identify which fingers/servos are involved
2. Define open/close positions (or intermediate positions)
3. Create timing sequence (which finger moves when)
4. Test with servo calibration values
5. Add JSON mapping in voice-to-gesture layer

## Configuration File Location

Runtime gesture mappings are defined in:
- `config/config.yaml` - Main configuration
- Section: `gestures:`

Example config:
```yaml
gestures:
  wave:
    hand: right
    duration_ms: 2000
    repeat: 1
  point:
    hand: right
    finger: index
    duration_ms: 1500
```

## Testing Gestures

Use the provided test scripts:

```bash
# Test specific gesture
python examples/test_scripts/test_finger_serial.py

# Test voice integration
python examples/voice_chat/voice_chat_example.py --gesture wave
```

## Integration with Voice System

The voice pipeline maps LLM outputs to gestures:

1. User speaks: "Can you wave at me?"
2. Riva ASR transcribes to text
3. Bedrock LLM processes and responds
4. BehaviorPlanner maps keywords to gestures
5. ArduinoSerialGestureAdapter sends JSON to Arduino
6. Arduino #1 executes the gesture

Gesture keywords are matched in the LLM response, triggering corresponding animations.
