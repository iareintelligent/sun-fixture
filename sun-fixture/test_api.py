#!/usr/bin/env python3
"""
Test script for Celestial Lighting System
Uses Home Assistant REST API to test light control logic locally
"""

import requests
import json
import time
import ephem
import math
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class CelestialLightingTester:
    """Test harness for celestial lighting calculations and HA API calls"""
    
    def __init__(self, ha_url: str = None, token: str = None):
        """Initialize the tester with HA connection details"""
        self.ha_url = ha_url or os.getenv("HA_URL", "http://homeassistant.local:8123")
        self.token = token or os.getenv("HA_TOKEN", "")
        
        if not self.token:
            print("⚠️  WARNING: No HA_TOKEN found. Set it in .env file or pass as parameter")
            print("   Get a long-lived access token from:")
            print("   Home Assistant → Profile → Security → Long-Lived Access Tokens")
        
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        # Default location (San Francisco) - will be updated from HA
        self.latitude = 37.7749
        self.longitude = -122.4194
        
        # Set up ephem observer
        self.observer = ephem.Observer()
        self.observer.lat = str(self.latitude)
        self.observer.lon = str(self.longitude)
    
    def test_connection(self) -> bool:
        """Test connection to Home Assistant"""
        try:
            response = requests.get(f"{self.ha_url}/api/", headers=self.headers)
            if response.status_code == 200:
                print(f"✅ Connected to Home Assistant: {response.json()['message']}")
                return True
            else:
                print(f"❌ Failed to connect: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False
    
    def get_sun_state(self) -> Dict:
        """Get current sun state from Home Assistant"""
        try:
            response = requests.get(
                f"{self.ha_url}/api/states/sun.sun",
                headers=self.headers
            )
            if response.status_code == 200:
                data = response.json()
                return {
                    "state": data["state"],
                    "elevation": float(data["attributes"]["elevation"]),
                    "azimuth": float(data["attributes"]["azimuth"]),
                    "rising": data["attributes"]["rising"]
                }
            return None
        except Exception as e:
            print(f"Error getting sun state: {e}")
            return None
    
    def get_location(self) -> Tuple[float, float]:
        """Get location from Home Assistant configuration"""
        try:
            response = requests.get(
                f"{self.ha_url}/api/config",
                headers=self.headers
            )
            if response.status_code == 200:
                data = response.json()
                self.latitude = data["latitude"]
                self.longitude = data["longitude"]
                self.observer.lat = str(self.latitude)
                self.observer.lon = str(self.longitude)
                return self.latitude, self.longitude
            return self.latitude, self.longitude
        except Exception as e:
            print(f"Error getting location: {e}")
            return self.latitude, self.longitude
    
    def calculate_sun_color_temperature(self, elevation: float) -> int:
        """Calculate color temperature in Kelvin based on sun elevation"""
        elevation = max(-10, min(90, elevation))
        kelvin = int(2000 + (elevation + 10) * 45)
        return min(6500, max(2000, kelvin))
    
    def calculate_sun_brightness(self, elevation: float) -> float:
        """Calculate brightness percentage based on sun elevation"""
        elevation = max(-10, min(90, elevation))
        if elevation <= 0:
            return 20.0
        else:
            return 20 + (80 * (elevation / 90))
    
    def get_moon_position(self) -> Dict[str, float]:
        """Calculate current moon position and phase using ephem"""
        self.observer.date = ephem.now()
        moon = ephem.Moon()
        moon.compute(self.observer)
        
        altitude = math.degrees(moon.alt)
        azimuth = math.degrees(moon.az)
        phase = moon.phase
        
        return {
            "altitude": altitude,
            "azimuth": azimuth,
            "phase": phase,
            "illumination": phase
        }
    
    def calculate_moon_color(self, altitude: float, phase: float) -> List[int]:
        """Calculate RGB color based on moon altitude and phase"""
        if altitude > 30:
            base_r, base_g, base_b = 200, 210, 255
        elif altitude > 0:
            base_r, base_g, base_b = 255, 240, 220
        else:
            base_r, base_g, base_b = 255, 200, 150
        
        intensity = phase / 100
        r = int(base_r * (0.3 + 0.7 * intensity))
        g = int(base_g * (0.3 + 0.7 * intensity))
        b = int(base_b * (0.3 + 0.7 * intensity))
        
        return [min(255, r), min(255, g), min(255, b)]
    
    def calculate_moon_brightness(self, altitude: float, illumination: float) -> float:
        """Calculate brightness percentage based on moon altitude and illumination"""
        if altitude < 0:
            return 5.0
        
        base_brightness = 5 + (illumination * 0.4)
        altitude_factor = min(1.0, altitude / 45)
        
        return base_brightness * (0.5 + 0.5 * altitude_factor)
    
    def get_lights(self) -> List[str]:
        """Get all light entities from Home Assistant"""
        try:
            response = requests.get(
                f"{self.ha_url}/api/states",
                headers=self.headers
            )
            if response.status_code == 200:
                states = response.json()
                lights = [s["entity_id"] for s in states if s["entity_id"].startswith("light.")]
                return lights
            return []
        except Exception as e:
            print(f"Error getting lights: {e}")
            return []
    
    def control_light(self, entity_id: str, **kwargs) -> bool:
        """Control a light via HA API"""
        try:
            data = {"entity_id": entity_id}
            data.update(kwargs)
            
            response = requests.post(
                f"{self.ha_url}/api/services/light/turn_on",
                headers=self.headers,
                json=data
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Error controlling light: {e}")
            return False
    
    def test_sun_lighting(self):
        """Test sun-based lighting calculations"""
        print("\n🌞 Testing Sun Lighting")
        print("-" * 40)
        
        # Get current sun state
        sun_state = self.get_sun_state()
        if not sun_state:
            print("Could not get sun state")
            return
        
        elevation = sun_state["elevation"]
        print(f"Sun elevation: {elevation:.1f}°")
        print(f"Sun state: {sun_state['state']}")
        
        # Calculate lighting parameters
        kelvin = self.calculate_sun_color_temperature(elevation)
        brightness_pct = self.calculate_sun_brightness(elevation)
        brightness = int(brightness_pct * 255 / 100)
        
        print(f"Color temperature: {kelvin}K")
        print(f"Brightness: {brightness_pct:.1f}% ({brightness}/255)")
        
        return {
            "kelvin": kelvin,
            "brightness": brightness,
            "transition": 5
        }
    
    def test_moon_lighting(self):
        """Test moon-based lighting calculations"""
        print("\n🌙 Testing Moon Lighting")
        print("-" * 40)
        
        # Get moon position
        moon_data = self.get_moon_position()
        altitude = moon_data["altitude"]
        phase = moon_data["phase"]
        
        print(f"Moon altitude: {altitude:.1f}°")
        print(f"Moon phase: {phase:.1f}%")
        
        # Calculate lighting parameters
        rgb = self.calculate_moon_color(altitude, phase)
        brightness_pct = self.calculate_moon_brightness(altitude, phase)
        brightness = int(brightness_pct * 255 / 100)
        
        print(f"RGB color: {rgb}")
        print(f"Brightness: {brightness_pct:.1f}% ({brightness}/255)")
        
        return {
            "rgb_color": rgb,
            "brightness": brightness,
            "transition": 5
        }
    
    def run_full_test(self, apply_to_lights: bool = False):
        """Run a complete test of the celestial lighting system"""
        print("\n" + "=" * 50)
        print("🌟 Celestial Lighting System Test")
        print("=" * 50)
        
        # Test connection
        if not self.test_connection():
            return
        
        # Get location
        lat, lon = self.get_location()
        print(f"\n📍 Location: {lat:.4f}, {lon:.4f}")
        
        # Get available lights
        lights = self.get_lights()
        print(f"\n💡 Found {len(lights)} lights:")
        for light in lights[:5]:  # Show first 5
            print(f"   - {light}")
        if len(lights) > 5:
            print(f"   ... and {len(lights) - 5} more")
        
        # Test sun/moon calculations
        sun_state = self.get_sun_state()
        if sun_state and sun_state["elevation"] > -10:
            # Daytime mode
            params = self.test_sun_lighting()
            mode = "SUN"
        else:
            # Nighttime mode
            params = self.test_moon_lighting()
            mode = "MOON"
        
        # Apply to lights if requested
        if apply_to_lights and lights and params:
            print(f"\n🎨 Applying {mode} lighting to lights...")
            test_lights = lights[:3]  # Only test on first 3 lights
            for light in test_lights:
                if self.control_light(light, **params):
                    print(f"   ✅ {light}")
                else:
                    print(f"   ❌ {light}")
        
        print("\n" + "=" * 50)
        print("Test complete!")
    
    def simulate_day_cycle(self, speed: int = 10):
        """Simulate a full day cycle for testing"""
        print("\n🔄 Simulating Day Cycle")
        print(f"Speed: {speed}x")
        print("Press Ctrl+C to stop")
        print("-" * 40)
        
        try:
            while True:
                # Get current celestial positions
                sun_state = self.get_sun_state()
                moon_data = self.get_moon_position()
                
                if sun_state:
                    sun_elev = sun_state["elevation"]
                    
                    # Determine mode and calculate parameters
                    if sun_elev > -10:
                        kelvin = self.calculate_sun_color_temperature(sun_elev)
                        brightness = self.calculate_sun_brightness(sun_elev)
                        print(f"☀️  Sun: {sun_elev:+6.1f}° | {kelvin}K @ {brightness:.0f}%")
                    else:
                        moon_alt = moon_data["altitude"]
                        phase = moon_data["phase"]
                        rgb = self.calculate_moon_color(moon_alt, phase)
                        brightness = self.calculate_moon_brightness(moon_alt, phase)
                        print(f"🌙 Moon: {moon_alt:+6.1f}° | RGB{rgb} @ {brightness:.0f}% (phase: {phase:.0f}%)")
                
                time.sleep(60 / speed)  # Update based on speed multiplier
                
        except KeyboardInterrupt:
            print("\nSimulation stopped")


def main():
    """Main entry point for testing"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Celestial Lighting System")
    parser.add_argument("--url", help="Home Assistant URL", default=None)
    parser.add_argument("--token", help="Home Assistant token", default=None)
    parser.add_argument("--apply", action="store_true", help="Apply changes to actual lights")
    parser.add_argument("--simulate", type=int, help="Simulate day cycle at Nx speed", default=0)
    
    args = parser.parse_args()
    
    # Create tester
    tester = CelestialLightingTester(args.url, args.token)
    
    if args.simulate:
        tester.simulate_day_cycle(args.simulate)
    else:
        tester.run_full_test(args.apply)


if __name__ == "__main__":
    main()