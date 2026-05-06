#!/bin/bash

# Test script for Celestial Lighting System
# This simulates Aurora dimmer events to test the AppDaemon app

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -E '^HA_' | xargs)
fi

# Check if token is set
if [ -z "$HA_TOKEN" ]; then
    echo "❌ HA_TOKEN not found in .env file"
    echo "Please add your Home Assistant token to .env"
    exit 1
fi

# Install requirements if needed
if ! python3 -c "import websocket" 2>/dev/null; then
    echo "📦 Installing websocket-client..."
    pip3 install websocket-client
fi

echo "================================================"
echo "   Celestial Lighting System - Test Suite"
echo "================================================"
echo ""
echo "This will simulate Aurora dimmer events to test:"
echo "  • Mode cycling (Sun → Moon → Off)"
echo "  • Brightness adjustment via rotation"
echo "  • Light activation patterns"
echo ""
echo "Choose test mode:"
echo "  1) Interactive mode (manual testing)"
echo "  2) Full automated test sequence"
echo ""

read -p "Enter choice (1 or 2): " choice

if [ "$choice" = "2" ]; then
    MODE="full"
else
    MODE="interactive"
fi

echo ""
echo "Starting tests..."
echo "Watch AppDaemon logs in another terminal:"
echo "  ssh root@homeassistant.local 'tail -f /addon_configs/a0d7b954_appdaemon/logs/appdaemon.log | grep celestial'"
echo ""

python3 test_celestial.py \
    --url "$HA_URL" \
    --token "$HA_TOKEN" \
    --mode "$MODE"