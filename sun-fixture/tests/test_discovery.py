#!/usr/bin/env python3
"""
Discovery tests for Celestial Lighting System
These tests connect to Home Assistant to discover and inspect Hue devices
Run these first to understand your system before making any changes
"""

import pytest
import requests
import json
from typing import Dict, List, Any
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class TestHueDiscovery:
    """Test suite for discovering Hue devices and their capabilities"""
    
    @pytest.fixture(scope="class")
    def ha_api(self):
        """Fixture to provide Home Assistant API connection"""
        ha_url = os.getenv("HA_URL", "http://homeassistant.local:8123")
        token = os.getenv("HA_TOKEN", "")
        
        if not token:
            pytest.skip("HA_TOKEN not set in .env file")
        
        return {
            "url": ha_url,
            "headers": {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
        }
    
    def test_connection(self, ha_api):
        """Test 1: Verify we can connect to Home Assistant"""
        response = requests.get(f"{ha_api['url']}/api/", headers=ha_api['headers'])
        assert response.status_code == 200, f"Failed to connect: {response.status_code}"
        
        data = response.json()
        print(f"\n✅ Connected to Home Assistant")
        print(f"   Version: {data.get('version', 'unknown')}")
        print(f"   Message: {data.get('message', '')}")
    
    def test_discover_all_lights(self, ha_api):
        """Test 2: Discover all light entities in Home Assistant"""
        response = requests.get(f"{ha_api['url']}/api/states", headers=ha_api['headers'])
        assert response.status_code == 200, "Failed to get states"
        
        states = response.json()
        lights = [s for s in states if s["entity_id"].startswith("light.")]
        
        print(f"\n💡 Found {len(lights)} total lights:")
        
        # Categorize lights
        hue_lights = []
        other_lights = []
        
        for light in lights:
            entity_id = light["entity_id"]
            attributes = light.get("attributes", {})
            
            # Check if it's a Hue light
            is_hue = (
                "hue" in entity_id.lower() or
                attributes.get("is_hue_group") or
                "philips" in str(attributes.get("manufacturer", "")).lower() or
                "signify" in str(attributes.get("manufacturer", "")).lower()
            )
            
            light_info = {
                "entity_id": entity_id,
                "state": light["state"],
                "friendly_name": attributes.get("friendly_name", entity_id),
                "supported_features": attributes.get("supported_features", 0),
                "supported_color_modes": attributes.get("supported_color_modes", []),
                "manufacturer": attributes.get("manufacturer", "Unknown"),
                "model": attributes.get("model", "Unknown"),
                "is_hue": is_hue
            }
            
            if is_hue:
                hue_lights.append(light_info)
            else:
                other_lights.append(light_info)
        
        # Display Hue lights
        print(f"\n🌉 Hue Lights ({len(hue_lights)}):")
        for light in hue_lights:
            print(f"   - {light['entity_id']}")
            print(f"     Name: {light['friendly_name']}")
            print(f"     State: {light['state']}")
            print(f"     Color modes: {', '.join(light['supported_color_modes'])}")
            print(f"     Model: {light['manufacturer']} {light['model']}")
        
        # Display other lights
        if other_lights:
            print(f"\n💡 Other Lights ({len(other_lights)}):")
            for light in other_lights[:5]:  # Show first 5
                print(f"   - {light['entity_id']} ({light['friendly_name']})")
            if len(other_lights) > 5:
                print(f"   ... and {len(other_lights) - 5} more")
        
        return hue_lights
    
    def test_inspect_hue_light_capabilities(self, ha_api):
        """Test 3: Inspect detailed capabilities of Hue lights"""
        response = requests.get(f"{ha_api['url']}/api/states", headers=ha_api['headers'])
        assert response.status_code == 200, "Failed to get states"
        
        states = response.json()
        lights = [s for s in states if s["entity_id"].startswith("light.")]
        
        # Find first Hue light that's on
        hue_light = None
        for light in lights:
            if light["state"] == "on":
                attrs = light.get("attributes", {})
                if "hue" in light["entity_id"].lower() or attrs.get("is_hue_group"):
                    hue_light = light
                    break
        
        if not hue_light:
            print("\n⚠️  No Hue lights are currently on. Turn one on for detailed inspection.")
            return
        
        print(f"\n🔍 Detailed inspection of: {hue_light['entity_id']}")
        attrs = hue_light["attributes"]
        
        # Display all attributes
        important_attrs = [
            "brightness", "color_mode", "color_temp", "color_temp_kelvin",
            "hs_color", "rgb_color", "xy_color", "min_color_temp_kelvin",
            "max_color_temp_kelvin", "min_mireds", "max_mireds",
            "effect_list", "effect"
        ]
        
        print("\n   Current Settings:")
        for attr in important_attrs:
            if attr in attrs:
                value = attrs[attr]
                if isinstance(value, list) and len(value) > 5:
                    value = f"{value[:3]} ... ({len(value)} items)"
                print(f"     {attr}: {value}")
        
        # Check feature support
        features = attrs.get("supported_features", 0)
        print(f"\n   Supported Features (bitmap: {features}):")
        
        # Feature flags from HA
        SUPPORT_BRIGHTNESS = 1
        SUPPORT_COLOR_TEMP = 2
        SUPPORT_EFFECT = 4
        SUPPORT_COLOR = 16
        SUPPORT_TRANSITION = 32
        
        feature_map = {
            "Brightness": SUPPORT_BRIGHTNESS,
            "Color Temperature": SUPPORT_COLOR_TEMP,
            "Effects": SUPPORT_EFFECT,
            "RGB Color": SUPPORT_COLOR,
            "Transitions": SUPPORT_TRANSITION
        }
        
        for name, flag in feature_map.items():
            supported = "✅" if features & flag else "❌"
            print(f"     {supported} {name}")
    
    def test_find_hue_integration(self, ha_api):
        """Test 4: Find Hue integration configuration"""
        # Try to get config entries
        response = requests.get(f"{ha_api['url']}/api/config/config_entries/entry", 
                              headers=ha_api['headers'])
        
        if response.status_code == 200:
            entries = response.json()
            hue_entries = [e for e in entries if e.get("domain") == "hue"]
            
            if hue_entries:
                print(f"\n🌉 Hue Integration Details:")
                for entry in hue_entries:
                    print(f"   Bridge: {entry.get('title', 'Unknown')}")
                    print(f"   ID: {entry.get('entry_id', 'Unknown')}")
                    print(f"   State: {entry.get('state', 'Unknown')}")
                    
                    # Try to get bridge info
                    data = entry.get("data", {})
                    if "host" in data:
                        print(f"   Host: {data['host']}")
    
    def test_check_sun_integration(self, ha_api):
        """Test 5: Check sun integration and current position"""
        response = requests.get(f"{ha_api['url']}/api/states/sun.sun", 
                              headers=ha_api['headers'])
        
        if response.status_code == 200:
            sun = response.json()
            attrs = sun.get("attributes", {})
            
            print(f"\n☀️ Sun Integration:")
            print(f"   State: {sun['state']}")
            print(f"   Elevation: {attrs.get('elevation', 'Unknown')}°")
            print(f"   Azimuth: {attrs.get('azimuth', 'Unknown')}°")
            print(f"   Rising: {attrs.get('rising', 'Unknown')}")
            
            # Get location for moon calculations
            config_response = requests.get(f"{ha_api['url']}/api/config", 
                                         headers=ha_api['headers'])
            if config_response.status_code == 200:
                config = config_response.json()
                print(f"\n📍 Location:")
                print(f"   Latitude: {config.get('latitude', 'Unknown')}")
                print(f"   Longitude: {config.get('longitude', 'Unknown')}")
                print(f"   Timezone: {config.get('time_zone', 'Unknown')}")
                print(f"   Elevation: {config.get('elevation', 'Unknown')}m")
        else:
            print("\n⚠️  Sun integration not found - this is required for the Celestial Lighting System")
    
    def test_check_appdaemon(self, ha_api):
        """Test 6: Check if AppDaemon is installed and running"""
        # Check for AppDaemon entities or add-on
        response = requests.get(f"{ha_api['url']}/api/states", headers=ha_api['headers'])
        
        if response.status_code == 200:
            states = response.json()
            
            # Look for AppDaemon-related entities
            appdaemon_entities = [
                s for s in states 
                if "appdaemon" in s["entity_id"].lower()
            ]
            
            if appdaemon_entities:
                print(f"\n📦 AppDaemon Status:")
                for entity in appdaemon_entities:
                    print(f"   {entity['entity_id']}: {entity['state']}")
            else:
                print("\n⚠️  AppDaemon entities not found.")
                print("   Check if AppDaemon add-on is installed via:")
                print("   Settings → Add-ons → Add-on Store → Search 'AppDaemon'")
    
    def test_monitor_hue_events(self, ha_api):
        """Test 7: Instructions for monitoring Hue events (manual test)"""
        print("\n🎛️ Aurora Dimmer Event Discovery:")
        print("   To find your Aurora dimmer device ID:")
        print("   1. Open Home Assistant")
        print("   2. Go to Developer Tools → Events")
        print("   3. In 'Listen to events', enter: hue_event")
        print("   4. Click 'Start Listening'")
        print("   5. Click or rotate your Aurora dimmer")
        print("   6. Look for 'device_id' in the event data")
        print("   7. Copy this ID to your apps.yaml configuration")
        print("\n   Example device_id format:")
        print("   00:17:88:01:XX:XX:XX:XX-XX-XXXX")


def run_discovery():
    """Run discovery tests without pytest"""
    tester = TestHueDiscovery()
    
    # Create mock ha_api
    ha_url = os.getenv("HA_URL", "http://homeassistant.local:8123")
    token = os.getenv("HA_TOKEN", "")
    
    if not token:
        print("❌ HA_TOKEN not set in .env file")
        print("   Get a long-lived access token from:")
        print("   Home Assistant → Profile → Security → Long-Lived Access Tokens")
        print("   Then create a .env file with:")
        print("   HA_TOKEN=your-token-here")
        print("   HA_URL=http://homeassistant.local:8123")
        return
    
    ha_api = {
        "url": ha_url,
        "headers": {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    }
    
    print("=" * 60)
    print("🔍 Hue Device Discovery")
    print("=" * 60)
    
    # Run tests in order
    try:
        tester.test_connection(ha_api)
        tester.test_discover_all_lights(ha_api)
        tester.test_inspect_hue_light_capabilities(ha_api)
        tester.test_find_hue_integration(ha_api)
        tester.test_check_sun_integration(ha_api)
        tester.test_check_appdaemon(ha_api)
        tester.test_monitor_hue_events(ha_api)
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("Discovery complete!")


if __name__ == "__main__":
    run_discovery()