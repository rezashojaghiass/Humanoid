#!/bin/bash
# Test script to turn LCD display OFF and ON

export DISPLAY=:0

echo "=========================================="
echo "LCD Display Control Test"
echo "=========================================="
echo ""

echo "Step 1: Turning display OFF (blank screen)..."
xset s blank
xset s 1 1
xset s activate
echo "✓ Display is now OFF (blank/black screen)"
echo "   Waiting 3 seconds..."
sleep 3

echo ""
echo "Step 2: Turning display ON..."
xset s off
xset s noblank
xset s reset
echo "✓ Display is now ON"
echo ""

echo "=========================================="
echo "Test complete!"
echo "=========================================="
