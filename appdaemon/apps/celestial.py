"""
Celestial Lighting System for Home Assistant
Automatically adjusts Philips Hue lights based on sun and moon positions
with directional brightness based on azimuth alignment
"""

import appdaemon.plugins.hass.hassapi as hass
import ephem
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional


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
        self.dimmer_level = 1.0  # Dimmer level controlled by Aurora (0.0 to 1.0)
        self.last_sun_elevation = None
        self.last_moon_phase = None
        self.manual_override = False  # Track if user has manually adjusted brightness
        
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
            self.log(f"Update lights - Mode: {self.lighting_mode}, Dimmer: {int(self.dimmer_level * 100)}%", level="DEBUG")
            
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
            import traceback
            self.log(f"Error updating lights: {e}", level="ERROR")
            self.log(f"Traceback: {traceback.format_exc()}", level="ERROR")
    
    def update_sun_lighting(self, elevation: float, azimuth: float):
        """Update lights based on sun position during daytime with directional awareness"""
        # Try to get real-time sun color from weather integration
        kelvin = self.get_realtime_sun_color(elevation)
        if not kelvin:
            # Fallback to calculated color temperature
            kelvin = self.calculate_sun_color_temperature(elevation)
        
        # Calculate base brightness based on sun elevation
        base_brightness_pct = self.calculate_sun_brightness(elevation)
        base_brightness = int(base_brightness_pct * 255 / 100)
        
        # Apply dimmer level multiplier
        base_brightness = int(base_brightness * self.dimmer_level)
        
        # Calculate directional brightness for each light
        brightness_map = self.calculate_directional_brightness(base_brightness, azimuth)
        
        # Calculate actual brightness being applied
        actual_brightness_pct = int((base_brightness * 100) / 255)
        self.log(f"Sun lighting - Kelvin: {kelvin}K, Base: {base_brightness_pct:.1f}% × Dimmer: {int(self.dimmer_level * 100)}% = {actual_brightness_pct}% actual, Azimuth: {azimuth:.1f}°")
        
        # Find the brightest light(s) for logging
        max_brightness = max(brightness_map.values())
        brightest_lights = [light for light, br in brightness_map.items() if br == max_brightness]
        self.log(f"Brightest lights (facing sun): {', '.join(brightest_lights)}")
        
        # Apply to all directional lights
        for light, brightness in brightness_map.items():
            brightness_pct = int(brightness * 100 / 255)
            
            # Turn on lights with brightness > 0, turn off others
            if brightness > 0:
                # Log at INFO level so we can see it
                self.log(f"  Setting {light}: {brightness_pct}% brightness (value: {int(brightness)})")
                self.call_service("light/turn_on",
                    entity_id=light,
                    kelvin=kelvin,
                    brightness=int(brightness),
                    transition=1  # Faster transition for responsive dimming
                )
            else:
                # Turn off lights that should be at 0%
                if self.get_state(light) == "on":
                    self.call_service("light/turn_off",
                        entity_id=light,
                        transition=1  # Faster transition
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
        
        # Try to get real-time moon color, fallback to calculated
        rgb = self.get_realtime_moon_color(altitude, phase)
        if not rgb:
            rgb = self.calculate_moon_color(altitude, phase)
        
        # Moon brightness: 60% of sun brightness, adjusted by dimmer
        base_brightness = int(255 * 0.6 * self.dimmer_level)  # 60% of full brightness
        
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
        
        self.log(f"Moon lighting - RGB: {rgb}, Base: 60% × Dimmer: {int(self.dimmer_level * 100)}% = {int(base_brightness * 100 / 255)}% actual")
        self.log(f"Moon facing lights: {', '.join(lights_to_activate)}")
        
        # Update all lights
        for light in self.light_directions.keys():
            if light in lights_to_activate:
                # Turn on closest lights
                self.call_service("light/turn_on",
                    entity_id=light,
                    rgb_color=rgb,
                    brightness=base_brightness,
                    transition=1  # Faster transition
                )
            else:
                # Turn off all other lights in moon mode
                self.call_service("light/turn_off",
                    entity_id=light,
                    transition=1  # Faster transition
                )
    
    def calculate_sun_color_temperature(self, elevation: float) -> int:
        """Calculate color temperature in Kelvin based on sun elevation
        
        More realistic color temperatures:
        - Sunrise/sunset (< 5°): 2000-3000K (warm orange)
        - Golden hour (5-15°): 3000-4000K (warm white)
        - Mid morning/afternoon (15-45°): 4000-5500K (neutral white)
        - Noon (> 45°): 5500-6500K (cool daylight)
        """
        elevation = max(-10, min(90, elevation))
        
        if elevation < 0:
            # Below horizon: very warm
            kelvin = 2000
        elif elevation < 5:
            # Sunrise/sunset: warm orange
            kelvin = int(2000 + (elevation / 5) * 1000)
        elif elevation < 15:
            # Golden hour: warm white
            kelvin = int(3000 + ((elevation - 5) / 10) * 1000)
        elif elevation < 45:
            # Mid day: neutral to cool
            kelvin = int(4000 + ((elevation - 15) / 30) * 1500)
        else:
            # High noon: cool daylight
            kelvin = int(5500 + ((elevation - 45) / 45) * 1000)
        
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
    
    def get_realtime_sun_color(self, elevation: float) -> Optional[int]:
        """Try to get real-time sun color based on weather conditions"""
        try:
            # Check for cloud cover which affects sun color
            cloud_cover = 0
            for sensor in ["sensor.cloud_coverage", "sensor.openweathermap_cloud_coverage", "weather.home"]:
                if sensor == "weather.home":
                    weather_state = self.get_state(sensor)
                    if weather_state:
                        # Map weather conditions to approximate cloud cover
                        conditions_map = {
                            "sunny": 0, "clear": 0, "clear-night": 0,
                            "partlycloudy": 30, "partly-cloudy": 30,
                            "cloudy": 70, "fog": 90,
                            "rainy": 80, "pouring": 90,
                            "snowy": 85, "hail": 85,
                            "lightning": 75, "lightning-rainy": 80
                        }
                        cloud_cover = conditions_map.get(weather_state, 50)
                        break
                else:
                    state = self.get_state(sensor)
                    if state and state != "unknown":
                        cloud_cover = float(state)
                        break
            
            # Adjust color temperature based on cloud cover and elevation
            if elevation < 0:
                base_kelvin = 2000  # Below horizon
            elif elevation < 10:
                # Sunrise/sunset - more orange with clouds
                base_kelvin = 2200 - int(cloud_cover * 2)  # More orange with clouds
            elif elevation < 30:
                # Low sun - golden hour
                base_kelvin = 3500 - int(cloud_cover * 5)  # Warmer with clouds
            else:
                # High sun - affected by clouds
                base_kelvin = 5500 - int(cloud_cover * 10)  # Much warmer with heavy clouds
            
            self.log(f"Real-time sun color: {base_kelvin}K (cloud cover: {cloud_cover}%)", level="DEBUG")
            return max(2000, min(6500, base_kelvin))
            
        except Exception as e:
            self.log(f"Could not get real-time sun color: {e}", level="DEBUG")
            return None
    
    def get_realtime_moon_color(self, altitude: float, phase: float) -> Optional[List[int]]:
        """Get realistic moon color based on altitude and atmospheric conditions"""
        try:
            # Check for atmospheric conditions that affect moon color
            humidity = 50  # Default
            for sensor in ["sensor.humidity", "sensor.outdoor_humidity", "sensor.openweathermap_humidity"]:
                state = self.get_state(sensor)
                if state and state != "unknown":
                    humidity = float(state)
                    break
            
            # Moon color is affected by altitude and atmospheric conditions
            # Lower altitude = more atmosphere = warmer color
            # High humidity = more scattering = warmer color
            
            if altitude < 0:
                return None  # Moon below horizon
            elif altitude < 10:
                # Very low moon - orange/amber due to atmosphere
                # This is the "harvest moon" effect
                base_r, base_g, base_b = 255, 180, 120
            elif altitude < 30:
                # Low moon - yellowish white
                humidity_factor = humidity / 100
                base_r = int(255 - 10 * (1 - humidity_factor))
                base_g = int(240 - 20 * (1 - humidity_factor))
                base_b = int(210 - 30 * (1 - humidity_factor))
            else:
                # High moon - cool white with slight blue tint
                # This is the typical "moonlight" color
                base_r, base_g, base_b = 226, 231, 244
            
            # Adjust for moon phase (dimmer during crescent)
            phase_factor = 0.5 + (phase / 200)  # 0.5 to 1.0 based on phase
            
            rgb = [
                min(255, int(base_r * phase_factor)),
                min(255, int(base_g * phase_factor)),
                min(255, int(base_b * phase_factor))
            ]
            
            self.log(f"Real-time moon color: RGB{rgb} (altitude: {altitude:.1f}°, humidity: {humidity}%)", level="DEBUG")
            return rgb
            
        except Exception as e:
            self.log(f"Could not get real-time moon color: {e}", level="DEBUG")
            return None
    
    def calculate_moon_color(self, altitude: float, phase: float) -> List[int]:
        """Calculate RGB color based on moon altitude - more realistic moon colors"""
        # Moon should be cooler/whiter than sun, with slight blue tint
        if altitude > 45:
            # High moon: cool blue-white (moonlight color)
            base_r, base_g, base_b = 230, 235, 255
        elif altitude > 15:
            # Mid altitude: neutral cool white
            base_r, base_g, base_b = 240, 245, 255
        elif altitude > 0:
            # Low altitude: slightly warm but still cool
            base_r, base_g, base_b = 250, 245, 235
        else:
            # Below horizon: dim warm
            base_r, base_g, base_b = 255, 230, 200
        
        # Less dramatic intensity adjustment based on phase
        # Even new moon has some light reflection
        intensity = 0.6 + 0.4 * (phase / 100)  # Range from 60% to 100%
        r = int(base_r * intensity)
        g = int(base_g * intensity)
        b = int(base_b * intensity)
        
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
        subtype = data.get("subtype", "")
        
        # Button press cycles through modes (short_release is the actual button release)
        if event_type in ["short_release", "click", "button_1_press", "button_1_click", "on"]:
            self.cycle_lighting_mode()
        # Rotation adjusts brightness (only respond to "start" event, ignore "repeat")
        elif event_type == "start" and subtype in ["clock_wise", "counter_clock_wise"]:
            # Determine rotation direction
            if subtype == "counter_clock_wise":
                direction = -1
            else:
                direction = 1
            self.handle_dimmer_rotation({"direction": direction})
    
    def cycle_lighting_mode(self):
        """Cycle through lighting modes: sun -> moon -> off -> sun"""
        modes = ["sun", "moon", "off"]
        current_index = modes.index(self.lighting_mode)
        self.lighting_mode = modes[(current_index + 1) % len(modes)]
        
        # Reset dimmer to 100% when changing modes (optional behavior)
        # Comment out these lines if you want dimmer to persist across mode changes
        if self.manual_override:
            self.log(f"Resetting dimmer to 100% (was {int(self.dimmer_level * 100)}%)")
            self.dimmer_level = 1.0
            self.manual_override = False
        
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
        """Handle dimmer rotation to adjust dimmer level"""
        # Get rotation direction
        direction = data.get("direction", 0)
        
        if direction == 0:
            return
        
        # Mark that user has manually adjusted
        self.manual_override = True
            
        # Adjust dimmer level with 5% steps for noticeable changes
        step = 0.05  # 5% per click
        
        if direction > 0:
            self.dimmer_level = min(1.0, self.dimmer_level + step)
        else:
            self.dimmer_level = max(0.1, self.dimmer_level - step)
        
        # Round to nearest 5% for cleaner values
        self.dimmer_level = round(self.dimmer_level * 20) / 20
        
        self.log(f"Dimmer adjusted to: {int(self.dimmer_level * 100)}% (manual override active)")
        
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