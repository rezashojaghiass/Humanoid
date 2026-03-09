# Hardware Pin Mapping

## Complete System Pin Assignment

### Arduino #1 (Official FTDI) - Finger Control
**Port:** `/dev/ttyACM0` @ 115200 baud

#### Servo Pins (Digital I/O)
```
RIGHT HAND:
- Thumb:  D2
- Index:  D3
- Middle: D4
- Ring:   D5
- Pinky:  D6

LEFT HAND:
- Thumb:  D7
- Index:  D8
- Middle: D9
- Ring:   D10
- Pinky:  D11
```

#### ARM Servo Pins (if enabled)
```
LEFT ARM:
- Shoulder #1: Signal=D17, Power=D33 (Continuous rotation)
- Shoulder #2: Signal=D25, Power=D35 (Continuous rotation)
- Elbow:       Signal=D24, Power=D34 (Positional)

RIGHT ARM:
- Shoulder #1: Signal=D14, Power=D30 (Continuous rotation)
- Shoulder #2: Signal=D15, Power=D31 (Continuous rotation)
- Elbow:       Signal=D16, Power=D32 (Positional)
```

### Arduino #2 (Clone CH340) - Motor Control
**Port:** `/dev/ttyUSB0` @ 9600 baud

#### Motor PWM Pins
```
Motor A (Front-Left):  PWM=11, Dir1=34, Dir2=35
Motor B (Front-Right): PWM=7,  Dir1=36, Dir2=37
Motor C (Back-Left):   PWM=6,  Dir1=43, Dir2=42
Motor D (Back-Right):  PWM=4,  Dir1=A5, Dir2=A4
```

#### PS2 Controller Pins
```
DATA:   D9
CMD:    D10
SELECT: D13
CLOCK:  D44
```

## Servo Calibration Values

All values in **microseconds (µs)** (1ms = 1000µs)

### RIGHT HAND
```
Thumb:  Open=1500µs,  Close=2300µs
Index:  Open=2000µs,  Close=700µs
Middle: Open=2000µs,  Close=700µs
Ring:   Open=2000µs,  Close=700µs
Pinky:  Open=2000µs,  Close=700µs
```

### LEFT HAND (mirrored from right)
```
Thumb:  Open=1500µs,  Close=740µs
Index:  Open=700µs,   Close=2000µs
Middle: Open=700µs,   Close=2000µs
Ring:   Open=700µs,   Close=2000µs
Pinky:  Open=700µs,   Close=2000µs
```

### ARM SERVOS (Continuous)
```
LEFT SHOULDER #1:
  Down=700µs, Neutral=1370µs, Up=1700µs

LEFT SHOULDER #2:
  Down=700µs, Neutral=1500µs, Up=2300µs

LEFT ELBOW (Positional):
  Open=880µs, Close=1500µs

RIGHT SHOULDER #1:
  Down=1300µs, Neutral=1460µs, Up=1900µs

RIGHT SHOULDER #2:
  Down=600µs, Neutral=1460µs, Up=2300µs

RIGHT ELBOW (Positional):
  Open=1200µs, Close=1800µs
```

## Power Distribution

### 5V Power Supply (Servos)
- All finger servos: 10 × MG996R (6V/7.4V max)
- Supply: 5V @ 10A (heavy load)
- Per servo: ~0.5-1A stall current

**Wiring:**
- Red wire → +5V
- Black wire → GND
- White/Yellow wire → Signal pin

### 12V Power Supply (Motors)
- Motor A: 12V DC @ 2A max
- Motor B: 12V DC @ 2A max
- Motor C: 12V DC @ 2A max
- Motor D: 12V DC @ 2A max
- Total: 12V @ 5-8A under load

**Wiring (typical L298N or similar driver):**
- +12V → Motor driver IN1/IN2
- GND → Motor driver GND
- OUT1/OUT2 → Motor leads

### Arduino 5V Power
- USB: 500mA max
- External: 5V @ 1A (if using external power)

**Recommended Setup:**
1. Servo supply: 5V @ 10A PSU with voltage regulator
2. Motor supply: 12V @ 10A PSU
3. Arduino: USB power from host computer (or external 5V)
4. All grounds tied together

## Connector Types

### Servo Connectors
- **Standard:** 3-pin 0.1" header (GND-VCC-SIGNAL)
- **Alternate:** JST XH 2.54mm if using aftermarket connectors

### Motor Connectors  
- **Motor leads:** 2-pin deans or bullet connectors
- **Motor driver:** Terminal blocks or deans

## Serial Communication

### Arduino #1 (Fingers)
```
Device:     /dev/ttyACM0 (Linux) or COM3/4 (Windows)
Baud Rate:  115200
Data Bits:  8
Stop Bits:  1
Parity:     None
Flow Ctrl:  None

Protocol:   JSON-line format
```

Example commands from Python:
```json
{"type":"gesture","gesture":"wave","hand":"right"}
{"type":"gesture","gesture":"open_hand","hand":"left"}
{"type":"gesture","gesture":"point","hand":"right","finger":"index"}
```

### Arduino #2 (Motors)
```
Device:     /dev/ttyUSB0 (Linux) or COM5+ (Windows)
Baud Rate:  9600
Data Bits:  8
Stop Bits:  1
Parity:     None
Flow Ctrl:  None

Input:      PS2 Wireless Controller
Output:     Serial debug messages
```

## Safety Limits

- **Servo pulse width:** 600-2400 µs (enforced in firmware)
- **PWM output:** 0-255 (enforced by analogWrite)
- **Motor ramp rate:** 100 units/loop (prevents sudden acceleration)
- **Finger safe default:** Fully open (arm servos disabled)

## Troubleshooting Checklist

- [ ] All servo power wires solid and no voltage sag
- [ ] All ground connections secure
- [ ] Serial ports correctly identified and accessible
- [ ] Baud rates match (115200 for fingers, 9600 for motors)
- [ ] No pin conflicts between sketches
- [ ] Servo calibration values reasonable (600-2400µs range)
- [ ] Motor power supply voltage stable (12V ±0.5V)
- [ ] PS2 controller batteries fresh
