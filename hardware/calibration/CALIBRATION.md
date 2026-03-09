# Hardware Calibration Data

## Servo Calibration Procedure

### Tools Required
- Arduino IDE or CLI
- Serial monitor (9600 baud for servo verification)
- Servo test sketch (recommended: single servo control)
- Calipers or measurement tool (optional, for mechanical verification)

### Step 1: Test Single Servo

Create a test sketch for one servo:
```cpp
#include <Servo.h>

Servo testServo;
int pin = 2; // Change to servo pin being tested

void setup() {
  testServo.attach(pin);
  Serial.begin(115200);
}

void loop() {
  // Sweep 600-2400 µs
  for (int us = 600; us <= 2400; us += 50) {
    testServo.writeMicroseconds(us);
    Serial.println(us);
    delay(500);
  }
  delay(2000);
}
```

### Step 2: Record Endpoints

For each finger servo, record:
1. **Minimum position** (fully open): Start at 600µs, increase until servo moves noticeably
2. **Maximum position** (fully closed): Start at 2400µs, decrease until servo stops moving
3. **Neutral position** (middle): Usually ~1500µs but verify by feel

### Current Calibration Values

#### RIGHT HAND (as of Feb 10, 2025)
| Finger | Open (µs) | Close (µs) | Notes |
|--------|-----------|-----------|-------|
| Thumb (D2) | 1500 | 2300 | Reduced range - verify not stalling |
| Index (D3) | 2000 | 700 | Full range used |
| Middle (D4) | 2000 | 700 | Full range used |
| Ring (D5) | 2000 | 700 | Full range used |
| Pinky (D6) | 2000 | 700 | Full range used |

#### LEFT HAND (mirrored)
| Finger | Open (µs) | Close (µs) | Notes |
|--------|-----------|-----------|-------|
| Thumb (D7) | 1500 | 740 | Mirrored thumb |
| Index (D8) | 700 | 2000 | Reversed from right |
| Middle (D9) | 700 | 2000 | Reversed from right |
| Ring (D10) | 700 | 2000 | Reversed from right |
| Pinky (D11) | 700 | 2000 | Reversed from right |

### Step 3: Verify Smoothness

Test with the finger wave pattern:
```cpp
// In finger_servos.ino, verify PHASE_DELAY (120ms) is adequate
// If servo jitters, reduce UPDATE_MS from 20 to 10
// If servo moves too slowly, reduce HALF_MOVE from 800 to 600
```

### Step 4: Load Test

Power supply stability is critical. Record measurements under load:
1. Single servo moving: Should not drop below 4.8V
2. Multiple servos moving: Should not drop below 4.5V
3. If voltage sags, use external 5V/10A power supply

## Mechanical Calibration Notes

### Servo Gear Wear
- MG996R servos can develop play after 1000+ hours
- If servo has ~100µs dead zone, it's normal aging
- Replace if dead zone exceeds 200µs

### Servo Centering
Some servos need mechanical recalibration:
1. Disconnect servo horn
2. Center servo with 1500µs pulse
3. Physically reposition horn to neutral
4. Reattach and test

## Motor Speed Calibration

### DC Motor Speed Verification
Test script for consistent motor speeds:
```cpp
// Set PWM to same value for all motors, measure actual speed
// If unequal, adjust SPEED_RATIO or individual motor PWM pins

const int TEST_SPEED = 150;
// Motor A: setMotor(PWMA, DIRA1, DIRA2, TEST_SPEED);
// Motor B: setMotor(PWMB, DIRB1, DIRB2, TEST_SPEED);
// Motor C: setMotor(PWMC, DIRC1, DIRC2, TEST_SPEED);
// Motor D: setMotor(PWMD, DIRD1, DIRD2, TEST_SPEED);
// Time 1 meter distance for each
```

### Typical Speeds (with SPEED_RATIO=0.2, BASE_SPEED=150)
- Effective PWM: 30 (full speed ~2 m/s on flat surface)
- Adjust SPEED_RATIO up to 1.0 for faster movement
- Adjust down for finer control

## Voltage Stability Monitoring

### Power Supply Test
1. Measure resting voltage: Should be 5.0V ± 0.2V (servos), 12.0V ± 0.5V (motors)
2. Measure under load: Servos moving
3. Measure max load: All servos + motors active
4. If sag >0.5V, upgrade power supply

### Arduino 5V Rail Test
With USB-only power and servos active:
- Typical: 4.8-5.0V
- If <4.5V: Use external 5V power supply

## Adjustment Workflow

To retune any servo:
1. Edit constant in code (THUMB_OPEN, INDEX_CLOSE, etc.)
2. Compile and upload
3. Observe servo movement
4. If not enough travel, expand range by 50µs
5. If overshooting, contract by 50µs
6. Repeat until satisfied

## Historical Calibration Data

**Last Updated:** Feb 10, 2025

All finger servos: MG996R (continuous torque design)
- Operating temp: 20-40°C
- Supply voltage: 5V nominal (6-7.4V tolerates)
- Torque: ~10 kg-cm at 5V

## Maintenance Schedule

- **Weekly:** Check for loose servo horns, verify no stalling sounds
- **Monthly:** Test full range motion, verify speed consistency  
- **Quarterly:** Recalibrate if values drift >100µs from baseline
- **Annually:** Replace worn servo horns, consider bearing replacement

## Files in This Directory

- `CALIBRATION.md` - This file
- `servo_test.ino` - (To be created) Single servo test sketch
- `motor_speed_test.ino` - (To be created) Motor speed verification
