#if 0
// ============================================================
// FINGER SERVO CONTROL - Arduino #1 (Official)
// ============================================================
// Upload Port: /dev/ttyACM0 (Linux) or COM3-4 (Windows)
// Board: Arduino Mega 2560 (Official FTDI)
// Function: Controls 10 finger servos (5 per hand) + arm servos
// Serial: 115200 baud for Python voice control
// ============================================================

#include <Servo.h>

// Tune these independently for better balance/control.

// LEFT arm timing (milliseconds)
// const unsigned long L_ARM_UP_MS    = 1800;
// const unsigned long L_ARM_PAUSE_MS = 180;
// const unsigned long L_ARM_DOWN_MS  = 2000;

// // RIGHT arm timing (milliseconds)
// const unsigned long R_ARM_UP_MS    = 1800;
// const unsigned long R_ARM_PAUSE_MS = 180;
// const unsigned long R_ARM_DOWN_MS  = 2000;

// LEFT arm timing (milliseconds)
const unsigned long L_ARM_UP_MS    = 2000;
const unsigned long L_ARM_PAUSE_MS = 180;
const unsigned long L_ARM_DOWN_MS  = 1570;

// RIGHT arm timing (milliseconds)
const unsigned long R_ARM_UP_MS    = 2000;
const unsigned long R_ARM_PAUSE_MS = 180;
const unsigned long R_ARM_DOWN_MS  = 1900;

// ============================================================
// ================== ENABLE FLAGS (PER MAIN SERVO) ==================
// Set false to completely ignore that servo (no attach, no power, no writes)
const bool EN_L_SH1 = true;
const bool EN_L_ELB = true;
const bool EN_L_SH2 = true;

const bool EN_R_SH1 = true;
const bool EN_R_ELB = true;
const bool EN_R_SH2 = true;


const int REPEAT_COUNT = 3;

// ================== SPEED FACTORS ==================
// For continuous servos: speed is distance from neutral.
// 1.00 = unchanged, >1.00 faster, <1.00 slower.
const float L_SH1_SPEED = 1.00f;
const float L_SH2_SPEED = 1.00f;

const float R_SH1_SPEED = 1.25f;   // <-- make RIGHT faster than LEFT
const float R_SH2_SPEED = 1.00f;

// Safe clamp for servo pulses
const int SERVO_MIN_US = 600;
const int SERVO_MAX_US = 2400;

// ===== RIGHT HAND =====
#define THUMB_PIN   2
#define INDEX_PIN   3
#define MIDDLE_PIN  4
#define RING_PIN    5
#define PINKY_PIN   6

// ===== LEFT HAND =====
#define LTHUMB_PIN   7
#define LINDEX_PIN   8
#define LMIDDLE_PIN  9
#define LRING_PIN    10
#define LPINKY_PIN   11

// ================== ARM PIN MAP (YOUR LATEST) ==================
// LEFT ARM (signals): D17, D24, D25   (powers): D33, D34, D35
#define L_SH1_PIN 17
#define L_SH1_PWR 33

#define L_ELB_PIN 24
#define L_ELB_PWR 34

#define L_SH2_PIN 25
#define L_SH2_PWR 35

// RIGHT ARM (signals): D14, D15, D16  (powers): D30, D31, D32
#define R_SH1_PIN 14
#define R_SH1_PWR 30

#define R_SH2_PIN 15
#define R_SH2_PWR 31

#define R_ELB_PIN 16
#define R_ELB_PWR 32
// ===============================================================

// ===== Servos =====
Servo sThumb, sIndex, sMiddle, sRing, sPinky;
Servo sLThumb, sLIndex, sLMiddle, sLRing, sLPinky;

Servo sLSh1, sLSh2, sLElb;
Servo sRSh1, sRSh2, sRElb;

// ===== RIGHT HAND CAL =====
const int THUMB_OPEN  = 1500, THUMB_CLOSE  = 2300;
const int INDEX_OPEN  = 2000, INDEX_CLOSE  = 700;
const int MIDDLE_OPEN = 2000, MIDDLE_CLOSE = 700;
const int RING_OPEN   = 2000, RING_CLOSE   = 700;
const int PINKY_OPEN  = 2000, PINKY_CLOSE  = 700;

// ===== LEFT HAND (mirrored) =====
const int LTHUMB_OPEN  = 1500, LTHUMB_CLOSE  = 740;
const int LINDEX_OPEN  = INDEX_CLOSE,  LINDEX_CLOSE  = INDEX_OPEN;
const int LMIDDLE_OPEN = MIDDLE_CLOSE, LMIDDLE_CLOSE = MIDDLE_OPEN;
const int LRING_OPEN   = RING_CLOSE,   LRING_CLOSE   = RING_OPEN;
const int LPINKY_OPEN  = PINKY_CLOSE,  LPINKY_CLOSE  = PINKY_OPEN;

// ================== ARM CAL VALUES ==================
// 
// SERVO TYPES:
// - Continuous servos (shoulders): Pulse width controls DIRECTION & SPEED
//   * 1500µs = neutral/stopped
//   * >1500µs = rotate one way (typically UP)
//   * <1500µs = rotate other way (typically DOWN)
//   * Distance = constant_speed × duration (more time = more rotation)
//
// - Positional servos (elbow): Pulse width controls TARGET POSITION
//   * Moves to target and holds
//   * Duration doesn't affect distance
//
// LEFT SHOULDER #1 (continuous rotation)
// Duration: SHOULDER_STEP_MS = 1000ms (gives 2x movement)
const int LSH1_DOWN    = 700;      // Low pulse → rotate DOWN
const int LSH1_NEUTRAL = 1370;     // Mid pulse → servo stopped/neutral
const int LSH1_UP      = 1700;     // High pulse → rotate UP (2x amplified)

// LEFT SHOULDER #2 (continuous)
const int LSH2_DOWN    = 700;
const int LSH2_NEUTRAL = 1500;   // TODO: replace with measured neutral
const int LSH2_UP      = 2300;

// LEFT ELBOW (positional)
const int LELB_OPEN    = 880;
const int LELB_CLOSE   = 1500;

// RIGHT SHOULDERS (continuous)
const int RSH1_DOWN    = 1300;
const int RSH1_NEUTRAL = 1460;
const int RSH1_UP      = 1900;

const int RSH2_DOWN    = 600;
const int RSH2_NEUTRAL = 1460;
const int RSH2_UP      = 2300;

// RIGHT ELBOW (positional)
const int RELB_OPEN    = 1200;
const int RELB_CLOSE   = 1800;
// ====================================================

// ===== TIMING (fingers wave) =====
const unsigned long PHASE_DELAY = 120;
const unsigned long HALF_MOVE   = 800;
const unsigned long UPDATE_MS   = 20;

// ===== STATE =====
unsigned long t0;
unsigned long lastUpdate = 0;
bool done = false;
int repeatsDone = 0;

// ===== Helpers =====
int clampUs(int us) {
  if (us < SERVO_MIN_US) return SERVO_MIN_US;
  if (us > SERVO_MAX_US) return SERVO_MAX_US;
  return us;
}

// For continuous servos: scale away/toward neutral.
// factor=1.0 -> unchanged. factor>1.0 -> faster, factor<1.0 -> slower.
int scaledPulse(int neutralUs, int targetUs, float factor) {
  float delta = (float)(targetUs - neutralUs);
  int out = (int)((float)neutralUs + delta * factor);
  return clampUs(out);
}

