# ChatBotRobot Voice System Setup

This document consolidates voice system setup from the ChatBotRobot repository.

## NVIDIA Riva Setup

### Requirements
- Jetson AGX Xavier (8GB unified memory)
- Ubuntu 20.04 or later
- Docker installed
- 10GB+ free disk space

### Installation

**1. Install Docker** (if not already installed)
```bash
sudo apt-get update
sudo apt-get install docker.io
sudo usermod -a -G docker $USER
newgrp docker
```

**2. Pull Riva container**
```bash
# NVIDIA Riva - ASR (16kHz) and TTS (48kHz)
docker pull nvcr.io/nvidia/riva:latest
```

**3. Start Riva Server**
```bash
docker run --rm --gpus all \
  -p 50051:50051 \
  nvcr.io/nvidia/riva:latest \
  riva_start.sh
```

Should see output:
```
[riva_server.cc:main] Started server ...
[riva_server.cc:main] Accepting requests at port 50051
```

**4. Verify connection**
```bash
python3 -c "from riva.client import Client; c = Client('localhost'); print(c.get_version())"
```

### Configuration in Humanoid

Once Riva is running, update `config/config.yaml`:

```yaml
voice:
  riva:
    server: localhost
    port: 50051
    asr:
      sample_rate: 16000
      language: en-US
    tts:
      sample_rate: 48000
      voice: English-US-Hellen
```

## AWS Bedrock LLM

### Setup

**1. Create AWS Account** (if needed)
- Sign up at https://aws.amazon.com

**2. Request Model Access**
- Go to AWS Bedrock Console
- Select "Models" section
- Request access to Anthropic Claude or Meta Llama
- Wait for approval (usually instant)

**3. Create IAM User**
```bash
# Via AWS Console:
# 1. Create user with name "humanoid-robot"
# 2. Attach policy: AmazonBedrockFullAccess
# 3. Create access key (save key and secret)
```

**4. Configure AWS Credentials**

Option A: Environment variables
```bash
export AWS_ACCESS_KEY_ID=YOUR_ACCESS_KEY
export AWS_SECRET_ACCESS_KEY=YOUR_SECRET_ACCESS_KEY
export AWS_REGION=us-east-1
```

Option B: AWS credentials file
```bash
mkdir -p ~/.aws
cat > ~/.aws/credentials <<EOF
[default]
aws_access_key_id = YOUR_ACCESS_KEY
aws_secret_access_key = YOUR_SECRET_ACCESS_KEY

[default]
region = us-east-1
EOF
chmod 600 ~/.aws/credentials
```

**5. Test Bedrock connection**
```bash
python3 << 'EOF'
import boto3
client = boto3.client('bedrock-runtime', region_name='us-east-1')
print("✅ Bedrock connected!")
EOF
```

### Configuration in Humanoid

Update `config/config.yaml`:

```yaml
voice:
  llm:
    provider: bedrock
    model: claude-3-haiku
    max_tokens: 256
    temperature: 0.7
    region: us-east-1
```

## PyAudio for Microphone Input

### Installation

```bash
# Install dependencies
sudo apt-get install python3-dev libasound2-dev

# Install PyAudio
pip install PyAudio

# Or via apt (simpler)
sudo apt-get install python3-pyaudio
```

### Verify

```bash
python3 << 'EOF'
import pyaudio
p = pyaudio.PyAudio()
print(f"Found {p.get_device_count()} audio devices")
p.terminate()
EOF
```

## Wireless GO II Microphone Setup

### Device Connection

1. Power on Wireless GO II
2. Connect USB receiver to Jetson Xavier
3. Set device to charge mode (or standby)

### Verify Detection

```bash
lsusb | grep -i rode
```

Should see: `RODE Wireless GO II`

### Audio Configuration

```yaml
audio:
  microphone:
    device_id: 25  # Replace with actual from device list
    sample_rate: 48000
    channels: 1
    # Downsampling: 48kHz → 16kHz for Riva
    resample_target: 16000
```

## KT USB Speaker Setup

### Device Connection

1. Plug KT speaker into USB port
2. Power on speaker

### Verify Detection

```bash
lsusb | grep -i "KT"
aplay -l | grep -i "usb"
```

### Audio Configuration

```yaml
audio:
  speaker:
    device_id: 26  # Replace with actual from device list
    sample_rate: 48000
    channels: 2
```

## Voice Pipeline Testing

### Test 1: Riva ASR
```bash
python3 << 'EOF'
from riva.client import Client
client = Client('localhost')
# Audio from mic → 16kHz → transcribe
result = client.transcribe_file('test.wav')
print(result)
EOF
```

### Test 2: Bedrock LLM
```bash
python3 << 'EOF'
import boto3
client = boto3.client('bedrock-runtime')
response = client.invoke_model(
    modelId='anthropic.claude-3-haiku-20240307-v1:0',
    body='{"prompt": "Hello, how are you?"}' 
)
print(response)
EOF
```

### Test 3: Riva TTS
```bash
python3 << 'EOF'
from riva.client import Client
client = Client('localhost')
audio = client.synthesize('Hello, this is a test')
# Save audio to file and play
EOF
```

### Test Full Pipeline
```bash
python examples/test_scripts/test_audio_devices.py
python examples/voice_chat/voice_chat_example.py --voice
```

## Troubleshooting

### Riva server not starting
```bash
# Check GPU availability
nvidia-smi

# Check container logs
docker logs <container_id>

# If out of memory, reduce model size
docker run ... -e RIVA_GPU_MEMORY_FRACTION=0.5
```

### AWS Bedrock not responding
```bash
# Check credentials
aws configure list

# Check region
echo $AWS_REGION

# Test connection
aws bedrock list-foundation-models --region us-east-1
```

### Audio not being captured
```bash
# List audio devices
arecord -l

# Check Wireless GO permissions
ls -la /dev/ttyUSB* /dev/ttyACM*

# Try as sudo (temporary)
sudo python examples/test_scripts/test_audio_devices.py
```

## Performance Tuning

### For faster responses
```yaml
voice:
  asr:
    timeout_ms: 20000  # Stop listening faster
  llm:
    max_tokens: 128    # Shorter responses
```

### For better accuracy
```yaml
voice:
  asr:
    timeout_ms: 40000  # Allow longer speech
  llm:
    temperature: 0.3   # More consistent
```

## References

- NVIDIA Riva: https://docs.nvidia.com/deeplearning/riva/user-guide/
- AWS Bedrock: https://docs.aws.amazon.com/bedrock/
- PyAudio: http://people.csail.mit.edu/hubert/pyaudio/
