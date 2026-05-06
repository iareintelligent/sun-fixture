#!/usr/bin/env python3
"""
Local Test Server for Celestial Lighting Visualization
Run this to test the UI locally without Home Assistant

Usage:
    python local_test_server.py
    
Then open: http://localhost:5050
"""

import asyncio
import json
import math
import os
from datetime import datetime
from aiohttp import web, ClientSession
import ephem
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class HomeAssistantClient:
    """Client for connecting to real Home Assistant instance"""
    
    def __init__(self):
        self.url = os.getenv("HA_URL", "http://homeassistant.local:8123")
        self.token = os.getenv("HA_TOKEN", "")
        self.connected = False
        self.session = None
        self.last_error = None
        
        # Light configuration matching apps.yaml
        self.directional_lights = {
            "N": "light.sun_north",
            "NE": "light.sun_nnw_bulb_2",
            "E": "light.sun_e_bulb",
            "SE": "light.sun_ssw_bulb",
            "S": "light.sun_s_bulb",
            "SW": "light.sun_ssw_bulb_2",
            "W": "light.sun_west_bulb",
            "NW": "light.sun_nnw_bulb"
        }
        
        self.direction_azimuths = {
            "N": 0, "NE": 45, "E": 90, "SE": 135,
            "S": 180, "SW": 225, "W": 270, "NW": 315
        }
    
    def has_credentials(self):
        """Check if HA credentials are configured"""
        return bool(self.url and self.token)
    
    async def connect(self):
        """Attempt to connect to Home Assistant"""
        if not self.has_credentials():
            self.last_error = "No credentials configured in .env file"
            return False
        
        try:
            self.session = ClientSession()
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
            
            # Test connection by getting API status
            async with self.session.get(
                f"{self.url}/api/",
                headers=headers,
                timeout=5
            ) as response:
                if response.status == 200:
                    self.connected = True
                    self.last_error = None
                    return True
                else:
                    self.last_error = f"HTTP {response.status}: {await response.text()}"
                    await self.session.close()
                    self.session = None
                    return False
        except Exception as e:
            self.last_error = str(e)
            if self.session:
                await self.session.close()
                self.session = None
            return False
    
    async def disconnect(self):
        """Disconnect from Home Assistant"""
        if self.session:
            await self.session.close()
            self.session = None
        self.connected = False
    
    async def get_state(self, entity_id: str):
        """Get state of an entity"""
        if not self.connected or not self.session:
            return None
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            async with self.session.get(
                f"{self.url}/api/states/{entity_id}",
                headers=headers,
                timeout=5
            ) as response:
                if response.status == 200:
                    return await response.json()
                return None
        except:
            return None
    
    async def call_service(self, domain: str, service: str, data: dict):
        """Call a Home Assistant service"""
        if not self.connected or not self.session:
            return False
        
        try:
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
            async with self.session.post(
                f"{self.url}/api/services/{domain}/{service}",
                headers=headers,
                json=data,
                timeout=5
            ) as response:
                return response.status == 200
        except:
            return False
    
    def kelvin_to_rgb(self, kelvin: int) -> list:
        """Convert color temperature in Kelvin to RGB values"""
        temp = kelvin / 100
        
        if temp <= 66:
            red = 255
        else:
            red = temp - 60
            red = 329.698727446 * (red ** -0.1332047592)
            red = max(0, min(255, red))
        
        if temp <= 66:
            green = temp
            green = 99.4708025861 * math.log(green) - 161.1195681661
        else:
            green = temp - 60
            green = 288.1221695283 * (green ** -0.0755148492)
        green = max(0, min(255, green))
        
        if temp >= 66:
            blue = 255
        elif temp <= 19:
            blue = 0
        else:
            blue = temp - 10
            blue = 138.5177312231 * math.log(blue) - 305.0447927307
            blue = max(0, min(255, blue))
        
        return [int(red), int(green), int(blue)]
    
    async def apply_mode(self, mode: str):
        """Apply a lighting mode to the real lights"""
        if not self.connected:
            return False
        
        if mode == "off":
            # Turn off all lights
            for entity_id in self.directional_lights.values():
                await self.call_service("light", "turn_off", {"entity_id": entity_id})
            return True
        
        # Get sun position for calculations
        sun_state = await self.get_state("sun.sun")
        if not sun_state:
            return False
        
        sun_elevation = float(sun_state.get("attributes", {}).get("elevation", 0))
        sun_azimuth = float(sun_state.get("attributes", {}).get("azimuth", 0))
        
        if mode == "sun":
            # Calculate and apply sun-based lighting
            kelvin = self.calculate_sun_color_temperature(sun_elevation)
            base_brightness_pct = self.calculate_sun_brightness(sun_elevation)
            
            for direction, entity_id in self.directional_lights.items():
                light_azimuth = self.direction_azimuths[direction]
                alignment = self.calculate_azimuth_alignment(light_azimuth, sun_azimuth)
                brightness = int((base_brightness_pct * alignment / 100) * 255)
                
                if brightness > 0:
                    await self.call_service("light", "turn_on", {
                        "entity_id": entity_id,
                        "kelvin": kelvin,
                        "brightness": brightness,
                        "transition": 1
                    })
                else:
                    await self.call_service("light", "turn_off", {"entity_id": entity_id})
        
        elif mode == "moon":
            # Moon mode - only light closest bulb
            # Get moon position
            observer = ephem.Observer()
            observer.lat = "47.6763"
            observer.lon = "-122.3233"
            observer.date = ephem.now()
            moon = ephem.Moon()
            moon.compute(observer)
            moon_azimuth = math.degrees(moon.az)
            
            # Find closest light
            closest_light = None
            best_diff = 360
            for direction, entity_id in self.directional_lights.items():
                light_azimuth = self.direction_azimuths[direction]
                diff = abs(light_azimuth - moon_azimuth)
                if diff > 180:
                    diff = 360 - diff
                if diff < best_diff:
                    best_diff = diff
                    closest_light = entity_id
            
            # Turn on closest, turn off others
            for entity_id in self.directional_lights.values():
                if entity_id == closest_light:
                    await self.call_service("light", "turn_on", {
                        "entity_id": entity_id,
                        "rgb_color": [230, 235, 255],
                        "brightness": 102,  # 40%
                        "transition": 1
                    })
                else:
                    await self.call_service("light", "turn_off", {"entity_id": entity_id})
        
        return True
    
    def calculate_azimuth_alignment(self, light_azimuth: float, celestial_azimuth: float) -> float:
        """Calculate alignment factor (0-1) based on azimuth difference"""
        diff = abs(light_azimuth - celestial_azimuth)
        if diff > 180:
            diff = 360 - diff
        
        if diff <= 15:
            return 1.0
        elif diff <= 45:
            return 0.85 - ((diff - 15) / 30) * 0.35
        elif diff <= 90:
            return 0.50 - ((diff - 45) / 45) * 0.35
        else:
            return max(0.01, 0.15 - ((diff - 90) / 90) * 0.14)
    
    def calculate_sun_color_temperature(self, elevation: float) -> int:
        """Calculate color temperature based on sun elevation"""
        elevation = max(-10, min(90, elevation))
        if elevation < 0:
            return 2000
        elif elevation < 5:
            return int(2000 + (elevation / 5) * 1000)
        elif elevation < 15:
            return int(3000 + ((elevation - 5) / 10) * 1000)
        elif elevation < 45:
            return int(4000 + ((elevation - 15) / 30) * 1500)
        else:
            return min(6500, int(5500 + ((elevation - 45) / 45) * 1000))
    
    def calculate_sun_brightness(self, elevation: float) -> float:
        """Calculate brightness percentage based on sun elevation"""
        elevation = max(-10, min(90, elevation))
        if elevation <= 0:
            return 30.0
        elif elevation <= 15:
            return 30 + (30 * (elevation / 15))
        elif elevation <= 45:
            return 60 + (30 * ((elevation - 15) / 30))
        else:
            return 90 + (10 * ((elevation - 45) / 45))

    async def get_full_state(self):
        """Get current state of all lights from Home Assistant"""
        if not self.connected:
            return None
        
        lights = []
        sun_state = await self.get_state("sun.sun")
        
        sun_elevation = 0
        sun_azimuth = 0
        if sun_state:
            sun_elevation = float(sun_state.get("attributes", {}).get("elevation", 0))
            sun_azimuth = float(sun_state.get("attributes", {}).get("azimuth", 0))
        
        for direction, entity_id in self.directional_lights.items():
            state_data = await self.get_state(entity_id)
            light_azimuth = self.direction_azimuths[direction]
            
            if state_data:
                attrs = state_data.get("attributes", {})
                state = state_data.get("state", "off")
                brightness = attrs.get("brightness", 0) or 0
                
                # Get color temp
                color_temp = attrs.get("color_temp")
                kelvin = 4000
                if color_temp:
                    try:
                        kelvin = int(1000000 / color_temp)
                    except:
                        pass
                
                # Get RGB
                rgb = attrs.get("rgb_color")
                if not rgb:
                    rgb = self.kelvin_to_rgb(kelvin)
                else:
                    rgb = list(rgb)
                
                lights.append({
                    "entity_id": entity_id,
                    "state": state,
                    "brightness": brightness,
                    "brightness_pct": int((brightness / 255) * 100) if brightness else 0,
                    "kelvin": kelvin,
                    "rgb": rgb,
                    "azimuth": light_azimuth,
                    "direction": direction
                })
            else:
                # Entity not found
                lights.append({
                    "entity_id": entity_id,
                    "state": "unavailable",
                    "brightness": 0,
                    "brightness_pct": 0,
                    "kelvin": 4000,
                    "rgb": [100, 100, 100],
                    "azimuth": light_azimuth,
                    "direction": direction
                })
        
        return {
            "lights": lights,
            "celestial": {
                "mode": "live",
                "sun": {
                    "elevation": sun_elevation,
                    "azimuth": sun_azimuth
                },
                "timestamp": datetime.now().isoformat()
            },
            "config": {
                "latitude": 47.6763,
                "longitude": -122.3233
            },
            "connection": {
                "connected": True,
                "url": self.url
            }
        }