int lerpInt(int a, int b, float t) {
  return a + (int)((b - a) * t);
}

int wavePos(int openUs, int closeUs, long dt) {
  if (dt < 0) return openUs;

  if ((unsigned long)dt < HALF_MOVE) {
    return lerpInt(openUs, closeUs, (float)dt / (float)HALF_MOVE);
  }
  dt -= HALF_MOVE;

  if ((unsigned long)dt < HALF_MOVE) {
    return lerpInt(closeUs, openUs, (float)dt / (float)HALF_MOVE);
  }
  return openUs;
}

void powerOn(uint8_t pwrPin) {
  pinMode(pwrPin, OUTPUT);
  digitalWrite(pwrPin, HIGH);
  delay(250);
}

void powerOff(uint8_t pwrPin) {
  digitalWrite(pwrPin, LOW);
}

void setup() {
  // Fingers attach (kept as-is, you didn't ask to remove)
  sThumb.attach(THUMB_PIN);
  sIndex.attach(INDEX_PIN);
  sMiddle.attach(MIDDLE_PIN);
  sRing.attach(RING_PIN);
  sPinky.attach(PINKY_PIN);

  sLThumb.attach(LTHUMB_PIN);
  sLIndex.attach(LINDEX_PIN);
  sLMiddle.attach(LMIDDLE_PIN);
  sLRing.attach(LRING_PIN);
  sLPinky.attach(LPINKY_PIN);

  // Power pins default LOW first (safe) - ONLY for enabled servos
  if (EN_L_SH1) { pinMode(L_SH1_PWR, OUTPUT); digitalWrite(L_SH1_PWR, LOW); }
  if (EN_L_SH2) { pinMode(L_SH2_PWR, OUTPUT); digitalWrite(L_SH2_PWR, LOW); }
  if (EN_L_ELB) { pinMode(L_ELB_PWR, OUTPUT); digitalWrite(L_ELB_PWR, LOW); }

  if (EN_R_SH1) { pinMode(R_SH1_PWR, OUTPUT); digitalWrite(R_SH1_PWR, LOW); }
  if (EN_R_SH2) { pinMode(R_SH2_PWR, OUTPUT); digitalWrite(R_SH2_PWR, LOW); }
  if (EN_R_ELB) { pinMode(R_ELB_PWR, OUTPUT); digitalWrite(R_ELB_PWR, LOW); }

  // Attach arm servos + neutral/initial BEFORE power ON (only if enabled)
  if (EN_L_SH1) { sLSh1.attach(L_SH1_PIN); sLSh1.writeMicroseconds(LSH1_NEUTRAL); }
  if (EN_L_SH2) { sLSh2.attach(L_SH2_PIN); sLSh2.writeMicroseconds(LSH2_NEUTRAL); }
  if (EN_L_ELB) { sLElb.attach(L_ELB_PIN); sLElb.writeMicroseconds(LELB_OPEN); }

  if (EN_R_SH1) { sRSh1.attach(R_SH1_PIN); sRSh1.writeMicroseconds(RSH1_NEUTRAL); }
  if (EN_R_SH2) { sRSh2.attach(R_SH2_PIN); sRSh2.writeMicroseconds(RSH2_NEUTRAL); }
  if (EN_R_ELB) { sRElb.attach(R_ELB_PIN); sRElb.writeMicroseconds(RELB_OPEN); }

  delay(200);

  // Power ON (only if enabled)
  if (EN_L_SH1) powerOn(L_SH1_PWR);
  if (EN_L_SH2) powerOn(L_SH2_PWR);
  if (EN_L_ELB) powerOn(L_ELB_PWR);

  if (EN_R_SH1) powerOn(R_SH1_PWR);
  if (EN_R_SH2) powerOn(R_SH2_PWR);
  if (EN_R_ELB) powerOn(R_ELB_PWR);

  t0 = millis();
}

