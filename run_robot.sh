#!/bin/bash
# Run Humanoid Robot with Lip-Sync Animation & Facial Expression Mode
# Features: Baseline lip-sync (frames 1,4,9), emotion animations, elbow joint fix, funny mode

# Note: set -e is NOT used here because screensaver startup should not block app launch

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
SCREENSAVER_SCRIPT="${ROBOT_DIR}/start_screensaver.sh"

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
# Use the standalone screensaver startup script
# Use || true to prevent screensaver errors from blocking app launch
if [ -f "$SCREENSAVER_SCRIPT" ]; then
    echo -e "${BLUE}Starting screensaver daemon...${NC}"
    bash "$SCREENSAVER_SCRIPT" || true
else
    echo -e "${YELLOW}⚠️  Screensaver script not found: $SCREENSAVER_SCRIPT${NC}"
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