class MockCelestialSystem:
    """Simulates the celestial lighting system state"""
    
    def __init__(self):
        # Light configuration matching apps.yaml
        self.directional_lights = {
            "N": "light.sun_north",
            "NE": "light.sun_nnw_bulb_2",
            "E": "light.sun_e_bulb",
            "SE": "light.sun_ssw_bulb",
            "S": "light.sun_s_bulb",
            "SW": "light.sun_ssw_bulb_2",
            "W": "light.sun_west_bulb",
            "NW": "light.sun_nnw_bulb"
        }
        
        # Direction to azimuth mapping
        self.direction_azimuths = {
            "N": 0, "NE": 45, "E": 90, "SE": 135,
            "S": 180, "SW": 225, "W": 270, "NW": 315
        }
        
        # Location (Seattle)
        self.latitude = 47.6763
        self.longitude = -122.3233
        
        # State
        self.lighting_mode = "sun"  # sun, moon, off
        self.manual_sun_azimuth = None  # For manual override
        self.manual_sun_elevation = None
        
        # Set up ephem observer
        self.observer = ephem.Observer()
        self.observer.lat = str(self.latitude)
        self.observer.lon = str(self.longitude)
    
    def cycle_mode(self):
        """Cycle through modes: sun -> moon -> on -> off -> sun"""
        modes = ["sun", "moon", "on", "off"]
        current_index = modes.index(self.lighting_mode) if self.lighting_mode in modes else 0
        self.lighting_mode = modes[(current_index + 1) % len(modes)]
        return self.lighting_mode
    
    def set_mode(self, mode):
        """Set specific mode"""
        if mode in ["sun", "moon", "on", "off"]:
            self.lighting_mode = mode
    
    def get_sun_position(self):
        """Get real sun position based on current time"""
        self.observer.date = ephem.now()
        sun = ephem.Sun()
        sun.compute(self.observer)
        
        elevation = math.degrees(sun.alt)
        azimuth = math.degrees(sun.az)
        
        return {
            "elevation": elevation,
            "azimuth": azimuth
        }
    
    def get_moon_position(self):
        """Get real moon position based on current time"""
        self.observer.date = ephem.now()
        moon = ephem.Moon()
        moon.compute(self.observer)
        
        return {
            "altitude": math.degrees(moon.alt),
            "azimuth": math.degrees(moon.az),
            "phase": moon.phase,
            "illumination": moon.phase
        }
    
    def calculate_azimuth_alignment(self, light_azimuth: float, celestial_azimuth: float) -> float:
        """Calculate alignment factor (0-1) based on azimuth difference"""
        diff = abs(light_azimuth - celestial_azimuth)
        if diff > 180:
            diff = 360 - diff
        
        if diff <= 15:
            alignment = 1.0
        elif diff <= 30:
            alignment = 1.0 - ((diff - 15) / 15) * 0.15
        elif diff <= 45:
            alignment = 0.85 - ((diff - 30) / 15) * 0.20
        elif diff <= 60:
            alignment = 0.65 - ((diff - 45) / 15) * 0.20
        elif diff <= 75:
            alignment = 0.45 - ((diff - 60) / 15) * 0.17
        elif diff <= 90:
            alignment = 0.28 - ((diff - 75) / 15) * 0.13
        elif diff <= 105:
            alignment = 0.15 - ((diff - 90) / 15) * 0.07
        elif diff <= 120:
            alignment = 0.08 - ((diff - 105) / 15) * 0.04
        elif diff <= 135:
            alignment = 0.04 - ((diff - 120) / 15) * 0.02
        elif diff <= 150:
            alignment = 0.02 - ((diff - 135) / 15) * 0.01
        else:
            alignment = 0.01
        
        return alignment
    
    def calculate_sun_color_temperature(self, elevation: float) -> int:
        """Calculate color temperature in Kelvin based on sun elevation"""
        elevation = max(-10, min(90, elevation))
        
        if elevation < 0:
            kelvin = 2000
        elif elevation < 5:
            kelvin = int(2000 + (elevation / 5) * 1000)
        elif elevation < 15:
            kelvin = int(3000 + ((elevation - 5) / 10) * 1000)
        elif elevation < 45:
            kelvin = int(4000 + ((elevation - 15) / 30) * 1500)
        else:
            kelvin = int(5500 + ((elevation - 45) / 45) * 1000)
        
        return min(6500, max(2000, kelvin))
    
    def calculate_sun_brightness(self, elevation: float) -> float:
        """Calculate brightness percentage based on sun elevation"""
        elevation = max(-10, min(90, elevation))
        
        if elevation <= 0:
            return 30.0
        elif elevation <= 15:
            return 30 + (30 * (elevation / 15))
        elif elevation <= 45:
            return 60 + (30 * ((elevation - 15) / 30))
        else:
            return 90 + (10 * ((elevation - 45) / 45))
    
    def kelvin_to_rgb(self, kelvin: int) -> list:
        """Convert color temperature in Kelvin to RGB values"""
        temp = kelvin / 100
        
        if temp <= 66:
            red = 255
        else:
            red = temp - 60
            red = 329.698727446 * (red ** -0.1332047592)
            red = max(0, min(255, red))
        
        if temp <= 66:
            green = temp
            green = 99.4708025861 * math.log(green) - 161.1195681661
        else:
            green = temp - 60
            green = 288.1221695283 * (green ** -0.0755148492)
        green = max(0, min(255, green))
        
        if temp >= 66:
            blue = 255
        elif temp <= 19:
            blue = 0
        else:
            blue = temp - 10
            blue = 138.5177312231 * math.log(blue) - 305.0447927307
            blue = max(0, min(255, blue))
        
        return [int(red), int(green), int(blue)]
    
    def calculate_moon_color(self, altitude: float, phase: float) -> list:
        """Calculate RGB color based on moon altitude"""
        if altitude > 45:
            base_r, base_g, base_b = 230, 235, 255
        elif altitude > 15:
            base_r, base_g, base_b = 240, 245, 255
        elif altitude > 0:
            base_r, base_g, base_b = 250, 245, 235
        else:
            base_r, base_g, base_b = 255, 230, 200
        
        intensity = 0.6 + 0.4 * (phase / 100)
        return [
            min(255, int(base_r * intensity)),
            min(255, int(base_g * intensity)),
            min(255, int(base_b * intensity))
        ]
    
    def get_state(self):
        """Get current state of the system"""
        sun_pos = self.get_sun_position()
        moon_pos = self.get_moon_position()
        
        # Use manual override if set, otherwise real position
        sun_azimuth = self.manual_sun_azimuth if self.manual_sun_azimuth is not None else sun_pos["azimuth"]
        sun_elevation = self.manual_sun_elevation if self.manual_sun_elevation is not None else sun_pos["elevation"]
        
        lights = []
        
        for direction, entity_id in self.directional_lights.items():
            light_azimuth = self.direction_azimuths[direction]
            
            if self.lighting_mode == "off":
                # All lights off
                lights.append({
                    "entity_id": entity_id,
                    "state": "off",
                    "brightness": 0,
                    "brightness_pct": 0,
                    "kelvin": 4000,
                    "rgb": [50, 50, 50],
                    "azimuth": light_azimuth,
                    "direction": direction
                })
            elif self.lighting_mode == "on":
                # On mode - all lights on at neutral white, no updates
                lights.append({
                    "entity_id": entity_id,
                    "state": "on",
                    "brightness": 255,
                    "brightness_pct": 100,
                    "kelvin": 4000,
                    "rgb": [255, 240, 220],
                    "azimuth": light_azimuth,
                    "direction": direction
                })
            elif self.lighting_mode == "sun":
                # Sun mode - directional brightness
                alignment = self.calculate_azimuth_alignment(light_azimuth, sun_azimuth)
                base_brightness_pct = self.calculate_sun_brightness(sun_elevation)
                brightness_pct = int(base_brightness_pct * alignment)
                brightness = int(brightness_pct * 255 / 100)
                kelvin = self.calculate_sun_color_temperature(sun_elevation)
                rgb = self.kelvin_to_rgb(kelvin)
                
                lights.append({
                    "entity_id": entity_id,
                    "state": "on" if brightness > 0 else "off",
                    "brightness": brightness,
                    "brightness_pct": brightness_pct,
                    "kelvin": kelvin,
                    "rgb": rgb,
                    "azimuth": light_azimuth,
                    "direction": direction
                })
            else:
                # Moon mode - only closest light on
                diff = abs(light_azimuth - moon_pos["azimuth"])
                if diff > 180:
                    diff = 360 - diff
                
                # Find if this is the closest light
                is_closest = True
                for other_dir, other_azimuth in self.direction_azimuths.items():
                    other_diff = abs(other_azimuth - moon_pos["azimuth"])
                    if other_diff > 180:
                        other_diff = 360 - other_diff
                    if other_diff < diff:
                        is_closest = False
                        break
                
                if is_closest:
                    brightness = int(255 * 0.4)
                    brightness_pct = 40
                    rgb = self.calculate_moon_color(moon_pos["altitude"], moon_pos["phase"])
                    state = "on"
                else:
                    brightness = 0
                    brightness_pct = 0
                    rgb = [50, 50, 50]
                    state = "off"
                
                lights.append({
                    "entity_id": entity_id,
                    "state": state,
                    "brightness": brightness,
                    "brightness_pct": brightness_pct,
                    "kelvin": 4000,
                    "rgb": rgb,
                    "azimuth": light_azimuth,
                    "direction": direction
                })
        
        return {
            "lights": lights,
            "celestial": {
                "mode": self.lighting_mode,
                "sun": {
                    "elevation": sun_elevation,
                    "azimuth": sun_azimuth
                },
                "moon": moon_pos,
                "timestamp": datetime.now().isoformat()
            },
            "config": {
                "latitude": self.latitude,
                "longitude": self.longitude
            }
        }