void loop() {
  if (done) return;

  unsigned long now = millis();
  if (now - lastUpdate < UPDATE_MS) return;
  lastUpdate = now;

  // Mexican wave timing offsets (10 fingers)
  long dt[10];
  for (int i = 0; i < 10; i++) dt[i] = (long)(now - (t0 + (unsigned long)i * PHASE_DELAY));

  // Fingers wave
  sThumb.writeMicroseconds(  wavePos(THUMB_OPEN,  THUMB_CLOSE,  dt[0]) );
  sIndex.writeMicroseconds(  wavePos(INDEX_OPEN,  INDEX_CLOSE,  dt[1]) );
  sMiddle.writeMicroseconds( wavePos(MIDDLE_OPEN, MIDDLE_CLOSE, dt[2]) );
  sRing.writeMicroseconds(   wavePos(RING_OPEN,   RING_CLOSE,   dt[3]) );
  sPinky.writeMicroseconds(  wavePos(PINKY_OPEN,  PINKY_CLOSE,  dt[4]) );

  sLThumb.writeMicroseconds(  wavePos(LTHUMB_OPEN,  LTHUMB_CLOSE,  dt[5]) );
  sLIndex.writeMicroseconds(  wavePos(LINDEX_OPEN,  LINDEX_CLOSE,  dt[6]) );
  sLMiddle.writeMicroseconds( wavePos(LMIDDLE_OPEN, LMIDDLE_CLOSE, dt[7]) );
  sLRing.writeMicroseconds(   wavePos(LRING_OPEN,   LRING_CLOSE,   dt[8]) );
  sLPinky.writeMicroseconds(  wavePos(LPINKY_OPEN,  LPINKY_CLOSE,  dt[9]) );

  // Decoupled ARM timing
  unsigned long t = now - t0;

  // LEFT timeline
  unsigned long L_UP_END    = L_ARM_UP_MS;
  unsigned long L_PAUSE_END = L_UP_END + L_ARM_PAUSE_MS;
  unsigned long L_DOWN_END  = L_PAUSE_END + L_ARM_DOWN_MS;

  // RIGHT timeline
  unsigned long R_UP_END    = R_ARM_UP_MS;
  unsigned long R_PAUSE_END = R_UP_END + R_ARM_PAUSE_MS;
  unsigned long R_DOWN_END  = R_PAUSE_END + R_ARM_DOWN_MS;

  // Round complete when BOTH arms done
  unsigned long ROUND_TOTAL = (L_DOWN_END > R_DOWN_END) ? L_DOWN_END : R_DOWN_END;

  // Precompute scaled pulses for continuous shoulders
  const int LSH1_UP_S   = scaledPulse(LSH1_NEUTRAL, LSH1_UP,   L_SH1_SPEED);
  const int LSH1_DOWN_S = scaledPulse(LSH1_NEUTRAL, LSH1_DOWN, L_SH1_SPEED);

  const int LSH2_UP_S   = scaledPulse(LSH2_NEUTRAL, LSH2_UP,   L_SH2_SPEED);
  const int LSH2_DOWN_S = scaledPulse(LSH2_NEUTRAL, LSH2_DOWN, L_SH2_SPEED);

  const int RSH1_UP_S   = scaledPulse(RSH1_NEUTRAL, RSH1_UP,   R_SH1_SPEED);
  const int RSH1_DOWN_S = scaledPulse(RSH1_NEUTRAL, RSH1_DOWN, R_SH1_SPEED);

  const int RSH2_UP_S   = scaledPulse(RSH2_NEUTRAL, RSH2_UP,   R_SH2_SPEED);
  const int RSH2_DOWN_S = scaledPulse(RSH2_NEUTRAL, RSH2_DOWN, R_SH2_SPEED);

  // ========== LEFT ARM ==========
  if (t < L_UP_END) {
    if (EN_L_SH1) sLSh1.writeMicroseconds(LSH1_UP_S);
    if (EN_L_SH2) sLSh2.writeMicroseconds(LSH2_UP_S);
    if (EN_L_ELB) sLElb.writeMicroseconds(LELB_OPEN);

  } else if (t < L_PAUSE_END) {
    if (EN_L_SH1) sLSh1.writeMicroseconds(LSH1_NEUTRAL);
    if (EN_L_SH2) sLSh2.writeMicroseconds(LSH2_NEUTRAL);
    if (EN_L_ELB) sLElb.writeMicroseconds(LELB_CLOSE);

  } else if (t < L_DOWN_END) {
    float prog = (float)(t - L_PAUSE_END) / (float)(L_ARM_DOWN_MS);
    int sh1_out = lerpInt(LSH1_NEUTRAL, LSH1_DOWN_S, prog);
    int sh2_out = lerpInt(LSH2_NEUTRAL, LSH2_DOWN_S, prog);
    if (EN_L_SH1) sLSh1.writeMicroseconds(sh1_out);
    if (EN_L_SH2) sLSh2.writeMicroseconds(sh2_out);
    if (EN_L_ELB) sLElb.writeMicroseconds(LELB_CLOSE);

  } else {
    if (EN_L_SH1) sLSh1.writeMicroseconds(LSH1_NEUTRAL);
    if (EN_L_SH2) sLSh2.writeMicroseconds(LSH2_NEUTRAL);
    if (EN_L_ELB) sLElb.writeMicroseconds(LELB_OPEN);
  }

  // ========== RIGHT ARM ==========
  if (t < R_UP_END) {
    if (EN_R_SH1) sRSh1.writeMicroseconds(RSH1_UP_S);
    if (EN_R_SH2) sRSh2.writeMicroseconds(RSH2_UP_S);
    if (EN_R_ELB) sRElb.writeMicroseconds(RELB_OPEN);

  } else if (t < R_PAUSE_END) {
    if (EN_R_SH1) sRSh1.writeMicroseconds(RSH1_NEUTRAL);
    if (EN_R_SH2) sRSh2.writeMicroseconds(RSH2_NEUTRAL);
    if (EN_R_ELB) sRElb.writeMicroseconds(RELB_CLOSE);

  } else if (t < R_DOWN_END) {
    float prog = (float)(t - R_PAUSE_END) / (float)(R_ARM_DOWN_MS);
    int sh1_out = lerpInt(RSH1_NEUTRAL, RSH1_DOWN_S, prog);
    int sh2_out = lerpInt(RSH2_NEUTRAL, RSH2_DOWN_S, prog);
    if (EN_R_SH1) sRSh1.writeMicroseconds(sh1_out);
    if (EN_R_SH2) sRSh2.writeMicroseconds(sh2_out);
    if (EN_R_ELB) sRElb.writeMicroseconds(RELB_CLOSE);

  } else {
    if (EN_R_SH1) sRSh1.writeMicroseconds(RSH1_NEUTRAL);
    if (EN_R_SH2) sRSh2.writeMicroseconds(RSH2_NEUTRAL);
    if (EN_R_ELB) sRElb.writeMicroseconds(RELB_OPEN);
  }

  // ========== DONE CHECK ==========
  if (t >= ROUND_TOTAL) {
    repeatsDone++;
    if (repeatsDone >= REPEAT_COUNT) {
      done = true;
    } else {
      t0 = now;
    }
  }
}
#endif

#include <Servo.h>

// ===================== Finger pins =====================
#define THUMB_PIN   2
#define INDEX_PIN   3
#define MIDDLE_PIN  4
#define RING_PIN    5
#define PINKY_PIN   6

#define LTHUMB_PIN   7
#define LINDEX_PIN   8
#define LMIDDLE_PIN  9
#define LRING_PIN    10
#define LPINKY_PIN   11

// ===================== Arm pins =====================
#define L_SH1_PIN 17
#define L_ELB_PIN 24
#define L_SH2_PIN 25
#define L_SH1_PWR 33
#define L_ELB_PWR 34
#define L_SH2_PWR 35

#define R_SH1_PIN 14
#define R_SH2_PIN 15
#define R_ELB_PIN 16
#define R_SH1_PWR 30
#define R_SH2_PWR 31
#define R_ELB_PWR 32

Servo sThumb, sIndex, sMiddle, sRing, sPinky;
Servo sLThumb, sLIndex, sLMiddle, sLRing, sLPinky;
Servo sLSh1, sLSh2, sLElb;
Servo sRSh1, sRSh2, sRElb;

const int THUMB_OPEN  = 1500, THUMB_CLOSE  = 2300;
const int INDEX_OPEN  = 2000, INDEX_CLOSE  = 700;
const int MIDDLE_OPEN = 2000, MIDDLE_CLOSE = 700;
const int RING_OPEN   = 2000, RING_CLOSE   = 700;
const int PINKY_OPEN  = 2000, PINKY_CLOSE  = 700;

const int LTHUMB_OPEN  = 1500, LTHUMB_CLOSE  = 740;
const int LINDEX_OPEN  = INDEX_CLOSE,  LINDEX_CLOSE  = INDEX_OPEN;
const int LMIDDLE_OPEN = MIDDLE_CLOSE, LMIDDLE_CLOSE = MIDDLE_OPEN;
const int LRING_OPEN   = RING_CLOSE,   LRING_CLOSE   = RING_OPEN;
const int LPINKY_OPEN  = PINKY_CLOSE,  LPINKY_CLOSE  = PINKY_OPEN;

const int L_ELB_OPEN_US = 880;
const int L_ELB_BEND_US = 1500;
const int R_ELB_OPEN_US = 1200;
const int R_ELB_BEND_US = 1800;

const int L_SH1_DOWN_US = 700;
const int L_SH1_NEUTRAL_US = 1370;
const int L_SH1_UP_US = 1700;

const int L_SH2_DOWN_US = 700;
const int L_SH2_NEUTRAL_US = 1500;
const int L_SH2_UP_US = 2300;

const int R_SH1_DOWN_US = 1300;
const int R_SH1_NEUTRAL_US = 1460;
const int R_SH1_UP_US = 1900;

const int R_SH2_DOWN_US = 600;
const int R_SH2_NEUTRAL_US = 1460;
const int R_SH2_UP_US = 2300;

