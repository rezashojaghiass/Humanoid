// ============================================================
// OMNIDIRECTIONAL BASE CONTROL - Arduino #2 (Clone CH340)
// ============================================================
// Upload Port: /dev/ttyUSB0 (Linux) or COM port (Windows)
// Board: Arduino Mega 2560 Clone with CH340 USB chip
// Function: Controls 4 DC motors for omnidirectional movement
// NOT for finger servo control - use finger_servos.ino on Arduino #1
// ============================================================

#include <PS2X_lib.h>

// PS2 Controller pin mapping
#define PS2_DAT  9    
#define PS2_CMD  10   
#define PS2_SEL  13   
#define PS2_CLK  44   

PS2X ps2x;
int error = 0;

// Speed tuning
const int BASE_SPEED = 150;     // Max base speed (0-255)
const float SPEED_RATIO = 0.2;  // 0.1 to 1.0
const int RAMP_RATE = 100;      // Speed increase/decrease per loop (0-255)
int currentSpeed = 0;           // Current motor speed
int lastMotorA = 0, lastMotorB = 0, lastMotorC = 0, lastMotorD = 0;

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
// Motor control function
// ============================================================
void setMotor(int pwm, int dir1, int dir2, int speed) {
    if (speed > 0) { // Forward
        digitalWrite(dir1, HIGH);
        digitalWrite(dir2, LOW);
    } else if (speed < 0) { // Backward
        digitalWrite(dir1, LOW);
        digitalWrite(dir2, HIGH);
    } else { // Stop
        digitalWrite(dir1, LOW);
        digitalWrite(dir2, LOW);
    }
    analogWrite(pwm, abs(speed));
}

void setup() {
    Serial.begin(9600);
    delay(1000);

    // Initialize motor pins
    pinMode(PWMA, OUTPUT); pinMode(DIRA1, OUTPUT); pinMode(DIRA2, OUTPUT);
    pinMode(PWMB, OUTPUT); pinMode(DIRB1, OUTPUT); pinMode(DIRB2, OUTPUT);
    pinMode(PWMC, OUTPUT); pinMode(DIRC1, OUTPUT); pinMode(DIRC2, OUTPUT);
    pinMode(PWMD, OUTPUT); pinMode(DIRD1, OUTPUT); pinMode(DIRD2, OUTPUT);
    
    // Stop all motors initially
    digitalWrite(PWMA, LOW);
    digitalWrite(PWMB, LOW);
    digitalWrite(PWMC, LOW);
    digitalWrite(PWMD, LOW);
    
    Serial.println("\n=== OMNIDIRECTIONAL BASE CONTROL ===");
    Serial.println("Board: Arduino Mega 2560 Clone (CH340)");
    Serial.println("Port: /dev/ttyUSB0 or /dev/ttyUSB1");
    Serial.println("Function: 4-wheel motor control");
    Serial.println("Status: Initializing PS2 Controller...");
    
    error = ps2x.config_gamepad(PS2_CLK, PS2_CMD, PS2_SEL, PS2_DAT, false, false);
    if (error == 0) {
        Serial.println("✅ PS2 Controller connected successfully!");
    } else {
        Serial.println("❌ PS2 Controller connection failed! Check wiring.");
    }
}

