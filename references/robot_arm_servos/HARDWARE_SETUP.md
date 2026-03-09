# RobotArmServos Hardware Reference

This document consolidates hardware information from the RobotArmServos repository.

## Overview

The robotic system uses two Arduino Mega 2560 boards:
- **Arduino #1 (Official):** Finger servo control (10 servos) + arm servos (6 servos)
- **Arduino #2 (Clone):** Omnidirectional wheel motor control (4 DC motors)

Communication between Python and Arduino happens via JSON-line protocol over serial.

## Arduino #1: Finger Servo Control

### Pin Assignments

#### RIGHT HAND (Pins 2-6)
```
D2  - Right Thumb
D3  - Right Index Finger
D4  - Right Middle Finger
D5  - Right Ring Finger
D6  - Right Pinky Finger
```

#### LEFT HAND (Pins 7-11)
```
D7  - Left Thumb
D8  - Left Index Finger
D9  - Left Middle Finger
D10 - Left Ring Finger
D11 - Left Pinky Finger
```

#### ARM SERVOS (Currently Disabled)
```
LEFT ARM:
  D17 - Shoulder #1 (signal), D33 - Power
  D24 - Elbow (signal), D34 - Power
  D25 - Shoulder #2 (signal), D35 - Power

RIGHT ARM:
  D14 - Shoulder #1 (signal), D30 - Power
  D16 - Elbow (signal), D32 - Power
  D15 - Shoulder #2 (signal), D31 - Power
```

### Servo Specifications

**MG996R Servo Motor**
- Voltage: 4.8-7.4V (nominal 5V)
- Torque: ~10 kg-cm at 5V
- Speed: 0.2s/60°
- Rotation: 0-180°
- Pulse range: 500-2500µs (safe: 600-2400µs)

### Servo Calibration Values

#### RIGHT HAND
```cpp
const int THUMB_OPEN  = 1500, THUMB_CLOSE  = 2300;
const int INDEX_OPEN  = 2000, INDEX_CLOSE  = 700;
const int MIDDLE_OPEN = 2000, MIDDLE_CLOSE = 700;
const int RING_OPEN   = 2000, RING_CLOSE   = 700;
const int PINKY_OPEN  = 2000, PINKY_CLOSE  = 700;
```

#### LEFT HAND (Mirrored)
```cpp
const int LTHUMB_OPEN  = 1500, LTHUMB_CLOSE  = 740;
const int LINDEX_OPEN  = 700,  LINDEX_CLOSE  = 2000;
const int LMIDDLE_OPEN = 700,  LMIDDLE_CLOSE = 2000;
const int LRING_OPEN   = 700,  LRING_CLOSE   = 2000;
const int LPINKY_OPEN  = 700,  LPINKY_CLOSE  = 2000;
```

All values in **microseconds (µs)**.

To recalibrate:
1. Edit the constant values in `arduino/finger_servos/finger_servos.ino`
2. Upload to Arduino
3. Test motion with `examples/test_scripts/test_finger_serial.py`
4. Adjust incrementally (±50µs per iteration)

### Power Supply

- **Requirements:** 5V @ 10A
- **Configuration:** External regulated power supply + buck converter
- **Voltage stability:** Must maintain >4.8V under load

Connection:
```
PSU +5V → Servo power rail (red wires)
PSU GND → Arduino GND, Servo GND (black wires)
```

### Serial Communication

**Port:** `/dev/ttyACM0` (Linux) or `COM3`/`COM4` (Windows)  
**Baud:** 115200  
**Format:** JSON-line (newline-terminated JSON objects)

Example commands:
```json
{"type":"gesture","gesture":"wave","hand":"right","duration_ms":2000}
{"type":"gesture","gesture":"point","hand":"right","finger":"index"}
```

## Arduino #2: Motor Control

### Pin Assignments

#### Motor Pins
```
Motor A (Front-Left):
  PWM: D11, Direction: D34/D35

Motor B (Front-Right):
  PWM: D7, Direction: D36/D37

Motor C (Back-Left):
  PWM: D6, Direction: D43/D42

Motor D (Back-Right):
  PWM: D4, Direction: A5/A4
```

#### PS2 Controller Pins
```
D9  - DATA
D10 - CMD
D13 - SELECT
D44 - CLOCK
```

### DC Motor Specifications

**4x Gear Motor (one per wheel)**
- Voltage: 12V DC
- Speed: 200-300 RPM
- Torque: 3-5 kg-cm
- Current: 0.5-1A continuous, 2-3A stall

### Motor Driver

**L298N or similar**
- Handles up to 2A per channel
- Requires heatsink for continuous operation
- Logic voltage: 5V (from Arduino)
- Power voltage: 12V (from battery)

### Power Supply

- **Requirements:** 12V @ 5A
- **Configuration:** Separate from servo power supply
- **Connection:** Motor driver → Motors

### Speed Control

Adjusted via software constants:
```cpp
const int BASE_SPEED = 150;      // Max PWM (0-255)
const float SPEED_RATIO = 0.2;   // 0.1-1.0 scale
const int RAMP_RATE = 100;       // Acceleration smoothing
```

### Serial Communication

**Port:** `/dev/ttyUSB0` (Linux) or `COM5+` (Windows)  
**Baud:** 9600  
**Input:** PS2 Wireless Controller  
**Output:** Debug messages

## Assembly Wiring Checklist

- [ ] All servo signal pins connected to correct Arduino pins
- [ ] All servo power wires (red) to +5V rail
- [ ] All servo ground wires (black) to GND rail
- [ ] All servo ground to Arduino GND
- [ ] Motor power wires to 12V supply via motor driver
- [ ] Motor driver outputs to motor terminals
- [ ] Motor driver logic inputs to Arduino pins
- [ ] PS2 controller pins correctly wired
- [ ] Ground plane continuous across all boards
- [ ] No voltage drops >0.5V under full load

## Testing

### Finger Servo Test
```bash
python examples/test_scripts/test_finger_serial.py
```

### Motor Test
```bash
python examples/test_scripts/test_motor_serial.py
# Move PS2 controller to test all directions
```

### Individual Servo Test
```cpp
// In Arduino IDE, create test sketch:
#include <Servo.h>
Servo testServo;
void setup() { testServo.attach(2); } // or any servo pin
void loop() {
  for(int us = 600; us <= 2400; us += 50) {
    testServo.writeMicroseconds(us);
    delay(100);
  }
}
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Servos jittering | Check power supply voltage stability |
| Servo not moving | Verify pin assignment, check calibration range |
| Motor not spinning | Check motor driver logic, verify 12V supply |
| Serial communication fails | Check baud rate, test with `screen /dev/ttyACM0` |
| Arduino not uploading | Check USB cable, install drivers |

## Future Enhancements

- [ ] Add servo current limiting (prevent stall damage)
- [ ] Implement feedback via potentiometer or encoder
- [ ] Add temperature monitoring on motor driver
- [ ] Wireless PS2 controller battery monitoring
- [ ] Autonomous motion using LiDAR feedback

## References

- MG996R Servo Datasheet
- L298N Motor Driver Datasheet
- Arduino Mega 2560 Pinout
- PS2X Library: https://github.com/madsci1016/Arduino-PS2X

See Also:
- [Complete Pin Mapping](../../hardware/pinouts/PIN_MAPPING.md)
- [Calibration Procedures](../../hardware/calibration/CALIBRATION.md)
- [Component Specifications](../../hardware/specs/SPECIFICATIONS.md)
