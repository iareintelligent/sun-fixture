#!/bin/bash

echo "================================================"
echo "   Updating AppDaemon Files from GitHub"
echo "================================================"
echo ""
echo "Enter password 'fortress' when prompted"
echo ""

# Update /config/apps/
echo "📦 Updating /config/apps/ directory..."
ssh root@homeassistant.local "cd /config/apps/ && wget -q -O apps.yaml https://raw.githubusercontent.com/iareintelligent/sun-fixture/main/appdaemon/apps/apps.yaml && wget -q -O celestial.py https://raw.githubusercontent.com/iareintelligent/sun-fixture/main/appdaemon/apps/celestial.py && echo 'Updated /config/apps/'"

echo ""
echo "📦 Checking /addon_configs/ directory..."
ssh root@homeassistant.local "if [ -d /addon_configs/a0d7b954_appdaemon/apps/ ]; then cd /addon_configs/a0d7b954_appdaemon/apps/ && wget -q -O apps.yaml https://raw.githubusercontent.com/iareintelligent/sun-fixture/main/appdaemon/apps/apps.yaml && wget -q -O celestial.py https://raw.githubusercontent.com/iareintelligent/sun-fixture/main/appdaemon/apps/celestial.py && echo 'Updated /addon_configs/'; else echo 'Directory not found'; fi"

echo ""
echo "🔄 Restarting AppDaemon..."
ssh root@homeassistant.local "ha addon restart a0d7b954_appdaemon"

echo ""
echo "✅ Complete! Both directories updated from GitHub."
echo ""
echo "To check logs:"
echo "  ssh root@homeassistant.local 'tail -20 /addon_configs/a0d7b954_appdaemon/logs/appdaemon.log'"