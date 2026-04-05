#!/bin/bash
# Run Humanoid Robot with Lip-Sync Animation & Facial Expression Mode
# Features: Baseline lip-sync (frames 1,4,9), emotion animations, elbow joint fix, funny mode

set -e  # Exit on any error

# Environment setup
export GTK_DEBUG=""
export G_MESSAGES_DEBUG="fatal-criticals"
export DISPLAY=:0

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Humanoid Robot - Voice Chat with Animation${NC}"
echo -e "${BLUE}══════════════════════════════════════════════════════════${NC}"

# Check required paths
ROBOT_DIR="/home/reza/Humanoid"
CONFIG_FILE="${ROBOT_DIR}/robot_sync_app/config/config_lipsync.yaml"
PYTHON_PATH="${ROBOT_DIR}/robot_sync_app/src"

if [ ! -d "$ROBOT_DIR" ]; then
    echo -e "${RED}✗ Robot directory not found: $ROBOT_DIR${NC}"
    exit 1
fi

if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${RED}✗ Config file not found: $CONFIG_FILE${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Robot directory: $ROBOT_DIR${NC}"
echo -e "${GREEN}✓ Config file: $CONFIG_FILE${NC}"

# Disable Ubuntu apport (crash reporting)
echo -e "${BLUE}Disabling crash reporting...${NC}"
sudo service apport stop 2>/dev/null || true

# ============================================================================
# Start Screensaver (for Jetson Xavier display)
# ============================================================================
# Ensure xscreensaver is running before app starts
# The app will disable it during execution and re-enable it on exit
if command -v xscreensaver &> /dev/null; then
    # Kill any existing instances
    echo -e "${BLUE}Cleaning up any existing xscreensaver processes...${NC}"
    pkill -9 xscreensaver 2>/dev/null || true
    killall -9 xscreensaver 2>/dev/null || true
    sleep 1
    
    # Check if config file has bad options and backup it if needed
    if [ -f ~/.xscreensaver ] && grep -q "overlayTextFont\|hardwareVideoSync" ~/.xscreensaver 2>/dev/null; then
        echo -e "${BLUE}⚠️  Found incompatible options in ~/.xscreensaver, backing up...${NC}"
        mv ~/.xscreensaver ~/.xscreensaver.bak.$(date +%s)
    fi
    
    # Start xscreensaver on physical display :0 (exact working command)
    echo -e "${BLUE}Starting screensaver on DISPLAY=:0...${NC}"
    DISPLAY=:0 /usr/bin/xscreensaver -no-splash > /tmp/xscreensaver.log 2>&1 &
    sleep 1
    
    # Verify it's running
    if DISPLAY=:0 xscreensaver-command -time >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Screensaver started successfully on physical display${NC}"
    else
        echo -e "${RED}✗ Screensaver failed to start${NC}"
        cat /tmp/xscreensaver.log
    fi
else
    echo -e "${BLUE}⚠️  xscreensaver not found (optional)${NC}"
fi

# Log startup info
echo -e "${BLUE}Starting robot with:${NC}"
echo "  - Baseline lip-sync (frames 1, 4, 9)"
echo "  - Facial expression mode (happy, sad, surprised)"
echo "  - Movement mode with elbow joint support"
echo "  - 🎭 FUNNY MODE: Say 'both hands' to trigger fun choreography"
echo "  - Enhanced cursor hiding"
echo "  - Pre-loaded expression animations (zero latency)"
echo ""

# Run the app
cd "$ROBOT_DIR"
PYTHONPATH="$PYTHON_PATH" python3 -m robot_sync_app.main \
    --config "$CONFIG_FILE" \
    --voice --intent chat \
    2>/dev/null

echo -e "${BLUE}Robot session ended${NC}"
