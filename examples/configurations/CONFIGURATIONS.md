# Configuration Examples

This directory contains example configuration files and templates for different deployment scenarios.

## Standard Configuration

See `config/config.yaml` for complete reference with all available options.

## Hardware-Specific Configurations

### Jetson Xavier (Recommended)
- NVIDIA Riva ASR/TTS (Docker container, GPU-accelerated)
- AWS Bedrock LLM via API
- PyAudio for audio I/O
- Serial communication at 115200 baud

### Raspberry Pi 4 (Limited)
- CPU-based Riva TTS (slower)
- AWS Bedrock LLM via API
- PyAudio or ALSA
- Serial communication at 115200 baud

## Audio Device Configuration

Detect your audio devices first:
```bash
python examples/test_scripts/test_audio_devices.py
```

Then update `config/config.yaml`:
```yaml
speech:
  # KT USB Speaker on this Xavier is usually index 25
  # Re-check after reboot with test_audio_devices.py
  output_device_index: 25
  sample_rate_hz: 48000

asr:
  # Set mic index from test_audio_devices.py output (often Wireless GO II)
  input_device_index: 8
  sample_rate_hz: 48000
```

## Serial Port Configuration

### Linux
```yaml
hardware:
  arduino_finger:
    port: /dev/ttyACM0
    baudrate: 115200
  
  arduino_motor:
    port: /dev/ttyUSB0
    baudrate: 9600
```

### Windows
```yaml
hardware:
  arduino_finger:
    port: COM3
    baudrate: 115200
  
  arduino_motor:
    port: COM5
    baudrate: 9600
```

### macOS
```yaml
hardware:
  arduino_finger:
    port: /dev/cu.usbmodem14201
    baudrate: 115200
  
  arduino_motor:
    port: /dev/cu.usbserial-0001
    baudrate: 9600
```

## AWS Bedrock Configuration

Set up AWS credentials:
```bash
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_REGION=us-east-1  # or your region
```

Or create `~/.aws/credentials`:
```ini
[default]
aws_access_key_id = YOUR_KEY
aws_secret_access_key = YOUR_SECRET

[default]
region = us-east-1
```

## Gesture Configuration

Customize gesture behavior in `config/config.yaml`:

```yaml
gestures:
  wave:
    hand: right
    duration_ms: 2000
    speed_factor: 1.0
    repeat: 1
  
  point:
    hand: right
    finger: index
    duration_ms: 1500
    speed_factor: 1.0
    repeat: 1
```

## Voice Processing Pipeline

Configure ASR/TTS/LLM parameters:

```yaml
voice:
  asr:
    sample_rate: 16000
    vad_threshold: 0.5
    timeout_ms: 30000
    language: en-US
  
  llm:
    model: claude-3-haiku  # or llama3-8b
    max_tokens: 256
    temperature: 0.7
  
  tts:
    sample_rate: 48000
    voice: English-US-Hellen
    speaking_rate: 1.0
```

## Logging Configuration

Control verbosity:

```yaml
logging:
  level: INFO  # DEBUG, INFO, WARNING, ERROR
  file: logs/humanoid.log
  max_size_mb: 10
  backup_count: 5
```

## Testing with Different Configs

### Test text-only (no audio devices needed)
```bash
python src/robot_sync_app/main.py --text "Hello, can you wave?"
```

### Test with custom config
```bash
HUMANOID_CONFIG=examples/configurations/custom_config.yaml \
  python src/robot_sync_app/main.py --voice
```

## Troubleshooting Configuration

### Audio device not found
```bash
# Check available devices
python examples/test_scripts/test_audio_devices.py

# Update device IDs in config.yaml
```

### Serial ports not accessible (Linux)
```bash
# Add current user to dialout group
sudo usermod -a -G dialout $USER

# Reload group membership (requires logout/login)
newgrp dialout
```

### AWS Bedrock timeout
```yaml
# Increase timeout in config
voice:
  llm:
    timeout_seconds: 30
    max_retries: 3
```

## Performance Tuning

### For low-latency voice interaction
```yaml
voice:
  asr:
    vad_threshold: 0.6  # Faster detection
    timeout_ms: 20000
  llm:
    max_tokens: 128  # Shorter responses
```

### For high-quality responses
```yaml
voice:
  asr:
    vad_threshold: 0.3  # More sensitive
    timeout_ms: 40000
  llm:
    max_tokens: 512  # Longer responses
    temperature: 0.5  # More consistent
```

## Files in This Directory

- `CONFIGURATIONS.md` - This file
- `config_jetson.yaml` - (To be created) Jetson Xavier optimized
- `config_pi.yaml` - (To be created) Raspberry Pi optimized
- `config_minimal.yaml` - (To be created) Minimal config (no voice)
