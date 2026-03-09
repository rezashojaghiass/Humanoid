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
const bool EN_L_SH1 = false;
const bool EN_L_ELB = false;
const bool EN_L_SH2 = false;

const bool EN_R_SH1 = false;
const bool EN_R_ELB = false;
const bool EN_R_SH2 = false;


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
// LEFT SHOULDER #1 (continuous)
const int LSH1_DOWN    = 700;
const int LSH1_NEUTRAL = 1370;   // adjust if needed
const int LSH1_UP      = 1700;

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