const int SERVO_MIN_US = 600;
const int SERVO_MAX_US = 2400;
// ================== SERVO MOVEMENT TIMING ==================
// ARM_STEP_MS: Normal movement duration for elbow/arm servos (500ms)
// SHOULDER_STEP_MS: Duration for shoulder movements (1000ms = 2x normal)
// 
// HOW IT WORKS:
// - Continuous servos (shoulders) move toward a target pulse width at constant speed
// - Duration = how long the servo moves = how far it travels
// - 2x duration = 2x distance traveled (same speed, more time)
// - SHOULDER_STEP_MS = 1000ms gives 2x movement amplification
// 
// EXAMPLE:
// - Command: Set shoulder to UP (1700µs), wait 500ms → rotates 50% of max
// - Command: Set shoulder to UP (1700µs), wait 1000ms → rotates 100% of max (2x)
// ============================================================
const unsigned long ARM_STEP_MS = 500;
const unsigned long SHOULDER_STEP_MS = 1000;  // 2x movement amplification

bool talkOn = false;
unsigned long talkCycleStartMs = 0;
unsigned long talkLastUpdateMs = 0;

// Feb10 motion profile (arms only)
const unsigned long TALK_L_ARM_UP_MS = 2000;
const unsigned long TALK_L_ARM_PAUSE_MS = 180;
const unsigned long TALK_L_ARM_DOWN_MS = 1570;

const unsigned long TALK_R_ARM_UP_MS = 2000;
const unsigned long TALK_R_ARM_PAUSE_MS = 180;
const unsigned long TALK_R_ARM_DOWN_MS = 1900;

const float TALK_L_SH1_SPEED = 1.00f;
const float TALK_L_SH2_SPEED = 1.00f;
const float TALK_R_SH1_SPEED = 1.25f;
const float TALK_R_SH2_SPEED = 1.00f;

const unsigned long TALK_UPDATE_MS = 20;

int currentLElbUs = (L_ELB_OPEN_US + L_ELB_BEND_US) / 2;
int currentRElbUs = (R_ELB_OPEN_US + R_ELB_BEND_US) / 2;
int currentLSh2Us = L_SH2_NEUTRAL_US;
int currentRSh2Us = R_SH2_NEUTRAL_US;

String tokenAt(const String &src, char delim, int idx);

int clampUs(int us) {
  if (us < SERVO_MIN_US) return SERVO_MIN_US;
  if (us > SERVO_MAX_US) return SERVO_MAX_US;
  return us;
}

int scaledPulse(int neutralUs, int targetUs, float factor) {
  float delta = (float)(targetUs - neutralUs);
  int out = (int)((float)neutralUs + delta * factor);
  return clampUs(out);
}

int mixUs(int openUs, int closeUs, float ratio) {
  return clampUs((int)(openUs + (closeUs - openUs) * ratio));
}

void powerOn(uint8_t pwrPin) {
  pinMode(pwrPin, OUTPUT);
  digitalWrite(pwrPin, HIGH);
  delay(120);
}

void powerOff(uint8_t pwrPin) {
  digitalWrite(pwrPin, LOW);
}

void setFingersOpen() {
  // Right hand
  sThumb.writeMicroseconds(THUMB_OPEN);
  sIndex.writeMicroseconds(INDEX_OPEN);
  sMiddle.writeMicroseconds(MIDDLE_OPEN);
  sRing.writeMicroseconds(RING_OPEN);
  sPinky.writeMicroseconds(PINKY_OPEN);
  // Left hand
  sLThumb.writeMicroseconds(LTHUMB_OPEN);
  sLIndex.writeMicroseconds(LINDEX_OPEN);
  sLMiddle.writeMicroseconds(LMIDDLE_OPEN);
  sLRing.writeMicroseconds(LRING_OPEN);
  sLPinky.writeMicroseconds(LPINKY_OPEN);
}

void setRightFingersOpen() {
  sThumb.writeMicroseconds(THUMB_OPEN);
  sIndex.writeMicroseconds(INDEX_OPEN);
  sMiddle.writeMicroseconds(MIDDLE_OPEN);
  sRing.writeMicroseconds(RING_OPEN);
  sPinky.writeMicroseconds(PINKY_OPEN);
}

void setLeftFingersOpen() {
  sLThumb.writeMicroseconds(LTHUMB_OPEN);
  sLIndex.writeMicroseconds(LINDEX_OPEN);
  sLMiddle.writeMicroseconds(LMIDDLE_OPEN);
  sLRing.writeMicroseconds(LRING_OPEN);
  sLPinky.writeMicroseconds(LPINKY_OPEN);
}

void setFingersClose() {
  // Right hand
  sThumb.writeMicroseconds(THUMB_CLOSE);
  sIndex.writeMicroseconds(INDEX_CLOSE);
  sMiddle.writeMicroseconds(MIDDLE_CLOSE);
  sRing.writeMicroseconds(RING_CLOSE);
  sPinky.writeMicroseconds(PINKY_CLOSE);
  // Left hand
  sLThumb.writeMicroseconds(LTHUMB_CLOSE);
  sLIndex.writeMicroseconds(LINDEX_CLOSE);
  sLMiddle.writeMicroseconds(LMIDDLE_CLOSE);
  sLRing.writeMicroseconds(LRING_CLOSE);
  sLPinky.writeMicroseconds(LPINKY_CLOSE);
}

void setRightFingersClose() {
  sThumb.writeMicroseconds(THUMB_CLOSE);
  sIndex.writeMicroseconds(INDEX_CLOSE);
  sMiddle.writeMicroseconds(MIDDLE_CLOSE);
  sRing.writeMicroseconds(RING_CLOSE);
  sPinky.writeMicroseconds(PINKY_CLOSE);
}

void setLeftFingersClose() {
  sLThumb.writeMicroseconds(LTHUMB_CLOSE);
  sLIndex.writeMicroseconds(LINDEX_CLOSE);
  sLMiddle.writeMicroseconds(LMIDDLE_CLOSE);
  sLRing.writeMicroseconds(LRING_CLOSE);
  sLPinky.writeMicroseconds(LPINKY_CLOSE);
}

// Helper function for smooth servo movement (like Feb10 code)
int lerpInt(int a, int b, float t) {
  return a + (int)((b - a) * t);
}

// Wave position function from Feb10 - calculates servo position based on elapsed time
// First 800ms: smooth close (OPEN -> CLOSE)
// Next 800ms: smooth open (CLOSE -> OPEN)
int wavePos(int openUs, int closeUs, long dt) {
  if (dt < 0) return openUs;
  
  const unsigned long HALF_MOVE = 800; // 800ms to close or open
  
  if ((unsigned long)dt < HALF_MOVE) {
    // Closing phase: lerp from open to close
    return lerpInt(openUs, closeUs, (float)dt / (float)HALF_MOVE);
  }
  dt -= HALF_MOVE;
  
  if ((unsigned long)dt < HALF_MOVE) {
    // Opening phase: lerp from close to open
    return lerpInt(closeUs, openUs, (float)dt / (float)HALF_MOVE);
  }
  return openUs;
}

