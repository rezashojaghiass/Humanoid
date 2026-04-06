#!/bin/bash
# Turn on LCD display and disable screen saver

export DISPLAY=:0

echo "Turning on LCD display..."
xset s off
xset s noblank
xset s reset
echo "✓ LCD display turned ON"
