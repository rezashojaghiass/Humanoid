#!/usr/bin/env python3
"""
Test script to verify serial communication with Arduino #1 (Finger Servos)

This script:
1. Opens serial connection to /dev/ttyACM0 @ 115200 baud
2. Sends JSON gesture commands
3. Prints responses
4. Tests all hand gestures
"""

import serial
import json
import time
import sys

# Configuration
ARDUINO_PORT = "/dev/ttyACM0"
BAUD_RATE = 115200
TIMEOUT = 2.0

def open_serial():
    """Open serial connection to Arduino"""
    try:
        ser = serial.Serial(ARDUINO_PORT, BAUD_RATE, timeout=TIMEOUT)
        time.sleep(2)  # Wait for Arduino to initialize
        print(f"✅ Connected to {ARDUINO_PORT} @ {BAUD_RATE} baud")
        return ser
    except Exception as e:
        print(f"❌ Failed to open serial port: {e}")
        sys.exit(1)

def send_command(ser, command):
    """Send JSON command to Arduino"""
    cmd_str = json.dumps(command) + '\n'
    print(f"📤 Sending: {cmd_str.strip()}")
    ser.write(cmd_str.encode())
    
    # Read response with timeout
    time.sleep(0.1)
    response = ""
    while ser.in_waiting:
        response += ser.read().decode()
    
    if response:
        print(f"📥 Response: {response.strip()}")
    time.sleep(0.5)

def test_finger_gestures(ser):
    """Test basic finger gestures"""
    print("\n=== TESTING FINGER GESTURES ===\n")
    
    gestures = [
        {"type": "gesture", "gesture": "open_hand", "hand": "right"},
        {"type": "gesture", "gesture": "close_hand", "hand": "right"},
        {"type": "gesture", "gesture": "open_hand", "hand": "left"},
        {"type": "gesture", "gesture": "close_hand", "hand": "left"},
        {"type": "gesture", "gesture": "wave", "hand": "right"},
        {"type": "gesture", "gesture": "point", "hand": "right", "finger": "index"},
        {"type": "gesture", "gesture": "peace", "hand": "left"},
        {"type": "gesture", "gesture": "thumbs_up", "hand": "right"},
    ]
    
    for gesture in gestures:
        send_command(ser, gesture)
        print()

def test_arm_gestures(ser):
    """Test arm gestures (if enabled in firmware)"""
    print("\n=== TESTING ARM GESTURES ===\n")
    
    gestures = [
        {"type": "gesture", "gesture": "raise_arm", "arm": "right"},
        {"type": "gesture", "gesture": "lower_arm", "arm": "right"},
        {"type": "gesture", "gesture": "raise_arm", "arm": "left"},
        {"type": "gesture", "gesture": "lower_arm", "arm": "left"},
        {"type": "gesture", "gesture": "wave_arm", "arm": "right"},
    ]
    
    for gesture in gestures:
        send_command(ser, gesture)
        print()

def test_direct_servo_control(ser):
    """Test direct servo microsecond control"""
    print("\n=== TESTING DIRECT SERVO CONTROL ===\n")
    
    # Test individual servos
    servos = [
        {"type": "servo", "id": "R_THUMB", "pin": 2, "microseconds": 1500},
        {"type": "servo", "id": "R_INDEX", "pin": 3, "microseconds": 1350},
        {"type": "servo", "id": "R_MIDDLE", "pin": 4, "microseconds": 1350},
        {"type": "servo", "id": "L_THUMB", "pin": 7, "microseconds": 1500},
        {"type": "servo", "id": "L_INDEX", "pin": 8, "microseconds": 1350},
    ]
    
    for servo_cmd in servos:
        send_command(ser, servo_cmd)
        print()

def test_continuous_reading(ser, duration=10):
    """Read all serial output for specified duration (for debugging)"""
    print(f"\n=== READING SERIAL OUTPUT FOR {duration} SECONDS ===\n")
    
    start_time = time.time()
    while (time.time() - start_time) < duration:
        if ser.in_waiting:
            data = ser.read().decode()
            sys.stdout.write(data)
            sys.stdout.flush()
        else:
            time.sleep(0.01)

def main():
    """Main test sequence"""
    print("╔════════════════════════════════════════╗")
    print("║  Arduino Finger Servo Serial Test      ║")
    print("╚════════════════════════════════════════╝\n")
    
    ser = open_serial()
    
    try:
        # Run test sequences
        test_finger_gestures(ser)
        time.sleep(1)
        
        test_direct_servo_control(ser)
        time.sleep(1)
        
        # Uncomment to test arm servos (requires EN_* = true in firmware)
        # test_arm_gestures(ser)
        
        print("\n✅ All tests completed!")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    finally:
        ser.close()
        print(f"Serial port {ARDUINO_PORT} closed")

if __name__ == "__main__":
    main()