// Sequential finger closing with Feb10 wave pattern
// Each finger starts 120ms after the previous one
// Each finger closes over 800ms, then opens over 800ms
void setFingersCloseSequential() {
  const unsigned long PHASE_DELAY = 120;  // 120ms between finger starts
  const unsigned long HALF_MOVE = 800;     // 800ms to close or open
  const unsigned long UPDATE_MS = 20;      // Update every 20ms
  unsigned long t0 = millis();             // Animation start time
  // Total duration: (9 * PHASE_DELAY) because 10th finger starts at 9*120ms, then needs 2*HALF_MOVE to close and open
  unsigned long totalDuration = (9 * PHASE_DELAY) + (2 * HALF_MOVE); // ~2680ms
  unsigned long lastUpdate = 0;
  
  while (millis() - t0 < totalDuration) {
    unsigned long now = millis();
    
    // Only update every UPDATE_MS
    if (now - lastUpdate < UPDATE_MS) continue;
    lastUpdate = now;
    
    // Calculate elapsed time for each finger (staggered start times)
    long dt[10];
    for (int i = 0; i < 10; i++) {
      dt[i] = (long)(now - (t0 + (unsigned long)i * PHASE_DELAY));
    }
    
    // Update all 10 finger positions
    sThumb.writeMicroseconds(  wavePos(THUMB_OPEN,  THUMB_CLOSE,  dt[0]) );
    sIndex.writeMicroseconds(  wavePos(INDEX_OPEN,  INDEX_CLOSE,  dt[1]) );
    sMiddle.writeMicroseconds( wavePos(MIDDLE_OPEN, MIDDLE_CLOSE, dt[2]) );
    sRing.writeMicroseconds(   wavePos(RING_OPEN,   RING_CLOSE,   dt[3]) );
    sPinky.writeMicroseconds(  wavePos(PINKY_OPEN,  PINKY_CLOSE,  dt[4]) );
    
    sLThumb.writeMicroseconds(  wavePos(LTHUMB_OPEN,  LTHUMB_CLOSE,  dt[5]) );
    sLIndex.writeMicroseconds(  wavePos(LINDEX_OPEN,  LINDEX_CLOSE,  dt[6]) );
    sLMiddle.writeMicroseconds( wavePos(LMIDDLE_OPEN, LMIDDLE_CLOSE, dt[7]) );
    sLRing.writeMicroseconds(   wavePos(LRING_OPEN,   LRING_CLOSE,   dt[8]) );
    sLPinky.writeMicroseconds(  wavePos(LPINKY_OPEN,  LPINKY_CLOSE,  dt[9]) );
  }
  
  // Ensure all fingers end in open position
  setFingersOpen();
}

// Sequential finger closing with right elbow movement (Mexican wave style)
void setFingersCloseSequentialWithArms() {
  const unsigned long PHASE_DELAY = 120;
  const unsigned long HALF_MOVE = 800;
  const unsigned long UPDATE_MS = 20;
  unsigned long t0 = millis();
  unsigned long totalDuration = (9 * PHASE_DELAY) + (2 * HALF_MOVE);
  unsigned long lastUpdate = 0;
  
  // Attach right elbow if not attached
  if (!sRElb.attached()) {
    powerOn(R_ELB_PWR);
    sRElb.attach(R_ELB_PIN);
  }
  
  while (millis() - t0 < totalDuration) {
    unsigned long now = millis();
    unsigned long elapsed = now - t0;
    
    if (now - lastUpdate < UPDATE_MS) continue;
    lastUpdate = now;
    
    // ========== FINGER WAVE ==========
    long dt[10];
    for (int i = 0; i < 10; i++) {
      dt[i] = (long)(now - (t0 + (unsigned long)i * PHASE_DELAY));
    }
    
    sThumb.writeMicroseconds(  wavePos(THUMB_OPEN,  THUMB_CLOSE,  dt[0]) );
    sIndex.writeMicroseconds(  wavePos(INDEX_OPEN,  INDEX_CLOSE,  dt[1]) );
    sMiddle.writeMicroseconds( wavePos(MIDDLE_OPEN, MIDDLE_CLOSE, dt[2]) );
    sRing.writeMicroseconds(   wavePos(RING_OPEN,   RING_CLOSE,   dt[3]) );
    sPinky.writeMicroseconds(  wavePos(PINKY_OPEN,  PINKY_CLOSE,  dt[4]) );
    
    sLThumb.writeMicroseconds(  wavePos(LTHUMB_OPEN,  LTHUMB_CLOSE,  dt[5]) );
    sLIndex.writeMicroseconds(  wavePos(LINDEX_OPEN,  LINDEX_CLOSE,  dt[6]) );
    sLMiddle.writeMicroseconds( wavePos(LMIDDLE_OPEN, LMIDDLE_CLOSE, dt[7]) );
    sLRing.writeMicroseconds(   wavePos(LRING_OPEN,   LRING_CLOSE,   dt[8]) );
    sLPinky.writeMicroseconds(  wavePos(LPINKY_OPEN,  LPINKY_CLOSE,  dt[9]) );
    
    // ========== RIGHT ELBOW ==========
    // Open at start, close in middle, open at end (same as fingers)
    if (elapsed < HALF_MOVE) {
      // First half: closing phase - elbow closes
      sRElb.writeMicroseconds(1800);  // RELB_CLOSE
    } else {
      // Second half: opening phase - elbow opens
      sRElb.writeMicroseconds(1200);  // RELB_OPEN
    }
  }
  
  // Return to neutral positions
  setFingersOpen();
  sRElb.writeMicroseconds(1200);  // RELB_OPEN
}

void setRightFingersCloseSequential() {
  const unsigned long PHASE_DELAY = 120;
  const unsigned long HALF_MOVE = 800;
  const unsigned long UPDATE_MS = 20;
  unsigned long t0 = millis();
  // Total duration: (4 * PHASE_DELAY) because 5th finger starts at 4*120ms, then needs 2*HALF_MOVE to close and open
  unsigned long totalDuration = (4 * PHASE_DELAY) + (2 * HALF_MOVE); // ~1920ms
  unsigned long lastUpdate = 0;
  
  while (millis() - t0 < totalDuration) {
    unsigned long now = millis();
    
    if (now - lastUpdate < UPDATE_MS) continue;
    lastUpdate = now;
    
    long dt[5];
    for (int i = 0; i < 5; i++) {
      dt[i] = (long)(now - (t0 + (unsigned long)i * PHASE_DELAY));
    }
    
    sThumb.writeMicroseconds(  wavePos(THUMB_OPEN,  THUMB_CLOSE,  dt[0]) );
    sIndex.writeMicroseconds(  wavePos(INDEX_OPEN,  INDEX_CLOSE,  dt[1]) );
    sMiddle.writeMicroseconds( wavePos(MIDDLE_OPEN, MIDDLE_CLOSE, dt[2]) );
    sRing.writeMicroseconds(   wavePos(RING_OPEN,   RING_CLOSE,   dt[3]) );
    sPinky.writeMicroseconds(  wavePos(PINKY_OPEN,  PINKY_CLOSE,  dt[4]) );
  }
  
  setRightFingersOpen();
}

