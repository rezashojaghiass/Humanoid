#!/usr/bin/env python3
"""
Voice chat example - demonstrates the voice-enabled interaction pipeline

Usage:
    python voice_chat_example.py [--text "Your question here"] [--voice]

Features:
    - Captures audio from Wireless GO II microphone (48kHz)
    - Transcribes with NVIDIA Riva ASR (16kHz)
    - Processes with AWS Bedrock LLM
    - Synthesizes response with NVIDIA Riva TTS
    - Controls finger gestures via Arduino serial
"""

import os
import sys
import argparse
import json
import time

# Example commands that would be processed
EXAMPLE_PROMPTS = [
    "Hello! How are you today?",
    "Can you wave at me?",
    "What's your favorite color?",
    "Can you give me a thumbs up?",
    "Tell me a joke",
    "Can you point to something?",
]

EXAMPLE_GESTURE_MAP = {
    "wave": {"gesture": "wave", "hand": "right", "duration_ms": 3000},
    "thumbs_up": {"gesture": "thumbs_up", "hand": "right", "duration_ms": 1000},
    "thumbs_down": {"gesture": "thumbs_down", "hand": "right", "duration_ms": 1000},
    "point": {"gesture": "point", "hand": "right", "finger": "index", "duration_ms": 2000},
    "peace": {"gesture": "peace", "hand": "left", "duration_ms": 1500},
    "open_hand": {"gesture": "open_hand", "hand": "right", "duration_ms": 500},
    "close_hand": {"gesture": "close_hand", "hand": "right", "duration_ms": 500},
}

def main():
    """Main voice chat example"""
    parser = argparse.ArgumentParser(description="Voice chat interaction example")
    parser.add_argument("--text", help="Text input instead of voice")
    parser.add_argument("--voice", action="store_true", help="Use voice input (requires mic)")
    parser.add_argument("--gesture", help="Test specific gesture (e.g., 'wave', 'thumbs_up')")
    
    args = parser.parse_args()
    
    print("╔══════════════════════════════════════════╗")
    print("║  Voice Chat Example - Humanoid Robot     ║")
    print("╚══════════════════════════════════════════╝\n")
    
    if args.gesture:
        # Direct gesture test
        test_gesture(args.gesture)
        return
    
    if args.voice:
        user_input = capture_voice()
    elif args.text:
        user_input = args.text
    else:
        # Interactive mode
        print("Select an example or type your own:")
        for i, prompt in enumerate(EXAMPLE_PROMPTS, 1):
            print(f"  {i}. {prompt}")
        print("  0. Custom input")
        
        try:
            choice = int(input("\nChoice (0-6): "))
            if 0 <= choice < len(EXAMPLE_PROMPTS):
                user_input = EXAMPLE_PROMPTS[choice]
            elif choice == 0:
                user_input = input("Enter your message: ")
            else:
                print("Invalid choice")
                return
        except ValueError:
            print("Invalid input")
            return
    
    print(f"\n📝 User: {user_input}")
    
    # Simulate processing pipeline
    response = process_with_llm(user_input)
    print(f"🤖 Robot: {response}")
    
    # Determine gesture
    gesture = map_text_to_gesture(user_input + " " + response)
    if gesture:
        print(f"💫 Gesture: {gesture['gesture']} ({gesture['hand']} hand)")
        # Would send to Arduino here
    
    # Synthesize speech
    print(f"🔊 Speaking response...")
    # synthesize_speech(response)  # Would call Riva TTS
    
    print("\n✅ Interaction complete!")

def capture_voice():
    """Capture voice input from microphone"""
    print("\n🎤 Recording audio (5 seconds, press Ctrl+C to stop)...")
    
    try:
        import sounddevice as sd
        import soundfile as sf
        import numpy as np
        
        # Record 5 seconds at 48kHz
        duration = 5
        sample_rate = 48000
        audio = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1)
        sd.wait()
        
        # Save for processing
        sf.write("/tmp/voice_input.wav", audio, sample_rate)
        print("✅ Audio captured")
        
        # Here would call Riva ASR to transcribe
        transcribed = "[ASR would transcribe here]"
        return transcribed
        
    except ImportError:
        print("❌ sounddevice not installed: pip install sounddevice soundfile")
        return "Can you wave at me?"

def process_with_llm(prompt):
    """Process text with LLM"""
    print("\n⚙️  Processing with LLM...")
    time.sleep(0.5)
    
    # Simulate LLM response (in real system, calls AWS Bedrock)
    responses = {
        "how are you": "I'm doing great, thank you for asking! I'm ready to help you.",
        "wave": "Of course! *waves enthusiastically*",
        "joke": "Why did the robot go to school? To improve its microprocessor!",
        "color": "I think blue is nice - it reminds me of the sky.",
        "thumbs up": "Absolutely! That's a great idea!",
        "point": "Sure, I can point that out for you.",
    }
    
    # Find matching response
    prompt_lower = prompt.lower()
    for key, response in responses.items():
        if key in prompt_lower:
            return response
    
    return "That's interesting! Tell me more about that."

def map_text_to_gesture(text):
    """Map text to gesture"""
    text_lower = text.lower()
    
    for gesture_name, gesture_cmd in EXAMPLE_GESTURE_MAP.items():
        if gesture_name in text_lower:
            return gesture_cmd
    
    return None

def test_gesture(gesture_name):
    """Test a specific gesture"""
    if gesture_name not in EXAMPLE_GESTURE_MAP:
        print(f"❌ Unknown gesture: {gesture_name}")
        print(f"Available: {', '.join(EXAMPLE_GESTURE_MAP.keys())}")
        return
    
    gesture = EXAMPLE_GESTURE_MAP[gesture_name]
    print(f"\n💫 Testing gesture: {gesture_name}")
    print(f"   Command: {json.dumps(gesture, indent=2)}")
    print("   [Would send to Arduino via serial]")

if __name__ == "__main__":
    main()
