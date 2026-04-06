#!/bin/bash
# Run Humanoid Robot with Lip-Sync Animation & Facial Expression Mode

export GTK_DEBUG=""
export G_MESSAGES_DEBUG="fatal-criticals"
export DISPLAY=:0

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Humanoid Robot - Voice Chat with Animation${NC}"
echo -e "${BLUE}══════════════════════════════════════════════════════════${NC}"

# Check required paths
ROBOT_DIR="/home/reza/Humanoid"
CONFIG_FILE="${ROBOT_DIR}/robot_sync_app/config/config_lipsync.yaml"
PYTHON_PATH="${ROBOT_DIR}/robot_sync_app/src"
DISPLAY_ON_SCRIPT="${ROBOT_DIR}/turn_display_on.sh"
DISPLAY_OFF_SCRIPT="${ROBOT_DIR}/turn_display_off.sh"

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
# TURN ON DISPLAY FOR APP
# ============================================================================
if [ -f "$DISPLAY_ON_SCRIPT" ]; then
    echo -e "${BLUE}Turning on display for app...${NC}"
    "$DISPLAY_ON_SCRIPT"
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

# ============================================================================
# RUN THE MAIN APP - This blocks until app exits
# ============================================================================
cd "$ROBOT_DIR"
PYTHONPATH="$PYTHON_PATH" python3 -m robot_sync_app.main \
    --config "$CONFIG_FILE" \
    --voice --intent chat \
    2>/dev/null

# App has exited - execution reaches here only after app closes
echo -e "${BLUE}Robot session ended${NC}"

# ============================================================================
# TURN OFF DISPLAY AFTER APP EXITS
# ============================================================================
# Display is now off to save power
if [ -f "$DISPLAY_OFF_SCRIPT" ]; then
    echo -e "${BLUE}Turning off display (power save mode)...${NC}"
    "$DISPLAY_OFF_SCRIPT"
fi

