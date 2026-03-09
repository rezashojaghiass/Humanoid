# Facial Animation System

This document describes the facial expression and LCD animation system integrated into the Humanoid robot.

## Overview

The facial animation system displays emotions and expressions on an LCD screen using pre-rendered PNG frame sequences. Currently using Blender-generated animation frames with LCD display capability.

## Asset Structure

Facial expression animations are organized by emotion type:

```
assets/facial_expressions/
├── smile/           (30 PNG frames)
├── sad/             (30 PNG frames)
├── surprise/        (30 PNG frames)
├── neutral/         (30 PNG frames)
├── angry/           (30 PNG frames)
└── mouth_positions/
    ├── aa/          (30 frames - mouth open)
    ├── ee/          (30 frames - mouth smile)
    └── oo/          (30 frames - mouth rounded)
```

Each subdirectory contains 30 PNG frames for smooth animation.

## Frame Specifications

- **Format:** PNG (8-bit indexed or 24-bit RGB)
- **Resolution:** 320×240 (typical LCD resolution)
- **Naming:** `frame_000.png`, `frame_001.png`, ... `frame_029.png`
- **Bit depth:** 24-bit RGB recommended for quality
- **Color space:** sRGB
- **Frame rate:** 30 fps (33ms per frame)

## Animation Playback

### Python Implementation

```python
from PIL import Image
import os

class FacialAnimator:
    def __init__(self, emotions_dir):
        self.emotions = {}
        for emotion in os.listdir(emotions_dir):
            frames = []
            emotion_path = os.path.join(emotions_dir, emotion)
            for frame_file in sorted(os.listdir(emotion_path)):
                img = Image.open(os.path.join(emotion_path, frame_file))
                frames.append(img)
            self.emotions[emotion] = frames
    
    def play_emotion(self, emotion, repeat=1, display_func=None):
        """Play emotion animation"""
        frames = self.emotions[emotion]
        for _ in range(repeat):
            for frame in frames:
                if display_func:
                    display_func(frame)
                time.sleep(1/30.0)  # 30 fps
```

### Hardware Drivers

For LCD/OLED displays:
- **LCD Driver:** DMA transfer for smooth 30fps playback
- **GPIO Control:** 5V GPIO for display data
- **SPI/Parallel Interface:** Depends on LCD module

## Blender Workflow

### Character Model Setup

1. **Load Rig:** Open humanoid character rig in Blender
2. **Set Facial Bones:** Armature includes:
   - Jaw rotation
   - Cheek deformation
   - Eye rotation
   - Eyebrow movement

### Creating Expressions

1. **New Action:** Create new animation action for each emotion
2. **Timeline:** Set animation to 30 frames
3. **Bone Keyframes:**
   - Frame 0: Neutral position
   - Frame 10: Expression peak
   - Frame 29: Return to neutral

### Rendering Animation

```blender
# Blender Python Console
import bpy
from bpy.ops import render

scene = bpy.context.scene
scene.render.resolution_x = 320
scene.render.resolution_y = 240
scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = '/path/to/output/frame_'

for frame in range(30):
    scene.frame_set(frame)
    bpy.ops.render.render(write_still=True)
```

### Export Settings

- **Samples:** 32 (or 64 for higher quality)
- **Format:** PNG 24-bit
- **Resolution:** 320×240
- **Frame range:** 0-29
- **Output padding:** 3 digits (frame_000.png)

## Integration with Voice System

When LLM response is processed, emotion is triggered:

```python
def map_text_to_emotion(text):
    """Map LLM response to facial expression"""
    text_lower = text.lower()
    
    emotions = {
        'smile': ['happy', 'great', 'excellent', 'love', 'wonderful'],
        'sad': ['bad', 'sorry', 'sad', 'terrible', 'worst'],
        'surprise': ['wow', 'amazing', 'incredible', 'shocked'],
        'angry': ['wrong', 'hate', 'angry', 'frustrated'],
        'neutral': []  # default
    }
    
    for emotion, keywords in emotions.items():
        if any(kw in text_lower for kw in keywords):
            return emotion
    
    return 'neutral'
```

## Customizing Expressions

