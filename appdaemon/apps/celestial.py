"""
Celestial Lighting System for Home Assistant
Automatically adjusts Philips Hue lights based on sun and moon positions
with directional brightness based on azimuth alignment
"""

import appdaemon.plugins.hass.hassapi as hass
import ephem
import math
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any


class CelestialLighting(hass.Hass):
    """Main AppDaemon app for celestial-based lighting control with directional awareness"""
    
    def initialize(self):
        """Initialize the app when AppDaemon starts"""
        self.log("Celestial Lighting System initializing...")
        
        # Configuration
        self.directional_lights = self.args.get("directional_lights", {})
        self.aurora_device_id = self.args.get("aurora_device_id", None)
        self.update_interval = self.args.get("update_interval", 60)
        
        # Location configuration (fallback to HA's location)
        location = self.args.get("location", {})
        self.latitude = location.get("latitude", self.get_state("zone.home", attribute="latitude"))
        self.longitude = location.get("longitude", self.get_state("zone.home", attribute="longitude"))
        
        # State management
        self.lighting_mode = "sun"  # "sun", "moon", or "off"
        self.base_brightness = 1.0  # Base brightness multiplier (0.0 to 1.0)
        self.last_sun_elevation = None
        self.last_moon_phase = None
        
        # Parse directional lights configuration
        self.light_directions = {}
        for direction, entity_id in self.directional_lights.items():
            # Convert direction to azimuth angle
            azimuth = self.direction_to_azimuth(direction.upper())
            if azimuth is not None:
                if isinstance(entity_id, list):
                    # Multiple bulbs for one direction
                    for eid in entity_id:
                        self.light_directions[eid] = azimuth
                else:
                    self.light_directions[entity_id] = azimuth
                self.log(f"Mapped {entity_id} to direction {direction} (azimuth {azimuth}°)")
        
        # Validate configuration
        if not self.light_directions:
            self.log("WARNING: No directional lights configured! Add directional_lights to apps.yaml", level="WARNING")
            return
            
        if not self.latitude or not self.longitude:
            self.log("ERROR: Location not configured! Set latitude/longitude in apps.yaml or Home Assistant", level="ERROR")
            return
            
        # Set up ephem observer for moon calculations
        self.observer = ephem.Observer()
        self.observer.lat = str(self.latitude)
        self.observer.lon = str(self.longitude)
        
        # Schedule regular updates
        self.run_every(self.update_lights, datetime.now() + timedelta(seconds=5), self.update_interval)
        
        # Listen for Aurora dimmer events if configured
        if self.aurora_device_id:
            # Try multiple event types for Aurora dimmer
            self.listen_event(self.handle_aurora_event, "hue_event", device_id=self.aurora_device_id)
            self.listen_event(self.handle_aurora_event, "zha_event", device_id=self.aurora_device_id)
            self.listen_event(self.handle_aurora_event, "deconz_event", device_id=self.aurora_device_id)
            self.log(f"Listening for Aurora dimmer events: {self.aurora_device_id}")
        
        self.log(f"Celestial Lighting initialized for {len(self.light_directions)} directional lights")
        self.log(f"Location: {self.latitude}, {self.longitude}")
        self.log(f"Update interval: {self.update_interval} seconds")
    
    def direction_to_azimuth(self, direction: str) -> Optional[float]:
        """Convert compass direction to azimuth angle (0-360 degrees)"""
        direction_map = {
            "N": 0,
            "NNE": 22.5,
            "NE": 45,
            "ENE": 67.5,
            "E": 90,
            "ESE": 112.5,
            "SE": 135,
            "SSE": 157.5,
            "S": 180,
            "SSW": 202.5,
            "SW": 225,
            "WSW": 247.5,
            "W": 270,
            "WNW": 292.5,
            "NW": 315,
            "NNW": 337.5,
            "NORTH": 0,
            "EAST": 90,
            "SOUTH": 180,
            "WEST": 270
        }
        return direction_map.get(direction)
    
    def calculate_azimuth_alignment(self, light_azimuth: float, celestial_azimuth: float) -> float:
        """
        Calculate alignment factor (0-1) based on azimuth difference
        1.0 = perfectly aligned, 0.0 = opposite direction (180° away)
        Linear falloff from 100% to 0% based on angular distance
        """
        # Calculate angular difference (0-180 degrees)
        diff = abs(light_azimuth - celestial_azimuth)
        if diff > 180:
            diff = 360 - diff
        
        # Linear falloff: 100% at 0°, 0% at 180°
        # alignment = 1.0 - (diff / 180.0)
        # 
        # Or use cosine for smoother falloff (comment out linear for this):
        # alignment = (math.cos(math.radians(diff)) + 1) / 2
        
        # Using raised cosine for natural falloff that reaches 0 at 180°
        alignment = max(0, (math.cos(math.radians(diff)) + 1) / 2)
        
        return alignment
    
    def calculate_directional_brightness(self, base_brightness: float, celestial_azimuth: float) -> Dict[str, float]:
        """
        Calculate individual brightness for each directional light based on celestial body position
        Each bulb's brightness is directly proportional to its alignment (0-100% based on angle)
        """
        brightness_map = {}
        
        for light, light_azimuth in self.light_directions.items():
            # Get alignment factor (1.0 at sun position, 0.0 at opposite side)
            alignment = self.calculate_azimuth_alignment(light_azimuth, celestial_azimuth)
            
            # Brightness is directly proportional to alignment
            # Full alignment = full brightness, opposite = 0% brightness
            brightness = base_brightness * alignment
            brightness_map[light] = brightness
            
            # Log individual bulb brightness for debugging
            if brightness > 0:
                brightness_pct = int(brightness * 100 / 255)
                self.log(f"  {light}: {brightness_pct}% (alignment: {alignment:.2f})", level="DEBUG")
        
        return brightness_map
    
    def update_lights(self, kwargs):
        """Main update loop - called every update_interval seconds"""
        try:
            self.log(f"Update lights - Mode: {self.lighting_mode}, Base brightness: {self.base_brightness:.1f}", level="DEBUG")
            
            if self.lighting_mode == "off":
                # Turn off all lights
                for light in self.light_directions.keys():
                    if self.get_state(light) == "on":
                        self.call_service("light/turn_off", entity_id=light)
                return
            elif self.lighting_mode == "sun":
                # Get sun position from Home Assistant
                sun_elevation = float(self.get_state("sun.sun", attribute="elevation"))
                sun_azimuth = float(self.get_state("sun.sun", attribute="azimuth"))
                self.log(f"Sun position - Elevation: {sun_elevation:.1f}°, Azimuth: {sun_azimuth:.1f}°", level="DEBUG")
                self.update_sun_lighting(sun_elevation, sun_azimuth)
            elif self.lighting_mode == "moon":
                self.update_moon_lighting()
                
        except Exception as e:
            self.log(f"Error updating lights: {e}", level="ERROR")
    
    def update_sun_lighting(self, elevation: float, azimuth: float):
        """Update lights based on sun position during daytime with directional awareness"""
        # Calculate color temperature based on sun elevation
        kelvin = self.calculate_sun_color_temperature(elevation)
        
        # Calculate base brightness based on sun elevation
        base_brightness_pct = self.calculate_sun_brightness(elevation)
        base_brightness = int(base_brightness_pct * 255 / 100)
        
        # Apply base brightness multiplier
        base_brightness = int(base_brightness * self.base_brightness)
        
        # Calculate directional brightness for each light
        brightness_map = self.calculate_directional_brightness(base_brightness, azimuth)
        
        self.log(f"Sun lighting - Kelvin: {kelvin}K, Base brightness: {base_brightness_pct}% (adjusted: {int(base_brightness_pct * self.base_brightness)}%), Azimuth: {azimuth:.1f}°")
        
        # Find the brightest light(s) for logging
        max_brightness = max(brightness_map.values())
        brightest_lights = [light for light, br in brightness_map.items() if br == max_brightness]
        self.log(f"Brightest lights (facing sun): {', '.join(brightest_lights)}")
        
        # Apply to all directional lights
        for light, brightness in brightness_map.items():
            if self.get_state(light) == "on":
                brightness_pct = int(brightness * 100 / 255)
                self.log(f"  {light}: {brightness_pct}% brightness", level="DEBUG")
                
                self.call_service("light/turn_on",
                    entity_id=light,
                    kelvin=kelvin,
                    brightness=int(brightness),
                    transition=5
                )
    
    def update_moon_lighting(self):
        """Update lights based on moon position - only light 1-2 closest bulbs"""
        # Calculate moon position and phase
        moon_data = self.get_moon_position()
        altitude = moon_data["altitude"]
        azimuth = moon_data["azimuth"]
        phase = moon_data["phase"]
        illumination = moon_data["illumination"]
        
        self.log(f"Moon position - Altitude: {altitude:.1f}°, Azimuth: {azimuth:.1f}°, Phase: {phase:.1f}%", level="DEBUG")
        
        # Calculate RGB color based on moon altitude and phase
        rgb = self.calculate_moon_color(altitude, phase)
        
        # Use same brightness as sun mode but apply base brightness multiplier
        base_brightness = int(255 * self.base_brightness)  # Full brightness adjusted by dimmer
        
        # Find the 1-2 closest bulbs to moon position
        light_alignments = {}
        for light, light_azimuth in self.light_directions.items():
            alignment = self.calculate_azimuth_alignment(light_azimuth, azimuth)
            light_alignments[light] = alignment
        
        # Sort by alignment and get top 2
        sorted_lights = sorted(light_alignments.items(), key=lambda x: x[1], reverse=True)
        closest_lights = sorted_lights[:2]  # Get top 2 aligned lights
        
        # Only light the closest 1-2 bulbs if they're reasonably aligned
        lights_to_activate = []
        for light, alignment in closest_lights:
            if alignment > 0.5:  # Only if more than 50% aligned
                lights_to_activate.append(light)
        
        self.log(f"Moon lighting - RGB: {rgb}, Brightness: {int(base_brightness * 100 / 255)}%")
        self.log(f"Moon facing lights: {', '.join([l for l, _ in closest_lights[:len(lights_to_activate)]])}")
        
        # Update all lights
        for light in self.light_directions.keys():
            if light in [l for l, _ in lights_to_activate]:
                # Turn on closest lights
                if self.get_state(light) == "on":
                    self.call_service("light/turn_on",
                        entity_id=light,
                        rgb_color=rgb,
                        brightness=base_brightness,
                        transition=5
                    )
            else:
                # Turn off all other lights in moon mode
                if self.get_state(light) == "on":
                    self.call_service("light/turn_off",
                        entity_id=light,
                        transition=5
                    )
    
    def calculate_sun_color_temperature(self, elevation: float) -> int:
        """Calculate color temperature in Kelvin based on sun elevation"""
        # Clamp elevation to valid range
        elevation = max(-10, min(90, elevation))
        
        # Map elevation (-10 to 90) to color temperature (2000K to 6500K)
        # Linear mapping: (elevation + 10) / 100 * 4500 + 2000
        kelvin = int(2000 + (elevation + 10) * 45)
        
        return min(6500, max(2000, kelvin))
    
    def calculate_sun_brightness(self, elevation: float) -> float:
        """Calculate brightness percentage based on sun elevation"""
        # Clamp elevation to valid range
        elevation = max(-10, min(90, elevation))
        
        # Map elevation (-10 to 90) to brightness (20% to 100%)
        # Use cosine curve for more natural transition
        if elevation <= 0:
            return 20.0
        else:
            # Smooth curve from 20% to 100%
            return 20 + (80 * (elevation / 90))
    
    def get_moon_position(self) -> Dict[str, float]:
        """Calculate current moon position and phase using ephem"""
        self.observer.date = ephem.now()
        moon = ephem.Moon()
        moon.compute(self.observer)
        
        # Convert radians to degrees
        altitude = math.degrees(moon.alt)
        azimuth = math.degrees(moon.az)
        
        # Calculate phase (0 = new moon, 100 = full moon)
        phase = moon.phase  # This is already 0-100
        
        # Calculate illumination percentage
        illumination = phase  # Simplified - phase percentage equals illumination
        
        return {
            "altitude": altitude,
            "azimuth": azimuth,
            "phase": phase,
            "illumination": illumination
        }
    
    def calculate_moon_color(self, altitude: float, phase: float) -> List[int]:
        """Calculate RGB color based on moon altitude and phase"""
        # Base color: blue-white for high moon, amber for low moon
        if altitude > 30:
            # High moon: cool blue-white
            base_r, base_g, base_b = 200, 210, 255
        elif altitude > 0:
            # Mid altitude: neutral white
            base_r, base_g, base_b = 255, 240, 220
        else:
            # Low/below horizon: warm amber
            base_r, base_g, base_b = 255, 200, 150
        
        # Adjust intensity based on phase (fuller moon = more intense)
        intensity = phase / 100
        r = int(base_r * (0.3 + 0.7 * intensity))
        g = int(base_g * (0.3 + 0.7 * intensity))
        b = int(base_b * (0.3 + 0.7 * intensity))
        
        return [min(255, r), min(255, g), min(255, b)]
    
    def calculate_moon_brightness(self, altitude: float, illumination: float) -> float:
        """Calculate brightness percentage based on moon altitude and illumination"""
        if altitude < 0:
            # Moon below horizon
            return 5.0
        
        # Base brightness on illumination (phase)
        base_brightness = 5 + (illumination * 0.4)  # 5% to 45% based on phase
        
        # Adjust for altitude (higher = brighter)
        altitude_factor = min(1.0, altitude / 45)  # Max factor at 45 degrees
        
        return base_brightness * (0.5 + 0.5 * altitude_factor)
    
    def handle_aurora_event(self, event_name, data, kwargs):
        """Handle events from Aurora dimmer"""
        self.log(f"Aurora event received: {event_name} - {data}")
        
        # Parse event type - different formats for different integrations
        event_type = data.get("type", data.get("command", ""))
        
        # Button press cycles through modes
        if event_type in ["click", "button_1_press", "button_1_click", "on"]:
            self.cycle_lighting_mode()
        # Rotation adjusts brightness
        elif event_type in ["rotation", "dial_rotate", "step_with_on_off"]:
            self.handle_dimmer_rotation(data)
    
    def cycle_lighting_mode(self):
        """Cycle through lighting modes: sun -> moon -> off -> sun"""
        modes = ["sun", "moon", "off"]
        current_index = modes.index(self.lighting_mode)
        self.lighting_mode = modes[(current_index + 1) % len(modes)]
        
        self.log(f"Lighting mode changed to: {self.lighting_mode.upper()}")
        
        # Flash lights to indicate mode
        if self.lighting_mode == "sun":
            self.flash_lights(1, [255, 200, 100])  # Warm white flash
        elif self.lighting_mode == "moon":
            self.flash_lights(1, [100, 100, 255])  # Blue flash
        elif self.lighting_mode == "off":
            self.flash_lights(1, [255, 0, 0])  # Red flash
        
        # Immediately update lights
        self.update_lights({})
    
    def handle_dimmer_rotation(self, data):
        """Handle dimmer rotation to adjust base brightness"""
        # Extract rotation amount (different keys for different integrations)
        rotation = data.get("value", data.get("params", {}).get("step_size", 0))
        
        if rotation == 0:
            return
            
        # Adjust base brightness (0.0 to 1.0)
        step = 0.05 if abs(rotation) < 10 else 0.1
        if rotation > 0:
            self.base_brightness = min(1.0, self.base_brightness + step)
        else:
            self.base_brightness = max(0.1, self.base_brightness - step)
        
        self.log(f"Base brightness adjusted to: {int(self.base_brightness * 100)}%")
        
        # Immediately update lights with new brightness
        self.update_lights({})
    
    def flash_lights(self, count: int, color: List[int]):
        """Flash lights with specified color to provide feedback"""
        lights_to_flash = list(self.light_directions.keys())
        
        for i in range(count):
            # Store current state
            original_states = {}
            for light in lights_to_flash:
                if self.get_state(light) == "on":
                    original_states[light] = {
                        "brightness": self.get_state(light, attribute="brightness"),
                        "rgb_color": self.get_state(light, attribute="rgb_color")
                    }
            
            # Flash color
            for light in original_states:
                self.call_service("light/turn_on",
                    entity_id=light,
                    rgb_color=color,
                    brightness=255,
                    transition=0
                )
            
            # Wait
            self.run_in(lambda *args: None, 0.3)
            
            # Restore original state
            for light, state in original_states.items():
                self.call_service("light/turn_on",
                    entity_id=light,
                    rgb_color=state["rgb_color"],
                    brightness=state["brightness"],
                    transition=0
                )
            
            if i < count - 1:
                self.run_in(lambda *args: None, 0.3)
    
    def terminate(self):
        """Cleanup when app is stopped"""
        self.log("Celestial Lighting System terminating...")