# Component Specifications

## Servo Motors

### Finger Servos - MG996R
**Quantity:** 10 (5 per hand)  
**Connector:** 3-pin 0.1" header (GND-VCC-SIGNAL)

| Specification | Value |
|---|---|
| Operating Voltage | 4.8-7.4V (nominal 5V) |
| Torque @ 5V | 10 kg-cm (~1 Nm) |
| Speed @ 5V | 0.2 sec/60° |
| Rotation | 180° positional |
| Dead band | ~5-10µs |
| Pulse range | 500-2500 µs (safe: 600-2400) |
| Dimensions | 40.7×19.7×43.2 mm |
| Weight | 55g |

**Notes:**
- High-torque design with metal gears
- Suitable for continuous waving motion
- Can handle stall current (requires current limiting)

### Arm Servos (Currently Unused)
**Specified:** MG996R or similar  
**Note:** Currently disabled in firmware (set EN_* = true to enable)

## DC Motors (Omnidirectional Base)

### 4x DC Gear Motors
**Quantity:** 4 (one per wheel)  
**Connector:** 2-pin deans or JST

| Specification | Value |
|---|---|
| Nominal Voltage | 12V DC |
| No-load Speed | 200-300 RPM (depends on gearbox) |
| Stall Torque | 3-5 kg-cm |
| Stall Current | 2-3A per motor |
| Operating Current | 0.5-1A continuous |
| Motor Type | Brushed DC with spur gearbox |

**Notes:**
- 90-degree gearbox for direct wheel drive
- Rated for continuous operation
- Overheating possible at 100% PWM for >10 minutes

## Microcontrollers

### Arduino #1 - Official Servo Control
**Board:** Arduino Mega 2560 (Official FTDI)  
**Processor:** ATmega2560  
**Flash Memory:** 256 KB  
**SRAM:** 8 KB  
**Clock:** 16 MHz  
**I/O Pins:** 54 digital + 16 analog  

**Features:**
- 4 UART ports (main: D0/D1 @ 115200)
- PWM on pins 2-13, 44-46
- Official FTDI USB chip (reliable uploads)

### Arduino #2 - Motor Control Base
**Board:** Arduino Mega 2560 Clone (CH340)  
**Processor:** ATmega2560  
**Clock:** 16 MHz (Chinese clone, may vary)  

**Caveats:**
- CH340 USB chip (driver required: https://www.wch.cn/downloads/CH341SER_EXE.html)
- Port may appear as /dev/ttyUSB0 or /dev/ttyUSB1
- Less reliable than official, but functional

## Motor Drivers

### L298N (Typical for DC Motor Control)
**Quantity:** 1-2 (handles 2-4 motors)  

| Specification | Value |
|---|---|
| Input Voltage | 5-35V (motors: 12V recommended) |
| Logic Voltage | 5V (from Arduino) |
| Max Current/Channel | 2A continuous, 3A peak |
| Number of Channels | 2 (controls 2 motors with direction) |
| Pinout | IN1/IN2 = direction, ENA = PWM speed |

**Heat dissipation:**
- Requires heatsink if running 4 motors continuously
- Recommended: Add 40x40mm aluminum heatsink + thermal paste

## Power Supplies

### Servo Power - 5V @ 10A
**Recommended:** Regulated 5V PSU with XT60 or barrel connector  

Voltage headroom calculation:
- 10 MG996R servos at 1A stall = 10A peak
- Servo internal resistance ~0.5Ω → 5V drop
- Supply must maintain >4.8V under load

### Motor Power - 12V @ 5A
**Recommended:** Regulated 12V PSU, automotive-grade  

Load calculation:
- 4 motors × 1.5A average = 6A peak
- Supply should be 12V ± 0.5V

### Arduino Power - 5V @ 1A
**Source:** USB from computer (sufficient)  
**Alternative:** External regulated 5V (if debugging without USB)

## Audio Hardware

### Microphone Input
**Device:** Wireless GO II by Rode  
**Sample Rate:** 48 kHz (down-resampled to 16 kHz for Riva)  
**Impedance:** 32Ω  

**Connection:** USB-A to host computer or Jetson Xavier

### Speaker Output  
**Device:** KT USB Speaker (typical USB stereo speaker)  
**Sample Rate:** 48 kHz (supported)  
**Power:** USB powered  

**Connection:** USB-A to host computer or Jetson Xavier

## Communication Interfaces

### Serial Ports (Arduino)
| Device | Port | Baud | Protocol |
|--------|------|------|----------|
| Arduino #1 (Fingers) | /dev/ttyACM0 | 115200 | JSON-line |
| Arduino #2 (Motors) | /dev/ttyUSB0 | 9600 | Debug output |
| LiDAR (Future) | /dev/ttyUSB1 | 2,000,000 | Binary protocol |

## Mechanical Specifications

### Servo Horn Sizes
- Finger servos: 25mm cross-shaped horns (standard MG996R)
- Arm servos: Multi-horn compatible

### Motor Mounting
- Typical 90-degree gearbox output shaft: 6mm D-shaft
- Wheel interface: 6mm bore hubs (common)
- Wheel size: Typically 60-80mm for omni-wheels

### Wiring Gauge
- Servo signal: 24 AWG (common control wire)
- Servo power: 18 AWG minimum (better: 16 AWG)
- Motor power: 14 AWG (for 5A+ currents)
- Ground: Same as power wire gauge

## Environmental Specifications

| Parameter | Operating Range | Storage Range |
|---|---|---|
| Temperature | 0-50°C | -10-60°C |
| Humidity | 10-90% RH (non-condensing) | <95% RH |
| Vibration | <1G | <2G |
| Operating Altitude | <3000m | <5000m |

## Reliability/MTBF (Mean Time Between Failure)

| Component | MTBF | Notes |
|---|---|---|
| MG996R Servo | ~2000 hours | Bearing wear, gear grinding |
| DC Motor | ~3000 hours | Brush wear, coil insulation |
| Arduino (Official) | >10,000 hours | Very reliable |
| Arduino (Clone) | ~5,000 hours | USB chip less stable |
| L298N | ~5,000 hours | Thermal stress primary failure mode |

## Files in This Directory

- `SPECIFICATIONS.md` - This file
- `pinouts/PIN_MAPPING.md` - Detailed pin assignments
- `calibration/CALIBRATION.md` - Servo and motor calibration procedures
- `schematics/` - (To be added) Circuit diagrams
