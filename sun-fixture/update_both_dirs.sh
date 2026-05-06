#!/bin/bash

# Update both AppDaemon directories from GitHub
# This ensures both possible locations have the latest code

set -e

echo "================================================"
echo "   Updating Both AppDaemon Directories"
echo "================================================"
echo ""

# Home Assistant connection details
HA_HOST="homeassistant.local"
HA_USER="root"

echo "Updating both potential AppDaemon directories from GitHub..."
echo "You'll be prompted for the password (fortress) multiple times"
echo ""

# Update /config/apps/ directory
echo "📦 Updating /config/apps/ ..."
ssh ${HA_USER}@${HA_HOST} << 'EOF'
cd /config/apps/
echo "Fetching latest files from GitHub..."
wget -q -O apps.yaml https://raw.githubusercontent.com/iareintelligent/sun-fixture/main/sun-fixture/appdaemon/apps/apps.yaml
wget -q -O celestial.py https://raw.githubusercontent.com/iareintelligent/sun-fixture/main/sun-fixture/appdaemon/apps/celestial.py
echo "✅ /config/apps/ updated"
ls -la /config/apps/
EOF

echo ""
echo "📦 Updating /addon_configs/a0d7b954_appdaemon/apps/ ..."
ssh ${HA_USER}@${HA_HOST} << 'EOF'
# Check if directory exists first
if [ -d "/addon_configs/a0d7b954_appdaemon/apps/" ]; then
    cd /addon_configs/a0d7b954_appdaemon/apps/
    echo "Fetching latest files from GitHub..."
    wget -q -O apps.yaml https://raw.githubusercontent.com/iareintelligent/sun-fixture/main/sun-fixture/appdaemon/apps/apps.yaml
    wget -q -O celestial.py https://raw.githubusercontent.com/iareintelligent/sun-fixture/main/sun-fixture/appdaemon/apps/celestial.py
    echo "✅ /addon_configs/a0d7b954_appdaemon/apps/ updated"
    ls -la /addon_configs/a0d7b954_appdaemon/apps/
else
    echo "⚠️  Directory /addon_configs/a0d7b954_appdaemon/apps/ not found"
fi
EOF

echo ""
echo "🔄 Restarting AppDaemon..."
ssh ${HA_USER}@${HA_HOST} << 'EOF'
# Try to restart AppDaemon using the addon
ha addon restart a0d7b954_appdaemon || echo "Could not restart via ha addon command"
EOF

echo ""
echo "✅ Both directories updated with latest code from GitHub!"
echo ""
echo "Next steps:"
echo "  1. Check AppDaemon logs to verify it loaded the new configuration"
echo "  2. Your lights should now use proper 8-direction mapping:"
echo "     N, NE, E, SE, S, SW, W, NW"
echo ""
echo "To check which config is being used:"
echo "  ssh root@homeassistant.local 'grep \"Mapped\" /addon_configs/a0d7b954_appdaemon/logs/appdaemon.log | tail -10'"
echo "================================================"