# Servo Movement Logic - Complete Explanation

## Overview

The humanoid robot has 16 servos:
- **10 finger servos** (5 per hand) - wave continuously in a pattern
- **6 arm servos** (3 per arm)
  - 2 shoulder servos per arm (continuous rotation)
  - 1 elbow servo per arm (positional)

## Key Concept: Pulse Width Control

Servo motors are controlled by pulse width (measured in microseconds, µs):
- **Pulse width = servo position/speed**
- **Range: 600-2400 microseconds** (defined as `SERVO_MIN_US` and `SERVO_MAX_US`)

### Continuous vs Positional Servos

**Continuous Servos (Shoulders):**
- Rotate continuously in one direction
- Pulse width represents **speed** and **direction**
- Example: 1500µs = stop, 1700µs = rotate one way, 1300µs = rotate other way
- **Neutral point = 1500µs** (default "stopped" position)

**Positional Servos (Elbow, Fingers):**
- Move to specific positions
- Pulse width represents the **target position**
- Example: 880µs = open, 1500µs = closed
- Stop at the target, don't rotate continuously

## How Shoulder Movement Works

### The Movement Cycle

When you command "Left Shoulder One Up":

```
1. Power ON the servo
2. Set servo to target pulse width (e.g., 2100µs for UP)
3. WAIT for SHOULDER_STEP_MS milliseconds (currently 1000ms)
4. Return servo to NEUTRAL (1500µs)
5. WAIT 120ms
6. Power OFF
```

### Why This Works for 2x Amplification

**The servo moves TOWARDS the target at constant speed.**

- **Pulse width = 1500µs (neutral)**: Servo is stopped
- **Pulse width = 2100µs (UP target)**: Servo is told to rotate UP continuously

When you set the pulse width to 2100µs and WAIT 1000ms:
- The servo rotates UP for 1000ms at its normal speed
- It covers a certain distance in that 1 second

When you DOUBLE the wait time to 2000ms:
- The servo rotates UP for 2000ms at the SAME speed
- It covers TWICE the distance in 2 seconds

**This is why:** `SHOULDER_STEP_MS = 1000ms` (double the normal 500ms) gives 2x movement

---

## Arduino Implementation Details

### File: `finger_servos.ino`

#### Calibration Constants (Lines 123-141)

```cpp
// LEFT SHOULDER #1 (continuous)
const int LSH1_DOWN    = 700;       // Pulse width when moving DOWN
const int LSH1_NEUTRAL = 1370;      // Stopped position
const int LSH1_UP      = 1700;      // Pulse width when moving UP

// RIGHT SHOULDER #1 (continuous)
const int RSH1_DOWN    = 1300;      // Pulse width when moving DOWN
const int RSH1_NEUTRAL = 1460;      // Stopped position
const int RSH1_UP      = 1900;      // Pulse width when moving UP
```

**What these mean:**
- `UP = 1700µs`: Tells servo to rotate in UP direction at full speed
- `DOWN = 700µs`: Tells servo to rotate in DOWN direction at full speed
- `NEUTRAL = 1370µs`: Tells servo to stop (midpoint between UP and DOWN)

#### Timing Constants (Lines 433-434)

```cpp
const unsigned long ARM_STEP_MS      = 500;   // Normal arm movement (elbow, etc.)
const unsigned long SHOULDER_STEP_MS = 1000;  // Shoulder movement (2x longer = 2x distance)
```

**Why SHOULDER_STEP_MS is 2x:**
- At 500ms: Servo moves for half a second towards target
- At 1000ms: Servo moves for a full second towards target at SAME speed
- Result: 2x the distance covered

#### The Movement Function (Lines 751-809)

