#!/usr/bin/env python3
"""
Test script to verify serial communication with Arduino #2 (Motor Base)

This script:
1. Opens serial connection to /dev/ttyUSB0 @ 9600 baud
2. Monitors PS2 controller input debug output
3. Sends manual motor commands (if needed)
4. Displays received status messages
"""

import serial
import time
import sys

# Configuration
MOTOR_PORT = "/dev/ttyUSB0"
MOTOR_BAUD = 9600
TIMEOUT = 2.0

# Alternate port if /dev/ttyUSB0 is unavailable
ALTERNATE_PORTS = ["/dev/ttyUSB1", "/dev/ttyUSB2", "COM5", "COM6"]

def find_motor_port():
    """Find available motor control Arduino port"""
    ports_to_try = [MOTOR_PORT] + ALTERNATE_PORTS
    
    for port in ports_to_try:
        try:
            ser = serial.Serial(port, MOTOR_BAUD, timeout=TIMEOUT)
            ser.close()
            return port
        except:
            continue
    
    return None

def open_serial(port):
    """Open serial connection to Arduino"""
    try:
        ser = serial.Serial(port, MOTOR_BAUD, timeout=TIMEOUT)
        time.sleep(1)  # Wait for Arduino to initialize
        print(f"✅ Connected to {port} @ {MOTOR_BAUD} baud")
        return ser
    except Exception as e:
        print(f"❌ Failed to open serial port: {e}")
        return None

def monitor_motor_output(ser, duration=30):
    """Monitor motor status output for specified duration"""
    print(f"\n=== MONITORING MOTOR OUTPUT FOR {duration} SECONDS ===")
    print("(Move PS2 controller to test motor commands)\n")
    
    start_time = time.time()
    last_output = time.time()
    
    while (time.time() - start_time) < duration:
        if ser and ser.in_waiting:
            try:
                data = ser.readline().decode('utf-8').strip()
                if data:
                    print(f"  {data}")
                    last_output = time.time()
            except:
                pass
        else:
            # Show heartbeat every 5 seconds
            if time.time() - last_output > 5:
                elapsed = int(time.time() - start_time)
                print(f"  ⏳ {elapsed}s elapsed (waiting for PS2 input)...")
                last_output = time.time()
            
            time.sleep(0.1)

def test_motor_commands(ser):
    """Send direct motor commands (for testing without PS2 controller)"""
    print("\n=== TESTING MOTOR COMMANDS ===")
    print("(Note: Serial protocol may not accept direct motor commands)")
    print("(Use PS2 Controller for proper motor testing)\n")
    
    # Try sending test strings (verify with Arduino firmware first)
    test_commands = [
        "M_FORWARD",
        "M_BACKWARD", 
        "M_LEFT",
        "M_RIGHT",
        "M_STOP",
    ]
    
    for cmd in test_commands:
        if ser:
            try:
                print(f"📤 Sending: {cmd}")
                ser.write((cmd + '\n').encode())
                time.sleep(1)
                
                # Try to read response
                if ser.in_waiting:
                    response = ser.readline().decode('utf-8').strip()
                    print(f"📥 Response: {response}")
            except:
                pass
        print()

def main():
    """Main test sequence"""
    print("╔═════════════════════════════════════════╗")
    print("║  Arduino Motor Base Serial Test         ║")
    print("╚═════════════════════════════════════════╝\n")
    
    # Find motor Arduino
    port = find_motor_port()
    if not port:
        print("❌ Could not find motor Arduino on any port")
        print("   Tried: /dev/ttyUSB0, /dev/ttyUSB1, /dev/ttyUSB2, COM5, COM6")
        print("\n   Troubleshooting:")
        print("   1. Check USB connection")
        print("   2. Verify correct Arduino board (Clone CH340)")
        print("   3. Install CH340 drivers: https://www.wch.cn/downloads/CH341SER_EXE.html")
        print("   4. Run: lsusb | grep CH340 (Linux)")
        sys.exit(1)
    
    ser = open_serial(port)
    if not ser:
        sys.exit(1)
    
    try:
        # Show initial status
        print("\nWaiting for Arduino to initialize...")
        time.sleep(2)
        
        # Read initial boot messages
        print("\nBoot messages from Arduino:")
        print("-" * 40)
        while ser.in_waiting:
            try:
                data = ser.readline().decode('utf-8').strip()
                if data:
                    print(f"  {data}")
            except:
                pass
        
        # Monitor PS2 controller output
        monitor_motor_output(ser, duration=30)
        
        # Test motor commands (if firmware supports it)
        # test_motor_commands(ser)
        
        print("\n✅ Motor test completed!")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    finally:
        if ser:
            ser.close()
            print(f"Serial port {port} closed")

if __name__ == "__main__":
    main()
