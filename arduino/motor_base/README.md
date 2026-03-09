# Arduino Motor Base Control

## Board: Arduino Mega 2560 Clone (CH340)

**Upload Port:** `/dev/ttyUSB0` or `/dev/ttyUSB1` (Linux)  
**Serial Speed:** 9600 baud  
**Function:** Controls 4 DC motors for omnidirectional movement  
**Input:** PS2 Controller wireless gamepad  

⚠️ **DO NOT upload to Arduino #1 (Official) - This is for Arduino #2 (Clone)**

## Motor Configuration

### Wheel Layout
```
        FRONT
    MotorA --- MotorB
      (FL)     (FR)
    
    MotorC --- MotorD
      (BL)     (BR)
        BACK
```

| Motor | Location | PWM Pin | Dir1 Pin | Dir2 Pin | Polarity |
|-------|----------|---------|----------|----------|----------|
| A | Front-Left | 11 | 34 | 35 | Forward=HIGH/LOW |
| B | Front-Right | 7 | 36 | 37 | Forward=HIGH/LOW |
| C | Back-Left | 6 | 43 | 42 | Forward=HIGH/LOW |
| D | Back-Right | 4 | A5 | A4 | Forward=HIGH/LOW |

## PS2 Controller Mapping

| Input | Action |
|-------|--------|
| Left Stick UP | Move Forward |
| Left Stick DOWN | Move Backward |
| Left Stick LEFT | Strafe Left |
| Left Stick RIGHT | Strafe Right |
| Right Stick LEFT | Rotate Counter-clockwise |
| Right Stick RIGHT | Rotate Clockwise |

## Speed Control

All tuning parameters in code:
```cpp
const int BASE_SPEED = 150;      // Max speed (0-255 PWM)
const float SPEED_RATIO = 0.2;   // 0.1-1.0 scale factor
const int RAMP_RATE = 100;       // Acceleration/deceleration smoothing
```

## Serial Debug Output

The Arduino prints movement status to Serial at 9600 baud:
```
⬆️ Moving Forward
➡️ Strafing Right
↪️ Rotating Right
🛑 Stopped
```

Useful for debugging with Serial Monitor.

## Uploading Code

```bash
# Linux - using Arduino CLI
arduino --upload --board arduino:avr:megaatmega2560 --port /dev/ttyUSB0 motor_control.ino

# Or use Arduino IDE
# 1. Select Board: Arduino Mega 2560
# 2. Select Port: /dev/ttyUSB0
# 3. Sketch > Upload
```

## Motor Calibration

If motors have different speeds:
1. Set all motors to same PWM value
2. Adjust `SPEED_RATIO` or individual motor pins
3. Test with joystick input

## Power Requirements

- **4x DC Motors:** 12V @ 5A (when all moving)
- **Arduino:** 5V @ 500mA
- **PS2 Controller:** Internal battery
- **Recommendation:** 12V/5A supply for motors, USB for Arduino

## Wiring Checklist

- [ ] All motor power wires to 12V supply
- [ ] Motor ground wires to power ground
- [ ] All Arduino ground pins to power ground
- [ ] PWM pins connected to motor driver
- [ ] Direction pins connected correctly
- [ ] PS2 pins configured (DAT=9, CMD=10, SEL=13, CLK=44)
- [ ] Arduino powered via USB or external 5V

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Motors not moving | Check PS2 connection (error message printed) |
| Motors move wrong direction | Swap DIR1/DIR2 pins for that motor |
| Speed inconsistent | Increase RAMP_RATE, check power supply voltage |
| Joystick not responding | Re-run PS2 config in setup() |
| Serial errors | Verify baud rate is 9600 |

## Files in This Directory

- `motor_control.ino` - Main sketch
- `README.md` - This file

## See Also

- [Hardware Specifications](../../../hardware/specs/)
- [Motor Driver Datasheets](../../../hardware/schematics/)
- [Voice Control Integration](../../../references/robot_arm_servos/)