```cpp
void applyShoulderStep(const String &side, const String &joint, 
                       const String &direction) {
  // ... determine which servo and which target ...
  
  // 1. Power ON the servo
  powerOn(pwr);
  
  // 2. Set servo to target pulse width (UP or DOWN)
  s->attach(pin);
  s->writeMicroseconds(clampUs(target));
  
  // 3. WAIT for shoulder movement (1000ms = 2x longer than normal)
  delay(SHOULDER_STEP_MS);  // <-- KEY: 1000ms instead of 500ms
  
  // 4. Return to neutral/stopped
  s->writeMicroseconds(clampUs(neutral));
  delay(120);
  
  // 5. Power OFF
  s->detach();
  powerOff(pwr);
}
```

---

## Python Side: The "Amount" Parameter

### File: `voice_session_service.py`

When Python sends a movement command to Arduino, it can specify an `amount` parameter:

```python
# Python sends to Arduino (format): side:joint:direction:amount
# Example: "LEFT:SHOULDER1:UP:75"
```

**Current Arduino implementation:** The `amount` parameter is **ignored** for shoulders.

### Why Amount Was Ineffective for Shoulders

In `applyShoulderStep()`, the `amount` parameter is not used:
- It only uses fixed UP/DOWN pulse widths
- Movement duration is always fixed (500ms or 1000ms)
- No way to scale the movement based on amount

### The 5x Amplification in Python (Why It Didn't Work)

```python
# In voice_session_service.py, we added:
cmd_amplified["amount"] = max(1, min(100, cmd_amplified.get("amount", 15) * 5))
```

This sends `amount=75` instead of `amount=15`, but Arduino ignores it anyway.

**Solution:** Double the SHOULDER_STEP_MS timing instead (which we did!)

---

## Complete Movement Example

**Scenario:** User says "Left Shoulder One Up" then "Some More"

### First Command: "Left Shoulder One Up"

```
1. Python: Recognize voice input → "LEFT:SHOULDER1:UP:15"
2. Arduino: Execute applyShoulderStep("LEFT", "SHOULDER1", "UP")
   - Power ON L_SH1_PWR
   - Set pulse width to L_SH1_UP (1700µs) 
   - Wait 500ms ← servo rotates UP for 0.5s
   - Set pulse width to neutral (1370µs) → servo stops
   - Power OFF
3. Result: Shoulder rotates UP for 0.5 seconds
```

### Second Command: "Some More"

With 5x amplification in Python + 2x SHOULDER_STEP_MS in Arduino:

```
1. Python: Recognize voice input → "LEFT:SHOULDER1:UP:75" (5x amplified)
2. Arduino: Execute applyShoulderStep("LEFT", "SHOULDER1", "UP")
   - Power ON L_SH1_PWR
   - Set pulse width to L_SH1_UP (1700µs)
   - Wait 1000ms ← servo rotates UP for 1.0s (2x longer!)
   - Set pulse width to neutral (1370µs) → servo stops
   - Power OFF
3. Result: Shoulder rotates UP for 1.0 second = 2x distance
```

**Note:** The `amount=75` from Python is ignored, but that's OK because we achieve 2x through timing!

---

## Future Improvements

If we want `amount` to actually control movement intensity:

### Option 1: Scale Movement Duration Based on Amount
```cpp
unsigned long movement_time = SHOULDER_STEP_MS * (amount / 15.0);
delay(movement_time);
```

### Option 2: Scale Pulse Width Based on Amount
```cpp
int target_scaled = neutral + (target - neutral) * (amount / 100.0);
s->writeMicroseconds(clampUs(target_scaled));
```

Both would make the `amount` parameter meaningful instead of just ignoring it.

---

## Summary

| Aspect | Details |
|--------|---------|
| **Servo Type** | Continuous (shoulders), Positional (elbow, fingers) |
| **Control Method** | Pulse width (600-2400 µs) |
| **Shoulder Movement** | Set target pulse width, wait for duration, servo reaches that distance |
| **2x Amplification** | Double SHOULDER_STEP_MS from 500ms → 1000ms |
| **Why It Works** | Same speed × 2x time = 2x distance covered |
| **Amount Parameter** | Currently ignored for shoulders (could be improved) |
| **Current Behavior** | All shoulder movements use fixed 1000ms (after amplification) |