void loop() {
    if (error) return;

    ps2x.read_gamepad(false, 0);
    
    // Read analog sticks
    int LX = ps2x.Analog(PSS_LX) - 127;  // Left/Right strafing
    int LY = ps2x.Analog(PSS_LY) - 127;  // Forward/Backward
    int RX = ps2x.Analog(PSS_RX) - 127;  // Rotation

    int driveSpeed = (int)(BASE_SPEED * SPEED_RATIO);
    bool moving = false;

    // FORWARD movement
    if (LY < -20) {
        if (currentSpeed < driveSpeed) currentSpeed += RAMP_RATE;
        if (currentSpeed > driveSpeed) currentSpeed = driveSpeed;
        lastMotorA = currentSpeed;
        lastMotorB = currentSpeed;
        lastMotorC = currentSpeed;
        lastMotorD = currentSpeed;
        setMotor(PWMA, DIRA1, DIRA2, lastMotorA);
        setMotor(PWMB, DIRB1, DIRB2, lastMotorB);
        setMotor(PWMC, DIRC1, DIRC2, lastMotorC);
        setMotor(PWMD, DIRD1, DIRD2, lastMotorD);
        Serial.println("⬆️ Moving Forward");
        moving = true;
    } 
    // BACKWARD movement
    else if (LY > 20) {
        if (currentSpeed < driveSpeed) currentSpeed += RAMP_RATE;
        if (currentSpeed > driveSpeed) currentSpeed = driveSpeed;
        lastMotorA = -currentSpeed;
        lastMotorB = -currentSpeed;
        lastMotorC = -currentSpeed;
        lastMotorD = -currentSpeed;
        setMotor(PWMA, DIRA1, DIRA2, lastMotorA);
        setMotor(PWMB, DIRB1, DIRB2, lastMotorB);
        setMotor(PWMC, DIRC1, DIRC2, lastMotorC);
        setMotor(PWMD, DIRD1, DIRD2, lastMotorD);
        Serial.println("⬇️ Moving Backward");
        moving = true;
    }
    // STRAFE LEFT
    else if (LX < -20) {
        if (currentSpeed < driveSpeed) currentSpeed += RAMP_RATE;
        if (currentSpeed > driveSpeed) currentSpeed = driveSpeed;
        lastMotorA = -currentSpeed;
        lastMotorB = currentSpeed;
        lastMotorC = -currentSpeed;
        lastMotorD = currentSpeed;
        setMotor(PWMA, DIRA1, DIRA2, lastMotorA);
        setMotor(PWMB, DIRB1, DIRB2, lastMotorB);
        setMotor(PWMC, DIRC1, DIRC2, lastMotorC);
        setMotor(PWMD, DIRD1, DIRD2, lastMotorD);
        Serial.println("⬅️ Strafing Left");
        moving = true;
    } 
    // STRAFE RIGHT
    else if (LX > 20) {
        if (currentSpeed < driveSpeed) currentSpeed += RAMP_RATE;
        if (currentSpeed > driveSpeed) currentSpeed = driveSpeed;
        lastMotorA = currentSpeed;
        lastMotorB = -currentSpeed;
        lastMotorC = currentSpeed;
        lastMotorD = -currentSpeed;
        setMotor(PWMA, DIRA1, DIRA2, lastMotorA);
        setMotor(PWMB, DIRB1, DIRB2, lastMotorB);
        setMotor(PWMC, DIRC1, DIRC2, lastMotorC);
        setMotor(PWMD, DIRD1, DIRD2, lastMotorD);
        Serial.println("➡️ Strafing Right");
        moving = true;
    }
    // ROTATE LEFT
    else if (RX < -20) {
        if (currentSpeed < driveSpeed) currentSpeed += RAMP_RATE;
        if (currentSpeed > driveSpeed) currentSpeed = driveSpeed;
        lastMotorA = -currentSpeed;
        lastMotorB = currentSpeed;
        lastMotorC = currentSpeed;
        lastMotorD = -currentSpeed;
        setMotor(PWMA, DIRA1, DIRA2, lastMotorA);
        setMotor(PWMB, DIRB1, DIRB2, lastMotorB);
        setMotor(PWMC, DIRC1, DIRC2, lastMotorC);
        setMotor(PWMD, DIRD1, DIRD2, lastMotorD);
        Serial.println("↩️ Rotating Left");
        moving = true;
    }
    // ROTATE RIGHT
    else if (RX > 20) {
        if (currentSpeed < driveSpeed) currentSpeed += RAMP_RATE;
        if (currentSpeed > driveSpeed) currentSpeed = driveSpeed;
        lastMotorA = currentSpeed;
        lastMotorB = -currentSpeed;
        lastMotorC = -currentSpeed;
        lastMotorD = currentSpeed;
        setMotor(PWMA, DIRA1, DIRA2, lastMotorA);
        setMotor(PWMB, DIRB1, DIRB2, lastMotorB);
        setMotor(PWMC, DIRC1, DIRC2, lastMotorC);
        setMotor(PWMD, DIRD1, DIRD2, lastMotorD);
        Serial.println("↪️ Rotating Right");
        moving = true;
    } 
    
    // Gradually decelerate when stopped
    if (!moving) {
        if (currentSpeed > 0) {
            currentSpeed -= RAMP_RATE;
            if (currentSpeed < 0) currentSpeed = 0;
            // Apply ramped-down speed in last direction
            int scaledA = (lastMotorA > 0) ? currentSpeed : (lastMotorA < 0) ? -currentSpeed : 0;
            int scaledB = (lastMotorB > 0) ? currentSpeed : (lastMotorB < 0) ? -currentSpeed : 0;
            int scaledC = (lastMotorC > 0) ? currentSpeed : (lastMotorC < 0) ? -currentSpeed : 0;
            int scaledD = (lastMotorD > 0) ? currentSpeed : (lastMotorD < 0) ? -currentSpeed : 0;
            setMotor(PWMA, DIRA1, DIRA2, scaledA);
            setMotor(PWMB, DIRB1, DIRB2, scaledB);
            setMotor(PWMC, DIRC1, DIRC2, scaledC);
            setMotor(PWMD, DIRD1, DIRD2, scaledD);
        } else {
            setMotor(PWMA, DIRA1, DIRA2, 0);
            setMotor(PWMB, DIRB1, DIRB2, 0);
            setMotor(PWMC, DIRC1, DIRC2, 0);
            setMotor(PWMD, DIRD1, DIRD2, 0);
            Serial.println("🛑 Stopped");
        }
    }

    delay(100);
}