void setLeftFingersCloseSequential() {
  const unsigned long PHASE_DELAY = 120;
  const unsigned long HALF_MOVE = 800;
  const unsigned long UPDATE_MS = 20;
  unsigned long t0 = millis();
  // Total duration: (4 * PHASE_DELAY) because 5th finger starts at 4*120ms, then needs 2*HALF_MOVE to close and open
  unsigned long totalDuration = (4 * PHASE_DELAY) + (2 * HALF_MOVE); // ~1920ms
  unsigned long lastUpdate = 0;
  
  while (millis() - t0 < totalDuration) {
    unsigned long now = millis();
    
    if (now - lastUpdate < UPDATE_MS) continue;
    lastUpdate = now;
    
    long dt[5];
    for (int i = 0; i < 5; i++) {
      dt[i] = (long)(now - (t0 + (unsigned long)i * PHASE_DELAY));
    }
    
    sLThumb.writeMicroseconds(  wavePos(LTHUMB_OPEN,  LTHUMB_CLOSE,  dt[0]) );
    sLIndex.writeMicroseconds(  wavePos(LINDEX_OPEN,  LINDEX_CLOSE,  dt[1]) );
    sLMiddle.writeMicroseconds( wavePos(LMIDDLE_OPEN, LMIDDLE_CLOSE, dt[2]) );
    sLRing.writeMicroseconds(   wavePos(LRING_OPEN,   LRING_CLOSE,   dt[3]) );
    sLPinky.writeMicroseconds(  wavePos(LPINKY_OPEN,  LPINKY_CLOSE,  dt[4]) );
  }
  
  setLeftFingersOpen();
}

void processFingerCmd(const String &line) {
  String action = tokenAt(line, ':', 1);
  String side = tokenAt(line, ':', 2);
  action.trim(); side.trim();
  action.toUpperCase(); side.toUpperCase();
  if (side.length() == 0) side = "BOTH";

  bool doRight = (side == "RIGHT" || side == "BOTH");
  bool doLeft  = (side == "LEFT"  || side == "BOTH");
  if (!doRight && !doLeft) {
    Serial.println("ERR:FINGER:BAD_SIDE");
    return;
  }

  if (action == "OPEN") {
    if (doRight) setRightFingersOpen();
    if (doLeft) setLeftFingersOpen();
    Serial.println("ACK:FINGER:OPEN");
    return;
  }

  if (action == "CLOSE") {
    if (doRight) setRightFingersClose();
    if (doLeft) setLeftFingersClose();
    Serial.println("ACK:FINGER:CLOSE");
    return;
  }

  if (action == "CLOSE_SEQ") {
    if (doRight && doLeft) {
      // Both hands: use the unified sequential function for continuous timeline
      setFingersCloseSequential();
    } else if (doRight) {
      setRightFingersCloseSequential();
    } else if (doLeft) {
      setLeftFingersCloseSequential();
    }
    Serial.println("ACK:FINGER:CLOSE_SEQ");
    return;
  }

  if (action == "CLOSE_SEQ_ARMS") {
    // Mexican wave with arm movement (only for BOTH hands)
    if (doRight && doLeft) {
      setFingersCloseSequentialWithArms();
    } else {
      // Fall back to sequential fingers if not both hands
      if (doRight) {
        setRightFingersCloseSequential();
      } else if (doLeft) {
        setLeftFingersCloseSequential();
      }
    }
    Serial.println("ACK:FINGER:CLOSE_SEQ_ARMS");
    return;
  }

  if (action == "WAVE") {
    if (doRight) setRightFingersClose();
    if (doLeft) setLeftFingersClose();
    delay(220);
    if (doRight) setRightFingersOpen();
    if (doLeft) setLeftFingersOpen();
    Serial.println("ACK:FINGER:WAVE");
    return;
  }

  Serial.println("ERR:FINGER:BAD_ACTION");
}

void neutralShouldersAndDetach() {
  powerOn(L_SH1_PWR); sLSh1.attach(L_SH1_PIN); sLSh1.writeMicroseconds(L_SH1_NEUTRAL_US);
  powerOn(L_SH2_PWR); sLSh2.attach(L_SH2_PIN); sLSh2.writeMicroseconds(L_SH2_NEUTRAL_US);
  powerOn(R_SH1_PWR); sRSh1.attach(R_SH1_PIN); sRSh1.writeMicroseconds(R_SH1_NEUTRAL_US);
  powerOn(R_SH2_PWR); sRSh2.attach(R_SH2_PIN); sRSh2.writeMicroseconds(R_SH2_NEUTRAL_US);
  delay(120);
  sLSh1.detach(); sLSh2.detach(); sRSh1.detach(); sRSh2.detach();
  powerOff(L_SH1_PWR); powerOff(L_SH2_PWR); powerOff(R_SH1_PWR); powerOff(R_SH2_PWR);
}

void setElbowsToCurrentAndDetach() {
  powerOn(L_ELB_PWR); sLElb.attach(L_ELB_PIN); sLElb.writeMicroseconds(clampUs(currentLElbUs));
  powerOn(R_ELB_PWR); sRElb.attach(R_ELB_PIN); sRElb.writeMicroseconds(clampUs(currentRElbUs));
  delay(120);
  sLElb.detach(); sRElb.detach();
  powerOff(L_ELB_PWR); powerOff(R_ELB_PWR);
}

void startTalkingMotion() {
  talkOn = true;
  talkCycleStartMs = millis();
  talkLastUpdateMs = 0;
  powerOn(L_ELB_PWR); sLElb.attach(L_ELB_PIN);
  powerOn(R_ELB_PWR); sRElb.attach(R_ELB_PIN);
  powerOn(L_SH1_PWR); sLSh1.attach(L_SH1_PIN);
  powerOn(R_SH1_PWR); sRSh1.attach(R_SH1_PIN);
  powerOn(L_SH2_PWR); sLSh2.attach(L_SH2_PIN);
  powerOn(R_SH2_PWR); sRSh2.attach(R_SH2_PIN);

  sLSh1.writeMicroseconds(clampUs(L_SH1_NEUTRAL_US));
  sRSh1.writeMicroseconds(clampUs(R_SH1_NEUTRAL_US));
  sLSh2.writeMicroseconds(clampUs(L_SH2_NEUTRAL_US));
  sRSh2.writeMicroseconds(clampUs(R_SH2_NEUTRAL_US));
  sLElb.writeMicroseconds(clampUs(L_ELB_OPEN_US));
  sRElb.writeMicroseconds(clampUs(R_ELB_OPEN_US));
}

void stopTalkingMotion() {
  talkOn = false;
  sLElb.writeMicroseconds(clampUs(currentLElbUs));
  sRElb.writeMicroseconds(clampUs(currentRElbUs));
  sLSh1.writeMicroseconds(clampUs(L_SH1_NEUTRAL_US));
  sRSh1.writeMicroseconds(clampUs(R_SH1_NEUTRAL_US));
  sLSh2.writeMicroseconds(clampUs(L_SH2_NEUTRAL_US));
  sRSh2.writeMicroseconds(clampUs(R_SH2_NEUTRAL_US));
  delay(80);
  sLElb.detach(); sRElb.detach(); sLSh1.detach(); sRSh1.detach(); sLSh2.detach(); sRSh2.detach();
  powerOff(L_ELB_PWR); powerOff(R_ELB_PWR); powerOff(L_SH1_PWR); powerOff(R_SH1_PWR); powerOff(L_SH2_PWR); powerOff(R_SH2_PWR);
}

