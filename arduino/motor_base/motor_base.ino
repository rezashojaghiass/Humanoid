// ============================================================
// OMNIDIRECTIONAL BASE CONTROL - Arduino #2 (Clone CH340)
// ============================================================
// Upload Port: /dev/ttyUSB0 (Linux) or COM port (Windows)
// Board: Arduino Mega 2560 Clone with CH340 USB chip
// Function: Controls 4 DC motors for omnidirectional movement
// NOT for finger servo control - use finger_servos.ino on Arduino #1
// ============================================================

#include <PS2X_lib.h>

// ============================================================
// PS2 Controller pin mapping
// ============================================================
#define PS2_DAT  9
#define PS2_CMD  10
#define PS2_SEL  13
#define PS2_CLK  44

PS2X ps2x;
int error = 0;

// ============================================================
// Speed tuning
// ============================================================
const int BASE_SPEED = 150;     // Master max speed cap (0-255)

// Different power levels for different movement types
const float FB_RATIO     = 0.20;  // Forward / backward = gentle
const float STRAFE_RATIO = 0.50;  // Strafe = stronger
const float ROTATE_RATIO = 0.25;  // Rotate = stronger than FB

const int RAMP_RATE = 5;       // Smaller value = smoother acceleration/deceleration
int currentSpeed = 0;          // Current ramped speed

// Remember last motor directions for smooth deceleration
int lastMotorA = 0;
int lastMotorB = 0;
int lastMotorC = 0;
int lastMotorD = 0;

// To reduce serial spam
String lastState = "";

// ============================================================
// Motor Pin Mapping
// ============================================================

// Motor A (Front-Left)
#define PWMA 11
#define DIRA1 34
#define DIRA2 35

// Motor B (Front-Right)
#define PWMB 7
#define DIRB1 36
#define DIRB2 37

// Motor C (Back-Left)
#define PWMC 6
#define DIRC1 43
#define DIRC2 42

// Motor D (Back-Right)
#define PWMD 4
#define DIRD1 A5
#define DIRD2 A4

// ============================================================
// Print state only when changed
// ============================================================
void printStateOnce(const String& state) {
  if (state != lastState) {
    Serial.println(state);
    lastState = state;
  }
}

// ============================================================
// Motor control function
// speed > 0  => forward
// speed < 0  => backward
// speed == 0 => stop
// ============================================================
void setMotor(int pwm, int dir1, int dir2, int speed) {
  if (speed > 0) {
    digitalWrite(dir1, HIGH);
    digitalWrite(dir2, LOW);
  } else if (speed < 0) {
    digitalWrite(dir1, LOW);
    digitalWrite(dir2, HIGH);
  } else {
    digitalWrite(dir1, LOW);
    digitalWrite(dir2, LOW);
  }

  analogWrite(pwm, abs(speed));
}

// ============================================================
// Apply current motor values
// ============================================================
void applyMotors(int a, int b, int c, int d) {
  setMotor(PWMA, DIRA1, DIRA2, a);
  setMotor(PWMB, DIRB1, DIRB2, b);
  setMotor(PWMC, DIRC1, DIRC2, c);
  setMotor(PWMD, DIRD1, DIRD2, d);
}

// ============================================================
// Smoothly ramp currentSpeed toward targetSpeed
// ============================================================
void rampToTarget(int targetSpeed) {
  if (currentSpeed < targetSpeed) {
    currentSpeed += RAMP_RATE;
    if (currentSpeed > targetSpeed) currentSpeed = targetSpeed;
  } else if (currentSpeed > targetSpeed) {
    currentSpeed -= RAMP_RATE;
    if (currentSpeed < targetSpeed) currentSpeed = targetSpeed;
  }
}

// ============================================================
// Setup
// ============================================================
void setup() {
  Serial.begin(9600);
  delay(1000);

  // Initialize motor pins
  pinMode(PWMA, OUTPUT); pinMode(DIRA1, OUTPUT); pinMode(DIRA2, OUTPUT);
  pinMode(PWMB, OUTPUT); pinMode(DIRB1, OUTPUT); pinMode(DIRB2, OUTPUT);
  pinMode(PWMC, OUTPUT); pinMode(DIRC1, OUTPUT); pinMode(DIRC2, OUTPUT);
  pinMode(PWMD, OUTPUT); pinMode(DIRD1, OUTPUT); pinMode(DIRD2, OUTPUT);

  // Stop all motors initially
  applyMotors(0, 0, 0, 0);

  Serial.println();
  Serial.println("=== OMNIDIRECTIONAL BASE CONTROL ===");
  Serial.println("Board: Arduino Mega 2560 Clone (CH340)");
  Serial.println("Port: /dev/ttyUSB0 or /dev/ttyUSB1");
  Serial.println("Function: 4-wheel motor control");
  Serial.println("Status: Initializing PS2 Controller...");

  error = ps2x.config_gamepad(PS2_CLK, PS2_CMD, PS2_SEL, PS2_DAT, false, false);

  if (error == 0) {
    Serial.println("PS2 Controller connected successfully!");
  } else {
    Serial.println("PS2 Controller connection failed! Check wiring.");
  }
}