# Global instances
mock_system = MockCelestialSystem()
ha_client = HomeAssistantClient()


async def handle_index(request):
    """Serve the main visualization page"""
    return web.FileResponse('./local_test_ui.html')


async def handle_api_state(request):
    """API endpoint for current state"""
    # If connected to HA, get real state
    if ha_client.connected:
        state = await ha_client.get_full_state()
        if state:
            return web.json_response(state)
    
    # Fall back to mock state
    state = mock_system.get_state()
    state["connection"] = {
        "connected": False,
        "has_credentials": ha_client.has_credentials(),
        "url": ha_client.url if ha_client.has_credentials() else None,
        "error": ha_client.last_error
    }
    return web.json_response(state)


async def handle_api_mode(request):
    """API endpoint to change mode"""
    data = await request.json()
    action = data.get("action", "cycle")
    
    if action == "cycle":
        new_mode = mock_system.cycle_mode()
        # If connected to HA, control lights directly
        if ha_client.connected:
            await ha_client.apply_mode(new_mode)
    elif action == "set":
        mode = data.get("mode", "sun")
        mock_system.set_mode(mode)
        new_mode = mock_system.lighting_mode
        if ha_client.connected:
            await ha_client.apply_mode(new_mode)
    
    return web.json_response({"mode": new_mode})


