# Arduino Finger Servo Control

## Board: Arduino Mega 2560 (Official FTDI)

**Upload Port:** `/dev/ttyACM0` (Linux) or `COM3-4` (Windows)  
**Serial Speed:** 115200 baud  
**Function:** Controls 10 finger servos (5 per hand) + arm servos  

## Pin Mapping

### RIGHT HAND (Pins 2-6)
| Finger | Pin | Open (µs) | Close (µs) | Servo Type |
|--------|-----|-----------|-----------|------------|
| Thumb  | 2   | 1500      | 2300      | Positional |
| Index  | 3   | 2000      | 700       | Positional |
| Middle | 4   | 2000      | 700       | Positional |
| Ring   | 5   | 2000      | 700       | Positional |
| Pinky  | 6   | 2000      | 700       | Positional |

### LEFT HAND (Pins 7-11)
| Finger | Pin | Open (µs) | Close (µs) | Servo Type |
|--------|-----|-----------|-----------|------------|
| Thumb  | 7   | 1500      | 740       | Positional |
| Index  | 8   | 700       | 2000      | Positional |
| Middle | 9   | 700       | 2000      | Positional |
| Ring   | 10  | 700       | 2000      | Positional |
| Pinky  | 11  | 700       | 2000      | Positional |

### ARM SERVOS (Currently Disabled - Set EN_* flags to true to enable)

**LEFT ARM:**
- Shoulder #1: Signal=D17, Power=D33 (Continuous)
- Shoulder #2: Signal=D25, Power=D35 (Continuous)
- Elbow: Signal=D24, Power=D34 (Positional)

**RIGHT ARM:**
- Shoulder #1: Signal=D14, Power=D30 (Continuous)
- Shoulder #2: Signal=D15, Power=D31 (Continuous)
- Elbow: Signal=D16, Power=D32 (Positional)

## Servo Calibration

All values are in **microseconds (µs)**:
- **Positional servos:** 600-2400 µs (safe range)
- **Continuous servos:** 1500 µs = neutral, <1500 = one direction, >1500 = opposite

To recalibrate:
1. Open `finger_servos.ino`
2. Find the `const int` declarations for OPEN/CLOSE values
3. Adjust incrementally (e.g., 100µs steps)
4. Recompile and upload

## Communication Protocol

Receives JSON commands via serial (115200 baud) from Python:
```json
{
  "type": "gesture",
  "gesture": "wave",
  "hand": "right",
  "duration_ms": 2000
}
```

## Timing Configuration

**Finger Wave:**
- `PHASE_DELAY`: 120ms (spacing between fingers)
- `HALF_MOVE`: 800ms (time for one direction)
- `UPDATE_MS`: 20ms (control loop frequency)

**Arm Movement:**
- LEFT arm: 2000ms up, 180ms pause, 1570ms down
- RIGHT arm: 2000ms up, 180ms pause, 1900ms down

## Power Requirements

- **Servo supply:** 5V @ 10A (10 servos max draw)
- **Arduino:** 5V @ 500mA (USB or external)
- **Recommendation:** Separate power supply for servos

## Uploading Code

```bash
# Linux
arduino --upload --board arduino:avr:megaatmega2560 --port /dev/ttyACM0 finger_servos.ino

# Or use Arduino IDE
# 1. Select Board: Arduino Mega 2560
# 2. Select Port: /dev/ttyACM0
# 3. Sketch > Upload
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Servos jittering | Check power supply stability, reduce UPDATE_MS |
| Some servos not responding | Verify pin assignments, check servo power connections |
| Serial communication fails | Confirm baud rate is 115200, check USB port |
| Arm servos disabled | Set `EN_*` flags to `true` in code |

## Files in This Directory

- `finger_servos.ino` - Main sketch with all servo control
- `pins.h` - Pin definitions (future modularization)
- `README.md` - This file

## See Also

- [Hardware Pinouts](../../../hardware/pinouts/)
- [Calibration Data](../../../hardware/calibration/)
- [Voice Control Integration](../../../references/chatbot_robot/)