void updateTalkingMotion() {
  if (!talkOn) return;
  unsigned long now = millis();
  if (now - talkLastUpdateMs < TALK_UPDATE_MS) return;
  talkLastUpdateMs = now;

  unsigned long t = now - talkCycleStartMs;

  const unsigned long L_UP_END = TALK_L_ARM_UP_MS;
  const unsigned long L_PAUSE_END = L_UP_END + TALK_L_ARM_PAUSE_MS;
  const unsigned long L_DOWN_END = L_PAUSE_END + TALK_L_ARM_DOWN_MS;

  const unsigned long R_UP_END = TALK_R_ARM_UP_MS;
  const unsigned long R_PAUSE_END = R_UP_END + TALK_R_ARM_PAUSE_MS;
  const unsigned long R_DOWN_END = R_PAUSE_END + TALK_R_ARM_DOWN_MS;

  const unsigned long ROUND_TOTAL = (L_DOWN_END > R_DOWN_END) ? L_DOWN_END : R_DOWN_END;

  const int LSH1_UP_S = scaledPulse(L_SH1_NEUTRAL_US, L_SH1_UP_US, TALK_L_SH1_SPEED);
  const int LSH1_DOWN_S = scaledPulse(L_SH1_NEUTRAL_US, L_SH1_DOWN_US, TALK_L_SH1_SPEED);
  const int LSH2_UP_S = scaledPulse(L_SH2_NEUTRAL_US, L_SH2_UP_US, TALK_L_SH2_SPEED);
  const int LSH2_DOWN_S = scaledPulse(L_SH2_NEUTRAL_US, L_SH2_DOWN_US, TALK_L_SH2_SPEED);

  const int RSH1_UP_S = scaledPulse(R_SH1_NEUTRAL_US, R_SH1_UP_US, TALK_R_SH1_SPEED);
  const int RSH1_DOWN_S = scaledPulse(R_SH1_NEUTRAL_US, R_SH1_DOWN_US, TALK_R_SH1_SPEED);
  const int RSH2_UP_S = scaledPulse(R_SH2_NEUTRAL_US, R_SH2_UP_US, TALK_R_SH2_SPEED);
  const int RSH2_DOWN_S = scaledPulse(R_SH2_NEUTRAL_US, R_SH2_DOWN_US, TALK_R_SH2_SPEED);

  if (t < L_UP_END) {
    sLSh1.writeMicroseconds(LSH1_UP_S);
    sLSh2.writeMicroseconds(LSH2_UP_S);
    sLElb.writeMicroseconds(L_ELB_OPEN_US);
  } else if (t < L_PAUSE_END) {
    sLSh1.writeMicroseconds(L_SH1_NEUTRAL_US);
    sLSh2.writeMicroseconds(L_SH2_NEUTRAL_US);
    sLElb.writeMicroseconds(L_ELB_OPEN_US);
  } else if (t < L_DOWN_END) {
    sLSh1.writeMicroseconds(LSH1_DOWN_S);
    sLSh2.writeMicroseconds(LSH2_DOWN_S);
    sLElb.writeMicroseconds(L_ELB_BEND_US);
  } else {
    sLSh1.writeMicroseconds(L_SH1_NEUTRAL_US);
    sLSh2.writeMicroseconds(L_SH2_NEUTRAL_US);
  }

  if (t < R_UP_END) {
    sRSh1.writeMicroseconds(RSH1_UP_S);
    sRSh2.writeMicroseconds(RSH2_UP_S);
    sRElb.writeMicroseconds(R_ELB_OPEN_US);
  } else if (t < R_PAUSE_END) {
    sRSh1.writeMicroseconds(R_SH1_NEUTRAL_US);
    sRSh2.writeMicroseconds(R_SH2_NEUTRAL_US);
    sRElb.writeMicroseconds(R_ELB_OPEN_US);
  } else if (t < R_DOWN_END) {
    sRSh1.writeMicroseconds(RSH1_DOWN_S);
    sRSh2.writeMicroseconds(RSH2_DOWN_S);
    sRElb.writeMicroseconds(R_ELB_BEND_US);
  } else {
    sRSh1.writeMicroseconds(R_SH1_NEUTRAL_US);
    sRSh2.writeMicroseconds(R_SH2_NEUTRAL_US);
  }

  if (t >= ROUND_TOTAL) {
    talkCycleStartMs = now;
  }
}

int tokenIndex(const String &src, char delim, int idx) {
  int found = 0;
  int start = 0;
  int len = src.length();
  for (int i = 0; i <= len; i++) {
    if (i == len || src[i] == delim) {
      if (found == idx) return start;
      found++;
      start = i + 1;
    }
  }
  return -1;
}

String tokenAt(const String &src, char delim, int idx) {
  int start = tokenIndex(src, delim, idx);
  if (start < 0) return "";
  int i = start;
  while (i < (int)src.length() && src[i] != delim) i++;
  return src.substring(start, i);
}

void applyElbowStep(const String &side, const String &direction, int amount) {
  int stepUs = constrain(amount, 1, 100) * 6;
  int dir = (direction == "UP") ? 1 : -1;
  if (side == "LEFT") {
    int lo = min(L_ELB_OPEN_US, L_ELB_BEND_US);
    int hi = max(L_ELB_OPEN_US, L_ELB_BEND_US);
    currentLElbUs = constrain(currentLElbUs + dir * stepUs, lo, hi);
    powerOn(L_ELB_PWR); sLElb.attach(L_ELB_PIN); sLElb.writeMicroseconds(currentLElbUs);
    delay(ARM_STEP_MS);
    sLElb.detach(); powerOff(L_ELB_PWR);
  } else {
    int lo = min(R_ELB_OPEN_US, R_ELB_BEND_US);
    int hi = max(R_ELB_OPEN_US, R_ELB_BEND_US);
    currentRElbUs = constrain(currentRElbUs + dir * stepUs, lo, hi);
    powerOn(R_ELB_PWR); sRElb.attach(R_ELB_PIN); sRElb.writeMicroseconds(currentRElbUs);
    delay(ARM_STEP_MS);
    sRElb.detach(); powerOff(R_ELB_PWR);
  }
}

