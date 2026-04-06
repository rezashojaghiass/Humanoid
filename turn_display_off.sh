#!/bin/bash
# Turn off LCD display by blanking the screen

export DISPLAY=:0

echo "Turning off LCD display (blank screen)..."
xset s blank
xset s 5 5
xset s activate
echo "✓ LCD display turned OFF (screen blanked)"