// ============================================================
// Main Loop
// ============================================================
void loop() {
  if (error != 0) {
    applyMotors(0, 0, 0, 0);
    printStateOnce("Controller not connected.");
    delay(200);
    return;
  }

  ps2x.read_gamepad(false, 0);

  // Analog stick centered around about 127
  int LX = ps2x.Analog(PSS_LX) - 127;  // strafe
  int LY = ps2x.Analog(PSS_LY) - 127;  // forward/back
  int RX = ps2x.Analog(PSS_RX) - 127;  // rotate

  // Deadzone threshold
  const int DEADZONE = 20;

  // Separate speed targets
  int fbSpeed     = (int)(BASE_SPEED * FB_RATIO);
  int strafeSpeed = (int)(BASE_SPEED * STRAFE_RATIO);
  int rotateSpeed = (int)(BASE_SPEED * ROTATE_RATIO);

  bool moving = false;

  // ==========================================================
  // FORWARD
  // ==========================================================
  if (LY < -DEADZONE) {
    rampToTarget(fbSpeed);

    lastMotorA =  currentSpeed;
    lastMotorB =  currentSpeed;
    lastMotorC =  currentSpeed;
    lastMotorD =  currentSpeed;

    applyMotors(lastMotorA, lastMotorB, lastMotorC, lastMotorD);
    printStateOnce("Moving Forward");
    moving = true;
  }

  // ==========================================================
  // BACKWARD
  // ==========================================================
  else if (LY > DEADZONE) {
    rampToTarget(fbSpeed);

    lastMotorA = -currentSpeed;
    lastMotorB = -currentSpeed;
    lastMotorC = -currentSpeed;
    lastMotorD = -currentSpeed;

    applyMotors(lastMotorA, lastMotorB, lastMotorC, lastMotorD);
    printStateOnce("Moving Backward");
    moving = true;
  }

  // ==========================================================
  // STRAFE LEFT
  // ==========================================================
  else if (LX < -DEADZONE) {
    rampToTarget(strafeSpeed);

    lastMotorA = -currentSpeed;
    lastMotorB =  currentSpeed;
    lastMotorC = -currentSpeed;
    lastMotorD =  currentSpeed;

    applyMotors(lastMotorA, lastMotorB, lastMotorC, lastMotorD);
    printStateOnce("Strafing Left");
    moving = true;
  }

  // ==========================================================
  // STRAFE RIGHT
  // ==========================================================
  else if (LX > DEADZONE) {
    rampToTarget(strafeSpeed);

    lastMotorA =  currentSpeed;
    lastMotorB = -currentSpeed;
    lastMotorC =  currentSpeed;
    lastMotorD = -currentSpeed;

    applyMotors(lastMotorA, lastMotorB, lastMotorC, lastMotorD);
    printStateOnce("Strafing Right");
    moving = true;
  }

  // ==========================================================
  // ROTATE LEFT
  // ==========================================================
  else if (RX < -DEADZONE) {
    rampToTarget(rotateSpeed);

    lastMotorA = -currentSpeed;
    lastMotorB =  currentSpeed;
    lastMotorC =  currentSpeed;
    lastMotorD = -currentSpeed;

    applyMotors(lastMotorA, lastMotorB, lastMotorC, lastMotorD);
    printStateOnce("Rotating Left");
    moving = true;
  }

  // ==========================================================
  // ROTATE RIGHT
  // ==========================================================
  else if (RX > DEADZONE) {
    rampToTarget(rotateSpeed);

    lastMotorA =  currentSpeed;
    lastMotorB = -currentSpeed;
    lastMotorC = -currentSpeed;
    lastMotorD =  currentSpeed;

    applyMotors(lastMotorA, lastMotorB, lastMotorC, lastMotorD);
    printStateOnce("Rotating Right");
    moving = true;
  }

  // ==========================================================
  // STOP / DECELERATE
  // ==========================================================
  if (!moving) {
    rampToTarget(0);

    int scaledA = (lastMotorA > 0) ? currentSpeed : (lastMotorA < 0) ? -currentSpeed : 0;
    int scaledB = (lastMotorB > 0) ? currentSpeed : (lastMotorB < 0) ? -currentSpeed : 0;
    int scaledC = (lastMotorC > 0) ? currentSpeed : (lastMotorC < 0) ? -currentSpeed : 0;
    int scaledD = (lastMotorD > 0) ? currentSpeed : (lastMotorD < 0) ? -currentSpeed : 0;

    applyMotors(scaledA, scaledB, scaledC, scaledD);

    if (currentSpeed == 0) {
      printStateOnce("Stopped");
    }
  }

  delay(50);
}