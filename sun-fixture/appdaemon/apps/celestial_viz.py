"""
Celestial Lighting Visualization UI
Provides a live-updating web UI to visualize the current state of the sun-fixture lights
"""

import appdaemon.plugins.hass.hassapi as hass
from aiohttp import web
import json
import math
from datetime import datetime
from typing import Dict, List, Optional


class CelestialVisualization(hass.Hass):
    """AppDaemon app that serves a visualization dashboard for the celestial lighting system"""
    
    def initialize(self):
        """Initialize the visualization app"""
        self.log("Celestial Visualization initializing...")
        
        # Get configuration from celestial_lighting app
        self.directional_lights = self.args.get("directional_lights", {})
        self.update_interval = self.args.get("update_interval", 5)
        
        # Location configuration
        location = self.args.get("location", {})
        self.latitude = location.get("latitude", self.get_state("zone.home", attribute="latitude"))
        self.longitude = location.get("longitude", self.get_state("zone.home", attribute="longitude"))
        
        # Parse directional lights into azimuth mapping
        self.light_directions = {}
        self.direction_names = {}
        for direction, entity_id in self.directional_lights.items():
            azimuth = self.direction_to_azimuth(direction.upper())
            if azimuth is not None:
                if isinstance(entity_id, list):
                    for eid in entity_id:
                        self.light_directions[eid] = azimuth
                        self.direction_names[eid] = direction.upper()
                else:
                    self.light_directions[entity_id] = azimuth
                    self.direction_names[entity_id] = direction.upper()
        
        # Register web routes
        self.register_route(self.serve_dashboard, "celestial")
        self.register_route(self.serve_api_state, "celestial/api/state")
        
        self.log(f"Celestial Visualization initialized - access at http://<appdaemon-ip>:5050/app/celestial")
        self.log(f"Tracking {len(self.light_directions)} lights")
    
    def direction_to_azimuth(self, direction: str) -> Optional[float]:
        """Convert compass direction to azimuth angle"""
        direction_map = {
            "N": 0, "NNE": 22.5, "NE": 45, "ENE": 67.5,
            "E": 90, "ESE": 112.5, "SE": 135, "SSE": 157.5,
            "S": 180, "SSW": 202.5, "SW": 225, "WSW": 247.5,
            "W": 270, "WNW": 292.5, "NW": 315, "NNW": 337.5,
            "NORTH": 0, "EAST": 90, "SOUTH": 180, "WEST": 270
        }
        return direction_map.get(direction)
    
    def kelvin_to_rgb(self, kelvin: int) -> List[int]:
        """Convert color temperature in Kelvin to RGB values"""
        temp = kelvin / 100
        
        # Red
        if temp <= 66:
            red = 255
        else:
            red = temp - 60
            red = 329.698727446 * (red ** -0.1332047592)
            red = max(0, min(255, red))
        
        # Green
        if temp <= 66:
            green = temp
            green = 99.4708025861 * math.log(green) - 161.1195681661
        else:
            green = temp - 60
            green = 288.1221695283 * (green ** -0.0755148492)
        green = max(0, min(255, green))
        
        # Blue
        if temp >= 66:
            blue = 255
        elif temp <= 19:
            blue = 0
        else:
            blue = temp - 10
            blue = 138.5177312231 * math.log(blue) - 305.0447927307
            blue = max(0, min(255, blue))
        
        return [int(red), int(green), int(blue)]
    
    def get_light_state(self, entity_id: str) -> Dict:
        """Get the current state of a light"""
        state = self.get_state(entity_id)
        brightness = self.get_state(entity_id, attribute="brightness") or 0
        color_temp = self.get_state(entity_id, attribute="color_temp")
        rgb_color = self.get_state(entity_id, attribute="rgb_color")
        kelvin = None
        
        # Try to get kelvin from color_temp (mired)
        if color_temp:
            try:
                kelvin = int(1000000 / color_temp)
            except:
                pass
        
        # If no kelvin, estimate from rgb or use default
        if not kelvin:
            kelvin = 4000  # Default neutral white
        
        # Get RGB - either from attribute or convert from kelvin
        if rgb_color:
            rgb = list(rgb_color)
        else:
            rgb = self.kelvin_to_rgb(kelvin)
        
        return {
            "entity_id": entity_id,
            "state": state,
            "brightness": brightness,
            "brightness_pct": int((brightness / 255) * 100) if brightness else 0,
            "kelvin": kelvin,
            "rgb": rgb,
            "azimuth": self.light_directions.get(entity_id, 0),
            "direction": self.direction_names.get(entity_id, "?")
        }
    
    def get_celestial_data(self) -> Dict:
        """Get current sun/moon position data"""
        sun_elevation = float(self.get_state("sun.sun", attribute="elevation") or 0)
        sun_azimuth = float(self.get_state("sun.sun", attribute="azimuth") or 0)
        
        # Determine mode based on elevation
        if sun_elevation > -6:
            mode = "sun"
        else:
            mode = "moon"
        
        return {
            "mode": mode,
            "sun": {
                "elevation": sun_elevation,
                "azimuth": sun_azimuth
            },
            "timestamp": datetime.now().isoformat()
        }
    
    async def serve_api_state(self, request, kwargs):
        """API endpoint to get current state as JSON"""
        try:
            lights_state = []
            for entity_id in self.light_directions.keys():
                lights_state.append(self.get_light_state(entity_id))
            
            celestial = self.get_celestial_data()
            
            response_data = {
                "lights": lights_state,
                "celestial": celestial,
                "config": {
                    "latitude": self.latitude,
                    "longitude": self.longitude
                }
            }
            
            return web.json_response(response_data)
        except Exception as e:
            self.log(f"API error: {e}", level="ERROR")
            return web.json_response({"error": str(e)}, status=500)
    
    async def serve_dashboard(self, request, kwargs):
        """Serve the main visualization dashboard"""
        html = self.get_dashboard_html()
        return web.Response(text=html, content_type="text/html")
    
    def get_dashboard_html(self) -> str:
        """Generate the visualization dashboard HTML"""
        return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Celestial Lighting Visualization</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            min-height: 100vh;
            color: #e0e0e0;
            padding: 20px;
        }
        
        .container {
            max-width: 900px;
            margin: 0 auto;
        }
        
        h1 {
            text-align: center;
            font-size: 1.8em;
            margin-bottom: 10px;
            color: #fff;
            text-shadow: 0 2px 10px rgba(255,200,100,0.3);
        }
        
        .status-bar {
            display: flex;
            justify-content: center;
            gap: 30px;
            margin-bottom: 20px;
            padding: 15px;
            background: rgba(255,255,255,0.05);
            border-radius: 12px;
            flex-wrap: wrap;
        }
        
        .status-item {
            text-align: center;
        }
        
        .status-label {
            font-size: 0.75em;
            color: #888;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .status-value {
            font-size: 1.2em;
            font-weight: 600;
            color: #fff;
        }
        
        .mode-sun { color: #ffd700; }
        .mode-moon { color: #b0c4de; }
        .mode-off { color: #666; }
        
        .visualization {
            position: relative;
            width: 100%;
            max-width: 600px;
            margin: 0 auto;
            aspect-ratio: 1;
        }
        
        .compass-ring {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 90%;
            height: 90%;
            border: 2px solid rgba(255,255,255,0.15);
            border-radius: 50%;
        }
        
        .compass-ring.inner {
            width: 60%;
            height: 60%;
            border-style: dashed;
            border-color: rgba(255,255,255,0.08);
        }
        
        .compass-labels {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 100%;
            height: 100%;
        }
        
        .compass-label {
            position: absolute;
            font-size: 0.85em;
            color: rgba(255,255,255,0.4);
            font-weight: 500;
        }
        
        .compass-label.n { top: 2%; left: 50%; transform: translateX(-50%); }
        .compass-label.s { bottom: 2%; left: 50%; transform: translateX(-50%); }
        .compass-label.e { right: 2%; top: 50%; transform: translateY(-50%); }
        .compass-label.w { left: 2%; top: 50%; transform: translateY(-50%); }
        
        .light-container {
            position: absolute;
            top: 50%;
            left: 50%;
            width: 100%;
            height: 100%;
            transform: translate(-50%, -50%);
        }
        
        .light {
            position: absolute;
            transform: translate(-50%, -50%);
            transition: all 0.5s ease;
        }
        
        .light-circle {
            width: 70px;
            height: 70px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-direction: column;
            transition: all 0.5s ease;
            box-shadow: 0 0 30px rgba(255,255,255,0.1);
            border: 2px solid rgba(255,255,255,0.2);
        }
        
        .light-circle.on {
            box-shadow: 0 0 40px var(--light-color), 0 0 80px var(--light-color-dim);
        }
        
        .light-circle.off {
            background: rgba(30,30,40,0.8) !important;
            box-shadow: none;
        }
        
        .light-direction {
            font-size: 0.9em;
            font-weight: 700;
            color: rgba(0,0,0,0.7);
            text-shadow: 0 1px 2px rgba(255,255,255,0.3);
        }
        
        .light-circle.off .light-direction {
            color: rgba(255,255,255,0.3);
        }
        
        .light-brightness {
            font-size: 0.7em;
            color: rgba(0,0,0,0.5);
        }
        
        .light-circle.off .light-brightness {
            color: rgba(255,255,255,0.2);
        }
        
        .celestial-body {
            position: absolute;
            transform: translate(-50%, -50%);
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5em;
            transition: all 1s ease;
            z-index: 10;
        }
        
        .celestial-body.sun {
            background: radial-gradient(circle, #fff9c4 0%, #ffeb3b 50%, #ff9800 100%);
            box-shadow: 0 0 30px #ffeb3b, 0 0 60px #ff9800;
        }
        
        .celestial-body.moon {
            background: radial-gradient(circle, #fff 0%, #e0e0e0 50%, #b0c4de 100%);
            box-shadow: 0 0 20px rgba(176,196,222,0.5);
        }
        
        .center-info {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            text-align: center;
            z-index: 5;
        }
        
        .center-info .fixture-icon {
            font-size: 2em;
            margin-bottom: 5px;
        }
        
        .center-info .fixture-label {
            font-size: 0.7em;
            color: rgba(255,255,255,0.5);
            text-transform: uppercase;
            letter-spacing: 2px;
        }
        
        .light-list {
            margin-top: 30px;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 10px;
        }
        
        .light-item {
            background: rgba(255,255,255,0.05);
            border-radius: 8px;
            padding: 12px;
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .light-item-indicator {
            width: 24px;
            height: 24px;
            border-radius: 50%;
            flex-shrink: 0;
        }
        
        .light-item-info {
            flex: 1;
            min-width: 0;
        }
        
        .light-item-name {
            font-size: 0.85em;
            font-weight: 500;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        
        .light-item-details {
            font-size: 0.7em;
            color: #888;
        }
        
        .update-time {
            text-align: center;
            margin-top: 20px;
            font-size: 0.75em;
            color: #666;
        }
        
        @keyframes pulse {
            0%, 100% { transform: translate(-50%, -50%) scale(1); }
            50% { transform: translate(-50%, -50%) scale(1.05); }
        }
        
        .celestial-body.sun {
            animation: pulse 4s ease-in-out infinite;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>☀️ Celestial Lighting</h1>
        
        <div class="status-bar">
            <div class="status-item">
                <div class="status-label">Mode</div>
                <div class="status-value" id="mode">--</div>
            </div>
            <div class="status-item">
                <div class="status-label">Sun Elevation</div>
                <div class="status-value" id="sun-elevation">--°</div>
            </div>
            <div class="status-item">
                <div class="status-label">Sun Azimuth</div>
                <div class="status-value" id="sun-azimuth">--°</div>
            </div>
        </div>
        
        <div class="visualization">
            <div class="compass-ring"></div>
            <div class="compass-ring inner"></div>
            <div class="compass-labels">
                <span class="compass-label n">N</span>
                <span class="compass-label s">S</span>
                <span class="compass-label e">E</span>
                <span class="compass-label w">W</span>
            </div>
            <div class="center-info">
                <div class="fixture-icon">💡</div>
                <div class="fixture-label">Sun Fixture</div>
            </div>
            <div class="light-container" id="lights-container"></div>
            <div class="celestial-body sun" id="celestial-body">☀️</div>
        </div>
        
        <div class="light-list" id="light-list"></div>
        
        <div class="update-time">Last update: <span id="last-update">--</span></div>
    </div>
    
    <script>
        const POLL_INTERVAL = 2000; // Poll every 2 seconds
        
        function azimuthToPosition(azimuth, radius = 42) {
            // Convert azimuth to radians (0° = North = top)
            // Azimuth goes clockwise from North
            const rad = (azimuth - 90) * (Math.PI / 180);
            const x = 50 + radius * Math.cos(rad);
            const y = 50 + radius * Math.sin(rad);
            return { x, y };
        }
        
        function rgbToString(rgb) {
            return `rgb(${rgb[0]}, ${rgb[1]}, ${rgb[2]})`;
        }
        
        function rgbToDimString(rgb, factor = 0.3) {
            return `rgba(${rgb[0]}, ${rgb[1]}, ${rgb[2]}, ${factor})`;
        }
        
        function updateVisualization(data) {
            const container = document.getElementById('lights-container');
            const listContainer = document.getElementById('light-list');
            
            // Clear existing lights
            container.innerHTML = '';
            listContainer.innerHTML = '';
            
            // Update status bar
            const mode = data.celestial.mode;
            const modeEl = document.getElementById('mode');
            modeEl.textContent = mode.toUpperCase();
            modeEl.className = `status-value mode-${mode}`;
            
            document.getElementById('sun-elevation').textContent = 
                data.celestial.sun.elevation.toFixed(1) + '°';
            document.getElementById('sun-azimuth').textContent = 
                data.celestial.sun.azimuth.toFixed(1) + '°';
            
            // Update celestial body position
            const celestialBody = document.getElementById('celestial-body');
            const celestialPos = azimuthToPosition(data.celestial.sun.azimuth, 38);
            celestialBody.style.left = celestialPos.x + '%';
            celestialBody.style.top = celestialPos.y + '%';
            
            if (mode === 'sun') {
                celestialBody.className = 'celestial-body sun';
                celestialBody.innerHTML = '☀️';
            } else {
                celestialBody.className = 'celestial-body moon';
                celestialBody.innerHTML = '🌙';
            }
            
            // Render lights
            data.lights.forEach(light => {
                // Circle visualization
                const pos = azimuthToPosition(light.azimuth, 38);
                const isOn = light.state === 'on' && light.brightness > 0;
                const color = rgbToString(light.rgb);
                const dimColor = rgbToDimString(light.rgb, 0.3);
                
                const lightEl = document.createElement('div');
                lightEl.className = 'light';
                lightEl.style.left = pos.x + '%';
                lightEl.style.top = pos.y + '%';
                
                const opacity = isOn ? 0.3 + (light.brightness_pct / 100) * 0.7 : 0.2;
                const scale = isOn ? 0.8 + (light.brightness_pct / 100) * 0.4 : 0.8;
                
                lightEl.innerHTML = `
                    <div class="light-circle ${isOn ? 'on' : 'off'}" 
                         style="background: ${isOn ? color : 'rgba(30,30,40,0.8)'};
                                --light-color: ${color};
                                --light-color-dim: ${dimColor};
                                transform: scale(${scale});
                                opacity: ${opacity};">
                        <span class="light-direction">${light.direction}</span>
                        <span class="light-brightness">${light.brightness_pct}%</span>
                    </div>
                `;
                container.appendChild(lightEl);
                
                // List item
                const listItem = document.createElement('div');
                listItem.className = 'light-item';
                listItem.innerHTML = `
                    <div class="light-item-indicator" 
                         style="background: ${isOn ? color : '#333'}; 
                                box-shadow: ${isOn ? '0 0 10px ' + dimColor : 'none'};"></div>
                    <div class="light-item-info">
                        <div class="light-item-name">${light.direction} - ${light.entity_id.split('.')[1]}</div>
                        <div class="light-item-details">
                            ${isOn ? `${light.brightness_pct}% · ${light.kelvin}K` : 'Off'}
                        </div>
                    </div>
                `;
                listContainer.appendChild(listItem);
            });
            
            // Update timestamp
            document.getElementById('last-update').textContent = 
                new Date(data.celestial.timestamp).toLocaleTimeString();
        }
        
        async function fetchState() {
            try {
                const response = await fetch('/app/celestial/api/state');
                if (!response.ok) throw new Error('Failed to fetch state');
                const data = await response.json();
                updateVisualization(data);
            } catch (error) {
                console.error('Error fetching state:', error);
            }
        }
        
        // Initial fetch
        fetchState();
        
        // Poll for updates
        setInterval(fetchState, POLL_INTERVAL);
    </script>
</body>
</html>'''
