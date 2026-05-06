#!/usr/bin/env python3
"""
Test specifically for Sun area lights and Aurora dimmer
"""

import requests
import json
import time
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

def find_sun_lights():
    """Find all lights with 'sun' in their name"""
    ha_url = os.getenv("HA_URL", "http://homeassistant.local:8123")
    token = os.getenv("HA_TOKEN", "")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(f"{ha_url}/api/states", headers=headers)
    if response.status_code != 200:
        print(f"Failed to get states: {response.status_code}")
        return []
    
    states = response.json()
    sun_lights = []
    
    for state in states:
        entity_id = state["entity_id"]
        if entity_id.startswith("light.") and "sun" in entity_id.lower():
            attrs = state.get("attributes", {})
            friendly_name = attrs.get("friendly_name", entity_id)
            
            # Also check friendly name for direction words
            direction_words = ["north", "south", "east", "west", "ne", "nw", "se", "sw"]
            has_direction = any(word in friendly_name.lower() for word in direction_words)
            
            sun_lights.append({
                "entity_id": entity_id,
                "friendly_name": friendly_name,
                "state": state["state"],
                "has_direction": has_direction,
                "brightness": attrs.get("brightness"),
                "color_temp_kelvin": attrs.get("color_temp_kelvin"),
                "supported_color_modes": attrs.get("supported_color_modes", [])
            })
    
    return sun_lights

def find_recent_aurora_events():
    """Listen for recent hue_event to find Aurora dimmer"""
    ha_url = os.getenv("HA_URL", "http://homeassistant.local:8123")
    token = os.getenv("HA_TOKEN", "")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print("\n🎛️  Checking for recent Aurora dimmer events...")
    print("   Looking for events in the last minute...")
    
    # Get recent events from logbook
    end_time = datetime.now()
    start_time = end_time - timedelta(minutes=5)
    
    params = {
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
    }
    
    response = requests.get(
        f"{ha_url}/api/logbook",
        headers=headers,
        params=params
    )
    
    if response.status_code == 200:
        events = response.json()
        hue_events = []
        
        for event in events:
            if event.get("domain") == "hue" or "hue" in event.get("name", "").lower():
                hue_events.append(event)
        
        if hue_events:
            print(f"   Found {len(hue_events)} Hue-related events:")
            for event in hue_events[-5:]:  # Show last 5
                print(f"     {event.get('when', '')} - {event.get('name', '')} - {event.get('message', '')}")
    
    # Alternative: Check for sensor entities that might track Aurora
    response = requests.get(f"{ha_url}/api/states", headers=headers)
    if response.status_code == 200:
        states = response.json()
        aurora_entities = []
        
        for state in states:
            entity_id = state["entity_id"]
            attrs = state.get("attributes", {})
            friendly_name = attrs.get("friendly_name", "")
            
            # Look for sensors that might be Aurora-related
            if ("aurora" in entity_id.lower() or 
                "aurora" in friendly_name.lower() or
                "dimmer" in entity_id.lower() or
                (entity_id.startswith("sensor.") and "hue" in entity_id.lower())):
                
                aurora_entities.append({
                    "entity_id": entity_id,
                    "friendly_name": friendly_name,
                    "state": state["state"],
                    "last_changed": state.get("last_changed", ""),
                    "attributes": attrs
                })
        
        if aurora_entities:
            print("\n   Potential Aurora-related entities:")
            for entity in aurora_entities:
                print(f"     {entity['entity_id']}: {entity['state']}")
                if entity['last_changed']:
                    print(f"       Last changed: {entity['last_changed']}")

def main():
    print("=" * 60)
    print("🌟 Sun Area Lights Discovery")
    print("=" * 60)
    
    # Find Sun lights
    sun_lights = find_sun_lights()
    
    print(f"\n☀️ Found {len(sun_lights)} Sun area lights:")
    
    # Group by main sun group vs individual directional lights
    main_sun = None
    directional_lights = []
    
    for light in sun_lights:
        if light["entity_id"] == "light.sun":
            main_sun = light
        elif light["has_direction"]:
            directional_lights.append(light)
        else:
            directional_lights.append(light)  # Include anyway
    
    if main_sun:
        print(f"\n📍 Main Sun Group:")
        print(f"   - {main_sun['entity_id']} ({main_sun['friendly_name']})")
        print(f"     State: {main_sun['state']}")
        if main_sun['color_temp_kelvin']:
            print(f"     Current: {main_sun['color_temp_kelvin']}K")
    
    if directional_lights:
        print(f"\n🧭 Directional Sun Lights ({len(directional_lights)}):")
        for light in directional_lights:
            print(f"   - {light['entity_id']} ({light['friendly_name']})")
            print(f"     State: {light['state']}")
            if light['color_temp_kelvin'] and light['state'] == 'on':
                print(f"     Current: {light['color_temp_kelvin']}K @ {light.get('brightness', 'unknown')} brightness")
            print(f"     Color modes: {', '.join(light['supported_color_modes'])}")
    
    # Look for Aurora events
    find_recent_aurora_events()
    
    # Generate suggested configuration
    print("\n" + "=" * 60)
    print("📝 Suggested apps.yaml configuration:")
    print("-" * 60)
    
    light_entities = ["light.sun"]  # Use the main sun group
    
    print(f"""
celestial_lighting:
  module: celestial
  class: CelestialLighting
  
  # Sun area lights (using main group)
  lights:
    - {light_entities[0]}
  
  # Aurora dimmer device ID
  # Check Developer Tools → Events → Listen to "hue_event"
  # Then click/rotate your Aurora to see the device_id
  # aurora_device_id: "00:17:88:01:XX:XX:XX:XX-XX-XXXX"
  
  update_interval: 60
  
  # Your Seattle location (from HA)
  location:
    latitude: 47.6763
    longitude: -122.3233
""")
    
    print("\n✅ Next steps:")
    print("1. Install AppDaemon add-on if not already installed")
    print("2. Find Aurora device ID via Developer Tools → Events")
    print("3. Copy celestial.py to /config/appdaemon/apps/")
    print("4. Copy the suggested configuration to /config/appdaemon/apps/apps.yaml")
    print("5. The app will start automatically!")

if __name__ == "__main__":
    main()