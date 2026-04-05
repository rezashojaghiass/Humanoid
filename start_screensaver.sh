#!/bin/bash
# Standalone screensaver startup script for Jetson Xavier
# This script starts xscreensaver on DISPLAY=:0

export DISPLAY=:0

echo "Killing existing xscreensaver processes..."
pkill -9 xscreensaver 2>/dev/null || true
killall -9 xscreensaver 2>/dev/null || true
sleep 1

# Check if config file has bad options and backup it
if [ -f ~/.xscreensaver ] && grep -q "overlayTextFont\|hardwareVideoSync" ~/.xscreensaver 2>/dev/null; then
    echo "Found incompatible options in ~/.xscreensaver, backing up..."
    mv ~/.xscreensaver ~/.xscreensaver.bak.$(date +%s)
fi

echo "Starting screensaver on DISPLAY=:0..."
DISPLAY=:0 /usr/bin/xscreensaver -no-splash > /tmp/xscreensaver.log 2>&1 &
sleep 1

# Verify it's running
echo "Verifying screensaver is running..."
if DISPLAY=:0 xscreensaver-command -time >/dev/null 2>&1; then
    echo "✓ Screensaver started successfully on physical display"
    DISPLAY=:0 xscreensaver-command -time
else
    echo "✗ Screensaver failed to start"
    echo "Error log:"
    cat /tmp/xscreensaver.log
fi