// ================== SHOULDER MOVEMENT CONTROLLER ==================
// Controls continuous rotation shoulder servos (LEFT_SH1, LEFT_SH2, RIGHT_SH1, RIGHT_SH2)
// 
// MECHANISM:
// 1. Power ON the shoulder servo
// 2. Set pulse width to target (UP or DOWN value)
//    - UP pulse (e.g., 1700µs): Servo rotates in UP direction
//    - DOWN pulse (e.g., 700µs): Servo rotates in DOWN direction
// 3. WAIT for SHOULDER_STEP_MS (1000ms = 2x amplification)
//    - Servo moves toward target during this time
//    - Longer wait = more rotation at same speed
// 4. Set pulse width back to NEUTRAL to stop
// 5. Power OFF
//
// CALIBRATION VALUES (microseconds):
// - UP (e.g., 1700µs): High pulse → rotate UP direction
// - DOWN (e.g., 700µs): Low pulse → rotate DOWN direction  
// - NEUTRAL (~1400µs): Middle pulse → servo stopped
//
// WHY 2x MOVEMENT WORKS:
// - Original: delay(500ms) → 50% of max rotation range
// - Amplified: delay(1000ms) → 100% of max rotation range (2x)
// ===================================================================
// ================== SHOULDER MOVEMENT CONTROLLER ==================
// Controls continuous rotation shoulder servos (LEFT_SH1, LEFT_SH2, RIGHT_SH1, RIGHT_SH2)
// 
// MECHANISM:
// 1. Power ON the shoulder servo
// 2. Set pulse width to target (UP or DOWN value)
//    - UP pulse (e.g., 1700µs): Servo rotates in UP direction
//    - DOWN pulse (e.g., 700µs): Servo rotates in DOWN direction
// 3. WAIT for SHOULDER_STEP_MS (1000ms = 2x amplification)
//    - Servo moves toward target during this time
//    - Longer wait = more rotation at same speed
// 4. Set pulse width back to NEUTRAL to stop
// 5. Power OFF
//
// CALIBRATION VALUES (microseconds):
// - UP (e.g., 1700µs): High pulse → rotate UP direction
// - DOWN (e.g., 700µs): Low pulse → rotate DOWN direction  
// - NEUTRAL (~1400µs): Middle pulse → servo stopped
//
// WHY 2x MOVEMENT WORKS:
// - Original: delay(500ms) → 50% of max rotation range
// - Amplified: delay(1000ms) → 100% of max rotation range (2x)
// ===================================================================
void applyShoulderStep(const String &side, const String &joint, const String &direction) {
  // SHOULDER2 is handled as positional-step to ensure visible calibration movement.
  if (joint == "SHOULDER2") {
    if (side == "LEFT") {
      currentLSh2Us = (direction == "UP") ? L_SH2_UP_US : L_SH2_DOWN_US;

      powerOn(L_SH2_PWR);
      sLSh2.attach(L_SH2_PIN);
      sLSh2.writeMicroseconds(clampUs(currentLSh2Us));
      delay(SHOULDER_STEP_MS);
      sLSh2.detach();
      powerOff(L_SH2_PWR);
    } else {
      currentRSh2Us = (direction == "UP") ? R_SH2_UP_US : R_SH2_DOWN_US;

      powerOn(R_SH2_PWR);
      sRSh2.attach(R_SH2_PIN);
      sRSh2.writeMicroseconds(clampUs(currentRSh2Us));
      delay(SHOULDER_STEP_MS);
      sRSh2.detach();
      powerOff(R_SH2_PWR);
    }
    return;
  }

  int target = 1500;
  if (side == "LEFT") {
    if (joint == "SHOULDER1") target = (direction == "UP") ? L_SH1_UP_US : L_SH1_DOWN_US;
    if (joint == "SHOULDER2") target = (direction == "UP") ? L_SH2_UP_US : L_SH2_DOWN_US;
    uint8_t pwr = (joint == "SHOULDER1") ? L_SH1_PWR : L_SH2_PWR;
    uint8_t pin = (joint == "SHOULDER1") ? L_SH1_PIN : L_SH2_PIN;
    Servo *s = (joint == "SHOULDER1") ? &sLSh1 : &sLSh2;
    int neutral = (joint == "SHOULDER1") ? L_SH1_NEUTRAL_US : L_SH2_NEUTRAL_US;
    powerOn(pwr); s->attach(pin); s->writeMicroseconds(clampUs(target));
    delay(SHOULDER_STEP_MS);
    s->writeMicroseconds(clampUs(neutral));
    delay(120);
    s->detach(); powerOff(pwr);
  } else {
    if (joint == "SHOULDER1") target = (direction == "UP") ? R_SH1_UP_US : R_SH1_DOWN_US;
    if (joint == "SHOULDER2") target = (direction == "UP") ? R_SH2_UP_US : R_SH2_DOWN_US;
    uint8_t pwr = (joint == "SHOULDER1") ? R_SH1_PWR : R_SH2_PWR;
    uint8_t pin = (joint == "SHOULDER1") ? R_SH1_PIN : R_SH2_PIN;
    Servo *s = (joint == "SHOULDER1") ? &sRSh1 : &sRSh2;
    int neutral = (joint == "SHOULDER1") ? R_SH1_NEUTRAL_US : R_SH2_NEUTRAL_US;
    powerOn(pwr); s->attach(pin); s->writeMicroseconds(clampUs(target));
    delay(SHOULDER_STEP_MS);
    s->writeMicroseconds(clampUs(neutral));
    delay(120);
    s->detach(); powerOff(pwr);
  }
}

void processArmCal(const String &line) {
  String side = tokenAt(line, ':', 1);
  String joint = tokenAt(line, ':', 2);
  String direction = tokenAt(line, ':', 3);
  String amountStr = tokenAt(line, ':', 4);
  side.trim(); joint.trim(); direction.trim(); amountStr.trim();
  side.toUpperCase(); joint.toUpperCase(); direction.toUpperCase();
  int amount = amountStr.toInt();
  if (amount <= 0) amount = 15;

  if ((side != "LEFT" && side != "RIGHT") || (direction != "UP" && direction != "DOWN")) {
    Serial.println("ERR:ARM_CAL:BAD_ARGS");
    return;
  }
  if (joint == "ELBOW") {
    applyElbowStep(side, direction, amount);
    Serial.println("ACK:ARM_CAL:ELBOW");
    return;
  }
  if (joint == "SHOULDER1" || joint == "SHOULDER2") {
    applyShoulderStep(side, joint, direction);
    Serial.println("ACK:ARM_CAL:SHOULDER");
    return;
  }
  Serial.println("ERR:ARM_CAL:BAD_JOINT");
}

void processLine(String line) {
  line.trim();
  if (line.length() == 0) return;

  if (line.startsWith("FINGER:")) {
    processFingerCmd(line);
    return;
  }

  if (line.startsWith("ARM_CAL:")) {
    processArmCal(line);
    return;
  }

  if (line == "TALK_ON") {
    startTalkingMotion();
    Serial.println("ACK:TALK_ON");
    return;
  }
  if (line == "TALK_OFF") {
    stopTalkingMotion();
    Serial.println("ACK:TALK_OFF");
    return;
  }

  if (line.indexOf("\"type\": \"gesture_start\"") >= 0 || line.indexOf("\"type\":\"gesture_start\"") >= 0) {
    startTalkingMotion();
    Serial.println("ACK:GESTURE_START");
    return;
  }
  if (line.indexOf("\"type\": \"gesture_stop\"") >= 0 || line.indexOf("\"type\":\"gesture_stop\"") >= 0) {
    stopTalkingMotion();
    Serial.println("ACK:GESTURE_STOP");
    return;
  }

  if (line == "STOP_ALL" || line == "CAL_END") {
    stopTalkingMotion();
    neutralShouldersAndDetach();
    setElbowsToCurrentAndDetach();
    Serial.println("ACK:STOP_ALL");
  }
}

void setup() {
  Serial.begin(115200);
  sThumb.attach(THUMB_PIN);
  sIndex.attach(INDEX_PIN);
  sMiddle.attach(MIDDLE_PIN);
  sRing.attach(RING_PIN);
  sPinky.attach(PINKY_PIN);
  sLThumb.attach(LTHUMB_PIN);
  sLIndex.attach(LINDEX_PIN);
  sLMiddle.attach(LMIDDLE_PIN);
  sLRing.attach(LRING_PIN);
  sLPinky.attach(LPINKY_PIN);

  setFingersOpen();
  neutralShouldersAndDetach();
  setElbowsToCurrentAndDetach();

  Serial.println("READY:FINGER_SERVOS_WITH_ARM_CAL");
}

void loop() {
  updateTalkingMotion();
  if (Serial.available() > 0) {
    String line = Serial.readStringUntil('\n');
    processLine(line);
  }
}
