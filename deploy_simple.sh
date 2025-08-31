#!/bin/bash

# Simple deployment script for Celestial Lighting System
# This version uses expect or manual password entry

set -e

echo "================================================"
echo "   Celestial Lighting System - Simple Deploy"
echo "================================================"
echo ""

# Check for required files
if [ ! -f "appdaemon/apps/celestial.py" ]; then
    echo "❌ celestial.py not found. Are you in the project root?"
    exit 1
fi

echo "📦 Creating AppDaemon directories on Home Assistant..."
echo "   You'll be prompted for the password (fortress) twice"
echo ""

# Create directories
ssh root@homeassistant.local "mkdir -p /config/appdaemon/apps /config/appdaemon/logs"

echo "📤 Copying celestial.py..."
scp appdaemon/apps/celestial.py root@homeassistant.local:/config/appdaemon/apps/

echo "📤 Copying apps.yaml..."
scp appdaemon/apps/apps.yaml root@homeassistant.local:/config/appdaemon/apps/

echo ""
echo "✅ Deployment complete!"
echo ""
echo "Next steps:"
echo "  1. Check AppDaemon logs: /config/appdaemon/logs/appdaemon.log"
echo "  2. Restart AppDaemon from HA UI if needed"
echo "  3. Your lights should start responding to celestial positions!"
echo ""
echo "To view logs:"
echo "  ssh root@homeassistant.local 'tail -f /config/appdaemon/logs/appdaemon.log'"
echo "================================================"