async def handle_api_sun_position(request):
    """API endpoint to manually set sun position (for testing)"""
    data = await request.json()
    mock_system.manual_sun_azimuth = data.get("azimuth")
    mock_system.manual_sun_elevation = data.get("elevation")
    return web.json_response({"status": "ok"})


async def handle_api_reset(request):
    """Reset to real-time sun position"""
    mock_system.manual_sun_azimuth = None
    mock_system.manual_sun_elevation = None
    return web.json_response({"status": "ok"})


async def handle_api_connect(request):
    """Connect to Home Assistant"""
    success = await ha_client.connect()
    return web.json_response({
        "connected": success,
        "error": ha_client.last_error,
        "url": ha_client.url
    })


async def handle_api_disconnect(request):
    """Disconnect from Home Assistant"""
    await ha_client.disconnect()
    return web.json_response({"connected": False})


async def handle_api_connection_status(request):
    """Get current connection status"""
    return web.json_response({
        "connected": ha_client.connected,
        "has_credentials": ha_client.has_credentials(),
        "url": ha_client.url if ha_client.has_credentials() else None,
        "error": ha_client.last_error
    })


def create_app():
    app = web.Application()
    app.router.add_get('/', handle_index)
    app.router.add_get('/api/state', handle_api_state)
    app.router.add_post('/api/mode', handle_api_mode)
    app.router.add_post('/api/sun', handle_api_sun_position)
    app.router.add_post('/api/reset', handle_api_reset)
    app.router.add_post('/api/connect', handle_api_connect)
    app.router.add_post('/api/disconnect', handle_api_disconnect)
    app.router.add_get('/api/connection', handle_api_connection_status)
    return app


if __name__ == '__main__':
    print("=" * 60)
    print("Celestial Lighting Local Test Server")
    print("=" * 60)
    print()
    print("Starting server at http://localhost:5050")
    print()
    print("Features:")
    print("  - Real-time sun/moon position based on current time")
    print("  - Virtual Aurora button to cycle modes (sun/moon/off)")
    print("  - Manual sun position override for testing")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 60)
    
    app = create_app()
    web.run_app(app, host='localhost', port=5050)
