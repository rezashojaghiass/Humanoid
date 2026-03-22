# Servo Configuration Quick Reference

## Shoulder Servo Calibration Values

### Left Arm

| Joint | Type | Down (µs) | Neutral (µs) | Up (µs) |
|-------|------|-----------|--------------|---------|
| Shoulder 1 | Continuous | 700 | 1370 | **1700** |
| Shoulder 2 | Continuous | 700 | 1500 | 2300 |

### Right Arm

| Joint | Type | Down (µs) | Neutral (µs) | Up (µs) |
|-------|------|-----------|--------------|---------|
| Shoulder 1 | Continuous | 1300 | 1460 | **1900** |
| Shoulder 2 | Continuous | 600 | 1460 | 2300 |

**Note:** The bolded values are used in the 2x amplified movement (SHOULDER_STEP_MS = 1000ms)

---

## Timing Constants

```
ARM_STEP_MS      = 500ms   (Elbow movements, normal arm operations)
SHOULDER_STEP_MS = 1000ms  (Shoulder movements - 2x for amplification)
```

**Movement Calculation:**
- Distance = Speed × Time
- 2x Distance requires: 2x Time (at constant speed)
- SHOULDER_STEP_MS = 2 × ARM_STEP_MS → 2x movement

---

## Continuous vs Positional Servos

### Continuous (Shoulders)
- **Behavior:** Rotates continuously in one direction
- **Pulse Control:** Width = direction & speed
  - 1500µs = Neutral (stopped)
  - > 1500µs = Rotate one way
  - < 1500µs = Rotate other way
- **Duration:** How long you apply the pulse = how far it rotates
- **Key:** More time = more rotation (at constant speed)

### Positional (Elbow, Fingers)
- **Behavior:** Moves to target position and holds
- **Pulse Control:** Width = target position
  - 880µs = Fully open
  - 1500µs = Fully closed
- **Duration:** Doesn't matter (servo stops at target)
- **Key:** Pulse width = final position

---

## Movement Command Format

**From Python to Arduino:**

```
side:joint:direction:amount
```

Examples:
- `LEFT:SHOULDER1:UP:15` - Left shoulder 1, up, normal amount
- `RIGHT:SHOULDER2:DOWN:75` - Right shoulder 2, down, amplified amount

**Arduino Processing:**
- Extracts side, joint, direction
- **Currently ignores `amount`** for shoulders
- Uses fixed timing: SHOULDER_STEP_MS = 1000ms

---

## Why "Some More" Works Now

1. **Python sends:** amount = 75 (5x amplification)
2. **Arduino receives:** amount parameter (ignored currently)
3. **Arduino does:** Wait for SHOULDER_STEP_MS = 1000ms
4. **Result:** Servo moves for 1000ms instead of 500ms = 2x distance
5. **User sees:** 2x movement amplification ✓

---

## How to Modify Behavior

### To Change 2x Amplification to 3x:
```cpp
// Line 434 in finger_servos.ino
const unsigned long SHOULDER_STEP_MS = 1500;  // 3x instead of 2x
```

### To Make "Amount" Actually Work:
Modify `applyShoulderStep()` to use amount parameter:
```cpp
unsigned long movement_time = (unsigned long)(SHOULDER_STEP_MS * (amount / 15.0));
delay(movement_time);  // Scales with amount
```

### To Add Smooth Movement Instead of Instant:
Use pulse width interpolation:
```cpp
int start = neutral;
int end = target;
for(int i = 0; i < 100; i++) {
  int current = start + (end - start) * i / 100;
  s->writeMicroseconds(current);
  delay(SHOULDER_STEP_MS / 100);  // Smooth over time
}
```

---

## Testing Tips

1. **Verify Calibration:**
   - Command: "Left shoulder one up"
   - Should rotate clearly in UP direction
   - If reversed, swap UP and DOWN values

2. **Verify 2x Amplification:**
   - Command: "Left shoulder one up"
   - Observe movement distance (baseline)
   - Command: "Some more"
   - Should see 2x the distance (not just 5% or 10% more)

3. **Check Servo Limits:**
   - UP values should be > 1500µs (toward max 2400µs)
   - DOWN values should be < 1500µs (toward min 600µs)
   - If servo stalls or makes noise, values are too extreme

---

## Files & Locations

- **Arduino Code:** `/home/reza/Humanoid/arduino/finger_servos/finger_servos.ino`
  - Lines 123-141: Calibration constants
  - Lines 433-434: Timing constants
  - Lines 751-809: `applyShoulderStep()` function

- **Python Control:** `/home/reza/Humanoid/robot_sync_app/src/robot_sync_app/application/voice_session_service.py`
  - Lines ~127: Movement intent detection
  - Lines ~190, ~360: 5x amplification for "some more"

- **Configuration:** `/home/reza/Humanoid/config.yaml`
  - `gesture.provider: arduino_serial` (enables servo control)
