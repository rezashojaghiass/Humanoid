#!/usr/bin/env python3
"""
Test audio devices (microphone and speaker)

This script:
1. Lists available audio input devices (microphone)
2. Lists available audio output devices (speaker)
3. Tests mic recording at 48kHz (for Wireless GO II)
4. Tests speaker playback at 48kHz (for KT USB Speaker)
5. Verifies audio chain for voice pipeline
"""

import sys
import numpy as np

try:
    import sounddevice as sd
    import soundfile as sf
except ImportError:
    print("❌ Missing dependencies. Install with:")
    print("   pip install sounddevice soundfile")
    sys.exit(1)

# Configuration
SAMPLE_RATE = 48000  # 48kHz for voice input/output
TEST_DURATION = 2    # seconds
AMPLITUDE = 0.3      # test tone amplitude

def list_audio_devices():
    """List all audio input and output devices"""
    print("\n=== AVAILABLE AUDIO DEVICES ===\n")
    
    devices = sd.query_devices()
    
    print("INPUT DEVICES (Microphones):")
    print("-" * 60)
    for i, device in enumerate(devices):
        if device['max_input_channels'] > 0:
            print(f"[{i}] {device['name']}")
            print(f"    Channels: {device['max_input_channels']}")
            print(f"    Sample rate: {device['default_samplerate']} Hz")
            print()
    
    print("\nOUTPUT DEVICES (Speakers):")
    print("-" * 60)
    for i, device in enumerate(devices):
        if device['max_output_channels'] > 0:
            print(f"[{i}] {device['name']}")
            print(f"    Channels: {device['max_output_channels']}")
            print(f"    Sample rate: {device['default_samplerate']} Hz")
            print()

def test_mic_input(device_id=None, duration=3):
    """Test microphone input"""
    print(f"\n=== TESTING MICROPHONE INPUT ===")
    print(f"Duration: {duration} seconds at {SAMPLE_RATE} Hz\n")
    
    if device_id is None:
        print("Using default input device")
    else:
        try:
            device_info = sd.query_devices(device_id)
            print(f"Using device: {device_info['name']}")
        except:
            print(f"Invalid device ID: {device_id}")
            return
    
    print("\n🎤 Recording audio...")
    
    try:
        audio_data = sd.rec(
            frames=int(SAMPLE_RATE * duration),
            samplerate=SAMPLE_RATE,
            channels=1,
            device=device_id,
            dtype='float32'
        )
        sd.wait()  # Wait for recording to finish
        
        # Analyze recorded audio
        rms_level = np.sqrt(np.mean(audio_data ** 2))
        peak_level = np.max(np.abs(audio_data))
        
        print(f"✅ Recording complete!")
        print(f"   RMS Level: {rms_level:.4f}")
        print(f"   Peak Level: {peak_level:.4f}")
        print(f"   Frames captured: {len(audio_data)}")
        
        # Save recording for inspection
        output_file = "/tmp/mic_test.wav"
        sf.write(output_file, audio_data, SAMPLE_RATE)
        print(f"   Saved to: {output_file}")
        
        if rms_level < 0.01:
            print("   ⚠️  Warning: Very quiet signal. Check mic volume.")
        elif rms_level > 0.9:
            print("   ⚠️  Warning: Very loud signal. Check mic gain.")
        else:
            print("   ✅ Signal level OK")
        
    except Exception as e:
        print(f"❌ Microphone test failed: {e}")

def test_speaker_output(device_id=None, duration=2):
    """Test speaker output with 1kHz tone"""
    print(f"\n=== TESTING SPEAKER OUTPUT ===")
    print(f"Duration: {duration} seconds at {SAMPLE_RATE} Hz\n")
    
    if device_id is None:
        print("Using default output device")
    else:
        try:
            device_info = sd.query_devices(device_id)
            print(f"Using device: {device_info['name']}")
        except:
            print(f"Invalid device ID: {device_id}")
            return
    
    print("\n🔊 Playing 1kHz test tone...")
    
    try:
        # Generate 1kHz sine wave
        t = np.arange(0, duration, 1 / SAMPLE_RATE)
        frequency = 1000  # Hz
        audio_data = AMPLITUDE * np.sin(2 * np.pi * frequency * t)
        audio_data = audio_data.astype('float32').reshape(-1, 1)
        
        sd.play(audio_data, samplerate=SAMPLE_RATE, device=device_id)
        sd.wait()
        
        print(f"✅ Playback complete!")
        print(f"   Frequency: 1000 Hz")
        print(f"   Amplitude: {AMPLITUDE}")
        print(f"   Duration: {duration} seconds")
        
    except Exception as e:
        print(f"❌ Speaker test failed: {e}")

def find_wireless_go_mic():
    """Locate Wireless GO II microphone"""
    print("\n=== FINDING WIRELESS GO II MICROPHONE ===\n")
    
    devices = sd.query_devices()
    go_devices = []
    
    for i, device in enumerate(devices):
        name = device['name'].lower()
        if 'wireless' in name or 'go' in name or 'rode' in name:
            go_devices.append((i, device['name']))
    
    if go_devices:
        print("Found Wireless GO devices:")
        for device_id, name in go_devices:
            print(f"  [{device_id}] {name}")
        return go_devices[0][0]
    else:
        print("❌ Wireless GO II not found")
        print("   Check device is powered and connected via USB")
        return None

def find_kt_speaker():
    """Locate KT USB Speaker"""
    print("\n=== FINDING KT USB SPEAKER ===\n")
    
    devices = sd.query_devices()
    kt_devices = []
    
    for i, device in enumerate(devices):
        name = device['name'].lower()
        if 'kt' in name or 'usb' in name and device['max_output_channels'] > 0:
            kt_devices.append((i, device['name']))
    
    if kt_devices:
        print("Found KT USB Speaker devices:")
        for device_id, name in kt_devices:
            print(f"  [{device_id}] {name}")
        return kt_devices[0][0]
    else:
        print("❌ KT USB Speaker not found")
        print("   Check device is powered and connected via USB")
        return None

def main():
    """Main test sequence"""
    print("╔════════════════════════════════════════╗")
    print("║  Audio Device Test (Voice Pipeline)    ║")
    print("╚════════════════════════════════════════╝")
    
    # List all devices
    list_audio_devices()
    
    # Find specific hardware
    mic_id = find_wireless_go_mic()
    speaker_id = find_kt_speaker()
    
    # Test microphone
    if mic_id is not None:
        test_mic_input(device_id=mic_id, duration=3)
    else:
        test_mic_input(device_id=None, duration=3)
    
    input("\nPress ENTER to test speaker...")
    
    # Test speaker
    if speaker_id is not None:
        test_speaker_output(device_id=speaker_id, duration=2)
    else:
        test_speaker_output(device_id=None, duration=2)
    
    print("\n✅ Audio device test completed!")
    print("\nQuick Summary:")
    print(f"  Microphone: {mic_id if mic_id is not None else 'Default device'}")
    print(f"  Speaker: {speaker_id if speaker_id is not None else 'Default device'}")
    print(f"  Sample Rate: {SAMPLE_RATE} Hz")
    print("\nNext steps:")
    print("  1. Update config/config.yaml with device IDs")
    print("  2. Run voice pipeline: python main.py --voice")

if __name__ == "__main__":
    main()
