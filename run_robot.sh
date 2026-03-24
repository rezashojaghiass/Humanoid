#!/bin/bash
# Run Humanoid Robot with Lip-Sync Animation
# Suppress Ubuntu error reporting and GTK dialogs
export GTK_DEBUG=""
export G_MESSAGES_DEBUG="fatal-criticals"
export DISPLAY=:0

# Disable Ubuntu apport (crash reporting)
sudo service apport stop 2>/dev/null

# Run the app with enhanced cursor hiding and lip-sync
cd /home/reza/Humanoid
PYTHONPATH=robot_sync_app/src python3 -m robot_sync_app.main \
    --config robot_sync_app/config/config_lipsync.yaml \
    --voice --intent chat \
    2>/dev/null