### Create Custom Animation

1. **Blender:** Duplicate existing action (e.g., "Smile")
2. **Modify Keyframes:** Change bone rotations for new expression
3. **Render:** Follow export steps above
4. **Organize:** Create new subdirectory in `assets/facial_expressions/`
5. **Update Config:** Add emotion mapping in `config/config.yaml`

### Add New Emotion

```yaml
# config/config.yaml
emotions:
  smile:
    probability: 0.3
    duration_ms: 1000
  confused:
    probability: 0.1
    duration_ms: 1500
  # ... add new emotion
```

## LCD Display Driver

### Common LCD Modules

- **ILI9341:** 320×240, SPI interface
- **ST7789:** 320×240, SPI/parallel
- **HX8357:** 480×320, parallel interface

### Arduino LCD Integration

Example with ILI9341 and SPI:

```cpp
#include <Adafruit_ILI9341.h>
#include <SPI.h>

#define TFT_CS 10
#define TFT_DC 9
#define TFT_MOSI 11
#define TFT_CLK 13

Adafruit_ILI9341 tft = Adafruit_ILI9341(TFT_CS, TFT_DC);

void setup() {
    tft.begin();
}

void displayFrame(uint16_t* frameData) {
    // Write frame data to LCD
    tft.drawRGBBitmap(0, 0, frameData, 320, 240);
}
```

### Frame Transfer Protocol

For large frame files, stream over serial:

```
1. Send command: {"type":"lcd","action":"start_frame","emotion":"smile","frame":0}
2. Send 320×240×2 bytes of raw RGB565 data
3. Send completion: {"type":"lcd","action":"display"}
```

## Performance Considerations

### File Size Optimization

- **Original PNG:** ~500KB per frame
- **Compressed PNG:** ~150KB per frame
- **Indexed color:** ~50KB per frame (lossy)
- **Storage:** 30 frames × 150KB = 4.5MB per emotion

### Memory Usage

- **Frame buffer:** 320×240×2 bytes = 150KB (RGB565)
- **Decompress queue:** 2-3 frames = 450KB
- **Total:** ~600KB for smooth playback

### Optimization Tips

1. **Pre-convert to RGB565:** Reduce file I/O
2. **Compress with 256-color palette:** Use for simple expressions
3. **Stream from SD card:** If SD module available
4. **DMA transfer:** For smooth 30fps playback

## Testing Animation

### Manual Frame Display

```python
from PIL import Image
import time

emotion = 'smile'
for i in range(30):
    frame = Image.open(f'assets/facial_expressions/{emotion}/frame_{i:03d}.png')
    frame.show()
    time.sleep(1/30.0)
```

### Frame Sequence Verification

```bash
# Check frame count
ls assets/facial_expressions/smile/ | wc -l

# Check frame dimensions
identify assets/facial_expressions/smile/frame_000.png

# Convert to video (for preview)
ffmpeg -framerate 30 -i "assets/facial_expressions/smile/frame_%03d.png" \
  -c:v libx264 -pix_fmt yuv420p smile_animation.mp4
```

## Future Enhancements

- [ ] Real-time emotion blending (transition between expressions)
- [ ] Lip sync with voice output
- [ ] Blink animation
- [ ] Eye tracking (if camera added)
- [ ] Full face mesh deformation (instead of rigged model)
- [ ] Dynamic emotion intensity (0-100%)

## Files Reference

- **Blender project:** `assets/blender_files/humanoid_rig.blend`
- **Frame storage:** `assets/facial_expressions/{emotion}/frame_*.png`
- **Display driver:** `src/robot_sync_app/adapters/lcd_adapter.py` (stub)
- **Emotion mapping:** `src/robot_sync_app/application/behavior_planner.py`

## References

- Blender Animation: https://docs.blender.org/manual/en/latest/animation/index.html
- ILI9341 Driver: https://github.com/adafruit/Adafruit_ILI9341
- PIL/Pillow: https://python-pillow.org/

See Also:
- [Voice System Integration](../chatbot_robot/VOICE_SETUP.md)
- [Configuration Examples](../../examples/configurations/CONFIGURATIONS.md)
