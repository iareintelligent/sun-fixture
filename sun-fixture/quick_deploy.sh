#!/bin/bash

echo "Quick deploy to Home Assistant"
echo "Enter password 'fortress' when prompted"
echo ""

ssh root@homeassistant.local << 'EOF'
cd /addon_configs/a0d7b954_appdaemon/apps/
wget -q -O celestial.py https://raw.githubusercontent.com/iareintelligent/sun-fixture/main/appdaemon/apps/celestial.py
echo "✅ Updated celestial.py"
ha addon restart a0d7b954_appdaemon
echo "✅ Restarting AppDaemon..."
EOF

echo ""
echo "Done! The Aurora dimmer should now:"
echo "  • Button press: Cycle between Sun → Moon → Off modes"
echo "  • Rotation: Adjust brightness level"
echo ""
echo "Watch the logs to see it working:"
echo "  ssh root@homeassistant.local 'tail -f /addon_configs/a0d7b954_appdaemon/logs/appdaemon.log'"