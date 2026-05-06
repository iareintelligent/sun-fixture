"""
Sun-Fixture System Dashboard
All-in-one dashboard with network topology, compass light visualization, and git deploy.
Served via AppDaemon on port 5050.
"""

import appdaemon.plugins.hass.hassapi as hass
from aiohttp import web
import json
import math
import subprocess
import os
from datetime import datetime
from typing import Dict, List, Optional


class SystemDashboard(hass.Hass):
    """AppDaemon app that serves a tabbed system dashboard"""

    def initialize(self):
        self.log("System Dashboard initializing...")

        # Light configuration (same as celestial_viz)
        self.directional_lights = self.args.get("directional_lights", {})
        self.aurora_device_id = self.args.get("aurora_device_id", None)

        # Location
        location = self.args.get("location", {})
        self.latitude = location.get("latitude", self.get_state("zone.home", attribute="latitude"))
        self.longitude = location.get("longitude", self.get_state("zone.home", attribute="longitude"))

        # Parse directional lights
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

        # Aurora dimmer tracking
        self.aurora_last_event = None
        if self.aurora_device_id:
            self.listen_event(self._track_aurora, "hue_event", device_id=self.aurora_device_id)

        # Auto-detect repo directory
        self.repo_dir = self.args.get("repo_dir", None)
        if not self.repo_dir:
            self.repo_dir = self._detect_repo_dir()

        # Register routes
        self.register_route(self.serve_dashboard, "dashboard")
        self.register_route(self.serve_api_topology, "dashboard/api/topology")
        self.register_route(self.serve_api_lights, "dashboard/api/lights")
        self.register_route(self.serve_api_git, "dashboard/api/git")
        self.register_route(self.serve_api_deploy, "dashboard/api/deploy")
        self.register_route(self.serve_api_logs, "dashboard/api/logs")

        self.log(f"System Dashboard ready at http://<appdaemon-ip>:5050/app/dashboard")
        self.log(f"Tracking {len(self.light_directions)} lights, repo: {self.repo_dir}")

    # --- Aurora event tracking ---

    def _track_aurora(self, event_name, data, kwargs):
        self.aurora_last_event = datetime.now()

    # --- Repo detection ---

    def _detect_repo_dir(self) -> Optional[str]:
        """Try to find the git repo root."""
        candidates = [
            os.path.dirname(os.path.abspath(__file__)),  # apps/ dir
            "/addon_configs/a0d7b954_appdaemon/apps",
            "/config/appdaemon/apps",
        ]
        for path in candidates:
            try:
                result = subprocess.run(
                    ["git", "-C", path, "rev-parse", "--show-toplevel"],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    return result.stdout.strip()
            except Exception:
                pass
        return None

    # --- Reused helpers from celestial_viz ---

    def direction_to_azimuth(self, direction: str) -> Optional[float]:
        direction_map = {
            "N": 0, "NNE": 22.5, "NE": 45, "ENE": 67.5,
            "E": 90, "ESE": 112.5, "SE": 135, "SSE": 157.5,
            "S": 180, "SSW": 202.5, "SW": 225, "WSW": 247.5,
            "W": 270, "WNW": 292.5, "NW": 315, "NNW": 337.5,
            "NORTH": 0, "EAST": 90, "SOUTH": 180, "WEST": 270
        }
        return direction_map.get(direction)

    def kelvin_to_rgb(self, kelvin: int) -> List[int]:
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

    def get_light_state(self, entity_id: str) -> Dict:
        state = self.get_state(entity_id)
        brightness = self.get_state(entity_id, attribute="brightness") or 0
        color_temp = self.get_state(entity_id, attribute="color_temp")
        rgb_color = self.get_state(entity_id, attribute="rgb_color")
        kelvin = None
        if color_temp:
            try:
                kelvin = int(1000000 / color_temp)
            except Exception:
                pass
        if not kelvin:
            kelvin = 4000
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
        sun_elevation = float(self.get_state("sun.sun", attribute="elevation") or 0)
        sun_azimuth = float(self.get_state("sun.sun", attribute="azimuth") or 0)
        if sun_elevation > -6:
            mode = "sun"
        else:
            mode = "moon"
        return {
            "mode": mode,
            "sun": {"elevation": sun_elevation, "azimuth": sun_azimuth},
            "timestamp": datetime.now().isoformat()
        }

    # --- API endpoints ---

    async def serve_api_topology(self, request, kwargs):
        """Component statuses for the topology view."""
        try:
            # HA Core
            ha_status = "online"
            try:
                self.get_state("sun.sun")
            except Exception:
                ha_status = "offline"

            # AppDaemon - always online if we're serving
            ad_status = "online"

            # Hue Bridge - online if any light is not unavailable
            hue_status = "offline"
            lights = []
            for entity_id in self.light_directions:
                st = self.get_state(entity_id)
                if st and st != "unavailable":
                    hue_status = "online"
                lights.append({
                    "entity_id": entity_id,
                    "direction": self.direction_names.get(entity_id, "?"),
                    "state": st or "unknown"
                })

            # Aurora dimmer
            aurora_status = "unknown"
            aurora_last = None
            if self.aurora_device_id:
                if self.aurora_last_event:
                    age = (datetime.now() - self.aurora_last_event).total_seconds()
                    aurora_status = "online" if age < 86400 else "idle"
                    aurora_last = self.aurora_last_event.isoformat()
                else:
                    aurora_status = "unknown"

            return web.json_response({
                "ha_core": {"status": ha_status},
                "appdaemon": {"status": ad_status},
                "hue_bridge": {"status": hue_status},
                "aurora_dimmer": {
                    "status": aurora_status,
                    "device_id": self.aurora_device_id,
                    "last_event": aurora_last
                },
                "lights": lights,
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            self.log(f"Topology API error: {e}", level="ERROR")
            return web.json_response({"error": str(e)}, status=500)

    async def serve_api_lights(self, request, kwargs):
        """Light states for compass visualization."""
        try:
            lights_state = [self.get_light_state(eid) for eid in self.light_directions]
            celestial = self.get_celestial_data()
            return web.json_response({
                "lights": lights_state,
                "celestial": celestial,
                "config": {"latitude": self.latitude, "longitude": self.longitude}
            })
        except Exception as e:
            self.log(f"Lights API error: {e}", level="ERROR")
            return web.json_response({"error": str(e)}, status=500)

    async def serve_api_git(self, request, kwargs):
        """Git status: branch, last commit, ahead/behind."""
        if not self.repo_dir:
            return web.json_response({"error": "Git repo not found", "configured": False})
        try:
            def git(*args):
                r = subprocess.run(
                    ["git", "-C", self.repo_dir] + list(args),
                    capture_output=True, text=True, timeout=15
                )
                return r.stdout.strip(), r.stderr.strip(), r.returncode

            branch, _, _ = git("rev-parse", "--abbrev-ref", "HEAD")
            log_out, _, _ = git("log", "--oneline", "-1")
            status_out, _, _ = git("status", "--porcelain")
            has_changes = len(status_out) > 0

            # Fetch to check for updates (non-blocking, best-effort)
            git("fetch", "--quiet")
            behind_out, _, rc = git("rev-list", "HEAD..origin/" + branch, "--count")
            behind = int(behind_out) if rc == 0 and behind_out.isdigit() else None
            ahead_out, _, rc = git("rev-list", "origin/" + branch + "..HEAD", "--count")
            ahead = int(ahead_out) if rc == 0 and ahead_out.isdigit() else None

            return web.json_response({
                "configured": True,
                "repo_dir": self.repo_dir,
                "branch": branch,
                "last_commit": log_out,
                "has_local_changes": has_changes,
                "dirty_files": status_out.split("\n") if has_changes else [],
                "commits_behind": behind,
                "commits_ahead": ahead,
            })
        except Exception as e:
            self.log(f"Git API error: {e}", level="ERROR")
            return web.json_response({"error": str(e), "configured": True}, status=500)

    async def serve_api_deploy(self, request, kwargs):
        """Trigger git pull."""
        if request.method != "POST":
            return web.json_response({"error": "POST required"}, status=405)
        if not self.repo_dir:
            return web.json_response({"error": "Git repo not found"}, status=400)
        try:
            result = subprocess.run(
                ["git", "-C", self.repo_dir, "pull"],
                capture_output=True, text=True, timeout=30
            )
            self.log(f"Git pull result: {result.stdout}")
            if result.stderr:
                self.log(f"Git pull stderr: {result.stderr}")
            return web.json_response({
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr if result.returncode != 0 else None
            })
        except Exception as e:
            self.log(f"Deploy error: {e}", level="ERROR")
            return web.json_response({"error": str(e)}, status=500)

    async def serve_api_logs(self, request, kwargs):
        """Tail AppDaemon log file."""
        log_paths = [
            "/addon_configs/a0d7b954_appdaemon/logs/appdaemon.log",
            "/config/appdaemon/appdaemon.log",
            "/conf/logs/appdaemon.log",
        ]
        for path in log_paths:
            if os.path.exists(path):
                try:
                    result = subprocess.run(
                        ["tail", "-n", "50", path],
                        capture_output=True, text=True, timeout=5
                    )
                    return web.json_response({
                        "lines": result.stdout.split("\n"),
                        "path": path
                    })
                except Exception as e:
                    return web.json_response({"error": str(e)}, status=500)
        return web.json_response({"lines": ["Log file not found"], "path": None})

    # --- Dashboard HTML ---

    async def serve_dashboard(self, request, kwargs):
        return web.Response(text=self._dashboard_html(), content_type="text/html")

    def _dashboard_html(self) -> str:
        return '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Sun Fixture Dashboard</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{
  font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
  background:linear-gradient(135deg,#1a1a2e,#16213e,#0f3460);
  min-height:100vh;color:#e0e0e0;
}
/* --- Tab bar --- */
.tab-bar{
  display:flex;position:sticky;top:0;z-index:100;
  background:rgba(15,15,30,0.95);backdrop-filter:blur(10px);
  border-bottom:1px solid rgba(255,255,255,0.1);
}
.tab-btn{
  flex:1;padding:14px 10px;text-align:center;cursor:pointer;
  font-size:0.9em;font-weight:600;color:#888;border:none;background:none;
  transition:all 0.2s;border-bottom:3px solid transparent;
}
.tab-btn:hover{color:#ccc;background:rgba(255,255,255,0.03)}
.tab-btn.active{color:#fff;border-bottom-color:#ffd700}
.tab-content{display:none;padding:20px;max-width:900px;margin:0 auto}
.tab-content.active{display:block}

/* --- Shared --- */
h2{text-align:center;font-size:1.4em;margin-bottom:16px;color:#fff}
.card{background:rgba(255,255,255,0.05);border-radius:12px;padding:16px;margin-bottom:16px}
.status-dot{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:8px}
.status-dot.online{background:#4caf50;box-shadow:0 0 8px rgba(76,175,80,0.6)}
.status-dot.offline{background:#ff6b6b;box-shadow:0 0 8px rgba(255,107,107,0.4)}
.status-dot.unknown{background:#888}
.status-dot.idle{background:#ffd700;box-shadow:0 0 8px rgba(255,215,0,0.4)}
.btn{
  padding:10px 20px;border:none;border-radius:8px;font-size:0.9em;font-weight:600;
  cursor:pointer;transition:all 0.2s;color:#fff;
}
.btn:hover{transform:scale(1.03);box-shadow:0 4px 12px rgba(0,0,0,0.3)}
.btn:active{transform:scale(0.97)}
.btn:disabled{opacity:0.5;cursor:not-allowed;transform:none}
.btn-primary{background:linear-gradient(135deg,#4caf50,#388e3c)}
.btn-warn{background:linear-gradient(135deg,#ff9800,#f57c00)}
.btn-sm{padding:6px 14px;font-size:0.8em}

/* ====== TAB 1: TOPOLOGY ====== */
.topo-svg{width:100%;max-width:700px;margin:0 auto;display:block}
.topo-node{cursor:pointer}
.topo-node rect{rx:10;ry:10;stroke-width:2;transition:all 0.3s}
.topo-node:hover rect{filter:brightness(1.3)}
.topo-node text{fill:#e0e0e0;font-family:inherit;pointer-events:none}
.topo-line{stroke:rgba(255,255,255,0.15);stroke-width:2}
.topo-label{fill:#666;font-size:10px;font-family:inherit}
.node-detail{display:none;margin-top:12px}
.node-detail.visible{display:block}

/* ====== TAB 2: LIGHTS (compass) ====== */
.status-bar{
  display:flex;justify-content:center;gap:30px;margin-bottom:20px;
  padding:15px;background:rgba(255,255,255,0.05);border-radius:12px;flex-wrap:wrap;
}
.status-item{text-align:center}
.status-label{font-size:0.75em;color:#888;text-transform:uppercase;letter-spacing:1px}
.status-value{font-size:1.2em;font-weight:600;color:#fff}
.mode-sun{color:#ffd700}.mode-moon{color:#b0c4de}.mode-off{color:#666}
.visualization{position:relative;width:100%;max-width:600px;margin:0 auto;aspect-ratio:1}
.compass-ring{
  position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);
  width:90%;height:90%;border:2px solid rgba(255,255,255,0.15);border-radius:50%;
}
.compass-ring.inner{width:60%;height:60%;border-style:dashed;border-color:rgba(255,255,255,0.08)}
.compass-labels{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:100%;height:100%}
.compass-label{position:absolute;font-size:0.85em;color:rgba(255,255,255,0.4);font-weight:500}
.compass-label.n{top:2%;left:50%;transform:translateX(-50%)}
.compass-label.s{bottom:2%;left:50%;transform:translateX(-50%)}
.compass-label.e{right:2%;top:50%;transform:translateY(-50%)}
.compass-label.w{left:2%;top:50%;transform:translateY(-50%)}
.light-container{position:absolute;top:50%;left:50%;width:100%;height:100%;transform:translate(-50%,-50%)}
.light{position:absolute;transform:translate(-50%,-50%);transition:all 0.5s ease}
.light-circle{
  width:70px;height:70px;border-radius:50%;display:flex;align-items:center;
  justify-content:center;flex-direction:column;transition:all 0.5s ease;
  box-shadow:0 0 30px rgba(255,255,255,0.1);border:2px solid rgba(255,255,255,0.2);
}
.light-circle.on{box-shadow:0 0 40px var(--light-color),0 0 80px var(--light-color-dim)}
.light-circle.off{background:rgba(30,30,40,0.8)!important;box-shadow:none}
.light-direction{font-size:0.9em;font-weight:700;color:rgba(0,0,0,0.7);text-shadow:0 1px 2px rgba(255,255,255,0.3)}
.light-circle.off .light-direction{color:rgba(255,255,255,0.3)}
.light-brightness{font-size:0.7em;color:rgba(0,0,0,0.5)}
.light-circle.off .light-brightness{color:rgba(255,255,255,0.2)}
.celestial-body{
  position:absolute;transform:translate(-50%,-50%);width:40px;height:40px;border-radius:50%;
  display:flex;align-items:center;justify-content:center;font-size:1.5em;transition:all 1s ease;z-index:10;
}
.celestial-body.sun{background:radial-gradient(circle,#fff9c4,#ffeb3b 50%,#ff9800);box-shadow:0 0 30px #ffeb3b,0 0 60px #ff9800}
.celestial-body.moon{background:radial-gradient(circle,#fff,#e0e0e0 50%,#b0c4de);box-shadow:0 0 20px rgba(176,196,222,0.5)}
.center-info{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);text-align:center;z-index:5}
.center-info .fixture-icon{font-size:2em;margin-bottom:5px}
.center-info .fixture-label{font-size:0.7em;color:rgba(255,255,255,0.5);text-transform:uppercase;letter-spacing:2px}
.light-list{margin-top:20px;display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:10px}
.light-item{background:rgba(255,255,255,0.05);border-radius:8px;padding:12px;display:flex;align-items:center;gap:12px}
.light-item-indicator{width:24px;height:24px;border-radius:50%;flex-shrink:0}
.light-item-info{flex:1;min-width:0}
.light-item-name{font-size:0.85em;font-weight:500;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.light-item-details{font-size:0.7em;color:#888}
@keyframes pulse{0%,100%{transform:translate(-50%,-50%) scale(1)}50%{transform:translate(-50%,-50%) scale(1.05)}}
.celestial-body.sun{animation:pulse 4s ease-in-out infinite}

/* ====== TAB 3: DEPLOY ====== */
.deploy-status{display:flex;align-items:center;gap:12px;margin-bottom:12px}
.deploy-badge{
  padding:4px 12px;border-radius:12px;font-size:0.8em;font-weight:600;
}
.deploy-badge.uptodate{background:rgba(76,175,80,0.2);color:#4caf50}
.deploy-badge.behind{background:rgba(255,152,0,0.2);color:#ff9800}
.deploy-badge.deploying{background:rgba(33,150,243,0.2);color:#2196f3}
.deploy-badge.error{background:rgba(255,107,107,0.2);color:#ff6b6b}
.deploy-badge.unconfigured{background:rgba(136,136,136,0.2);color:#888}
.git-info{font-size:0.85em;color:#aaa;margin-bottom:8px}
.git-info code{background:rgba(255,255,255,0.08);padding:2px 6px;border-radius:4px;font-size:0.95em;color:#e0e0e0}
.deploy-output{
  background:rgba(0,0,0,0.3);border-radius:8px;padding:12px;font-family:monospace;
  font-size:0.8em;white-space:pre-wrap;max-height:200px;overflow-y:auto;margin-top:12px;color:#aaa;
  display:none;
}
.deploy-output.visible{display:block}
.log-viewer{
  background:rgba(0,0,0,0.3);border-radius:8px;padding:12px;font-family:monospace;
  font-size:0.75em;white-space:pre-wrap;max-height:350px;overflow-y:auto;color:#999;
  line-height:1.5;
}
.deploy-actions{display:flex;gap:10px;margin-top:12px}
.update-time{text-align:center;margin-top:20px;font-size:0.75em;color:#666}
</style>
</head>
<body>

<div class="tab-bar">
  <button class="tab-btn active" onclick="switchTab('system')">System</button>
  <button class="tab-btn" onclick="switchTab('lights')">Lights</button>
  <button class="tab-btn" onclick="switchTab('deploy')">Deploy</button>
</div>

<!-- ===================== TAB 1: SYSTEM TOPOLOGY ===================== -->
<div id="tab-system" class="tab-content active">
  <h2>System Topology</h2>

  <svg class="topo-svg" viewBox="0 0 500 420" xmlns="http://www.w3.org/2000/svg">
    <!-- Connection lines -->
    <line class="topo-line" x1="100" y1="50" x2="250" y2="50"/>
    <text class="topo-label" x="170" y="42">SSH / Git</text>

    <line class="topo-line" x1="250" y1="70" x2="175" y2="150"/>
    <line class="topo-line" x1="250" y1="70" x2="340" y2="150"/>

    <line class="topo-line" x1="175" y1="190" x2="175" y2="260"/>
    <text class="topo-label" x="183" y="230">REST</text>

    <line class="topo-line" x1="340" y1="190" x2="340" y2="260" stroke-dasharray="6,4"/>
    <text class="topo-label" x="348" y="230">WebSocket</text>

    <!-- Hue Bridge to bulbs -->
    <line class="topo-line" x1="175" y1="300" x2="100" y2="370"/>
    <line class="topo-line" x1="175" y1="300" x2="250" y2="370"/>
    <text class="topo-label" x="110" y="340">Zigbee</text>

    <!-- Hue Bridge to Aurora -->
    <line class="topo-line" x1="175" y1="300" x2="400" y2="370"/>
    <text class="topo-label" x="280" y="340">Zigbee</text>

    <!-- Nodes -->
    <g class="topo-node" data-node="developer" onclick="showNodeDetail('developer')">
      <rect x="10" y="30" width="110" height="40" fill="#2a2a4a" stroke="#555"/>
      <text x="65" y="55" text-anchor="middle" font-size="12">Developer Mac</text>
    </g>
    <g class="topo-node" data-node="ha_green" onclick="showNodeDetail('ha_green')">
      <rect x="190" y="30" width="120" height="40" fill="#2a2a4a" stroke="#555"/>
      <text x="250" y="55" text-anchor="middle" font-size="12">HA Green</text>
    </g>
    <g class="topo-node" data-node="ha_core" onclick="showNodeDetail('ha_core')">
      <rect x="110" y="150" width="130" height="40" fill="#1a3a5a" stroke="#555" id="node-ha-core"/>
      <text x="175" y="175" text-anchor="middle" font-size="12">Home Assistant</text>
      <circle cx="230" cy="160" r="5" id="dot-ha-core" fill="#888"/>
    </g>
    <g class="topo-node" data-node="appdaemon" onclick="showNodeDetail('appdaemon')">
      <rect x="275" y="150" width="130" height="40" fill="#1a3a5a" stroke="#555" id="node-appdaemon"/>
      <text x="340" y="168" text-anchor="middle" font-size="12">AppDaemon</text>
      <text x="340" y="182" text-anchor="middle" font-size="9" fill="#888">celestial, dashboard</text>
      <circle cx="395" cy="160" r="5" id="dot-appdaemon" fill="#4caf50"/>
    </g>
    <g class="topo-node" data-node="hue_bridge" onclick="showNodeDetail('hue_bridge')">
      <rect x="110" y="260" width="130" height="40" fill="#2a2a4a" stroke="#555" id="node-hue-bridge"/>
      <text x="175" y="285" text-anchor="middle" font-size="12">Hue Bridge</text>
      <circle cx="230" cy="270" r="5" id="dot-hue-bridge" fill="#888"/>
    </g>
    <g class="topo-node" data-node="bulbs" onclick="showNodeDetail('bulbs')">
      <rect x="30" y="350" width="140" height="40" fill="#2a2a4a" stroke="#555" id="node-bulbs"/>
      <text x="100" y="375" text-anchor="middle" font-size="12" id="text-bulbs">8 Bulbs</text>
      <circle cx="160" cy="360" r="5" id="dot-bulbs" fill="#888"/>
    </g>
    <g class="topo-node" data-node="celestial_app" onclick="showNodeDetail('celestial_app')">
      <rect x="185" y="350" width="130" height="40" fill="#2a2a4a" stroke="#555"/>
      <text x="250" y="375" text-anchor="middle" font-size="12">celestial.py</text>
    </g>
    <g class="topo-node" data-node="aurora" onclick="showNodeDetail('aurora')">
      <rect x="330" y="350" width="140" height="40" fill="#2a2a4a" stroke="#555" id="node-aurora"/>
      <text x="400" y="375" text-anchor="middle" font-size="12">Aurora Dimmer</text>
      <circle cx="460" cy="360" r="5" id="dot-aurora" fill="#888"/>
    </g>
  </svg>

  <div class="card node-detail" id="node-detail">
    <div id="node-detail-content"></div>
  </div>

  <div class="update-time">Topology updates every 5s &middot; Last: <span id="topo-update-time">--</span></div>
</div>

<!-- ===================== TAB 2: LIGHTS ===================== -->
<div id="tab-lights" class="tab-content">
  <h2>Celestial Lighting</h2>
  <div class="status-bar">
    <div class="status-item"><div class="status-label">Mode</div><div class="status-value" id="mode">--</div></div>
    <div class="status-item"><div class="status-label">Elevation</div><div class="status-value" id="sun-elevation">--</div></div>
    <div class="status-item"><div class="status-label">Azimuth</div><div class="status-value" id="sun-azimuth">--</div></div>
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
    <div class="center-info"><div class="fixture-icon">&#x1F4A1;</div><div class="fixture-label">Sun Fixture</div></div>
    <div class="light-container" id="lights-container"></div>
    <div class="celestial-body sun" id="celestial-body">&#x2600;&#xFE0F;</div>
  </div>
  <div class="light-list" id="light-list"></div>
  <div class="update-time">Last update: <span id="lights-update-time">--</span></div>
</div>

<!-- ===================== TAB 3: DEPLOY ===================== -->
<div id="tab-deploy" class="tab-content">
  <h2>Deploy</h2>
  <div class="card">
    <div class="deploy-status">
      <span class="deploy-badge unconfigured" id="deploy-badge">Checking...</span>
    </div>
    <div class="git-info" id="git-branch"></div>
    <div class="git-info" id="git-commit"></div>
    <div class="git-info" id="git-changes"></div>
    <div class="deploy-actions">
      <button class="btn btn-primary btn-sm" id="btn-check" onclick="checkGit()">Check for Updates</button>
      <button class="btn btn-warn btn-sm" id="btn-deploy" onclick="deploy()" disabled>Deploy (git pull)</button>
    </div>
    <div class="deploy-output" id="deploy-output"></div>
  </div>

  <div class="card">
    <h3 style="font-size:0.9em;margin-bottom:10px;color:#aaa">AppDaemon Logs</h3>
    <button class="btn btn-sm" style="background:#333;margin-bottom:10px" onclick="fetchLogs()">Refresh Logs</button>
    <div class="log-viewer" id="log-viewer">Loading logs...</div>
  </div>
</div>

<script>
/* ===== Tab switching ===== */
function switchTab(name) {
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
  document.getElementById('tab-' + name).classList.add('active');
  document.querySelector(`.tab-btn[onclick="switchTab('${name}')"]`).classList.add('active');
  // Trigger initial fetch for the tab
  if (name === 'system') fetchTopology();
  if (name === 'lights') fetchLights();
  if (name === 'deploy') { checkGit(); fetchLogs(); }
}

/* ===== Polling ===== */
let topoTimer, lightsTimer;
function startPolling() {
  topoTimer = setInterval(fetchTopology, 5000);
  lightsTimer = setInterval(fetchLights, 2000);
}

/* ===== TAB 1: Topology ===== */
const statusColors = {online:'#4caf50', offline:'#ff6b6b', unknown:'#888', idle:'#ffd700'};
let lastTopo = null;

async function fetchTopology() {
  try {
    const r = await fetch('/app/dashboard/api/topology');
    const d = await r.json();
    lastTopo = d;
    setDot('dot-ha-core', d.ha_core.status);
    setDot('dot-appdaemon', d.appdaemon.status);
    setDot('dot-hue-bridge', d.hue_bridge.status);
    setDot('dot-aurora', d.aurora_dimmer.status);

    // Bulbs summary
    const onCount = d.lights.filter(l => l.state === 'on').length;
    const totalCount = d.lights.length;
    document.getElementById('text-bulbs').textContent = `${onCount}/${totalCount} Bulbs On`;
    setDot('dot-bulbs', onCount > 0 ? 'online' : (d.lights.some(l => l.state === 'unavailable') ? 'offline' : 'unknown'));

    document.getElementById('topo-update-time').textContent = new Date(d.timestamp).toLocaleTimeString();
  } catch(e) { console.error('Topology fetch error:', e); }
}

function setDot(id, status) {
  const el = document.getElementById(id);
  if (el) el.setAttribute('fill', statusColors[status] || '#888');
}

function showNodeDetail(node) {
  const box = document.getElementById('node-detail');
  const content = document.getElementById('node-detail-content');
  if (!lastTopo) { content.innerHTML = 'Loading...'; box.classList.add('visible'); return; }

  let html = '';
  switch(node) {
    case 'ha_core':
      html = `<strong>Home Assistant Core</strong><br><span class="status-dot ${lastTopo.ha_core.status}"></span>${lastTopo.ha_core.status}`;
      break;
    case 'appdaemon':
      html = `<strong>AppDaemon</strong><br><span class="status-dot online"></span>online<br><small>Running: celestial.py, system_dashboard.py</small>`;
      break;
    case 'hue_bridge':
      html = `<strong>Philips Hue Bridge</strong><br><span class="status-dot ${lastTopo.hue_bridge.status}"></span>${lastTopo.hue_bridge.status}`;
      break;
    case 'aurora':
      html = `<strong>Lutron Aurora Dimmer</strong><br><span class="status-dot ${lastTopo.aurora_dimmer.status}"></span>${lastTopo.aurora_dimmer.status}`;
      if (lastTopo.aurora_dimmer.last_event) html += `<br><small>Last event: ${new Date(lastTopo.aurora_dimmer.last_event).toLocaleString()}</small>`;
      if (lastTopo.aurora_dimmer.device_id) html += `<br><small>Device: ${lastTopo.aurora_dimmer.device_id}</small>`;
      break;
    case 'bulbs':
      html = '<strong>Directional Bulbs</strong><br>' + lastTopo.lights.map(l =>
        `<span class="status-dot ${l.state === 'on' ? 'online' : l.state === 'unavailable' ? 'offline' : 'unknown'}"></span>${l.direction}: ${l.state} (${l.entity_id})`
      ).join('<br>');
      break;
    default:
      html = `<strong>${node.replace('_',' ')}</strong>`;
  }
  content.innerHTML = html;
  box.classList.add('visible');
}

/* ===== TAB 2: Lights ===== */
function azimuthToPosition(az, radius=42) {
  const rad = (az - 90) * (Math.PI / 180);
  return { x: 50 + radius * Math.cos(rad), y: 50 + radius * Math.sin(rad) };
}

async function fetchLights() {
  try {
    const r = await fetch('/app/dashboard/api/lights');
    const d = await r.json();
    const container = document.getElementById('lights-container');
    const list = document.getElementById('light-list');
    container.innerHTML = '';
    list.innerHTML = '';

    const mode = d.celestial.mode;
    const modeEl = document.getElementById('mode');
    modeEl.textContent = mode.toUpperCase();
    modeEl.className = 'status-value mode-' + mode;
    document.getElementById('sun-elevation').textContent = d.celestial.sun.elevation.toFixed(1) + '\\u00B0';
    document.getElementById('sun-azimuth').textContent = d.celestial.sun.azimuth.toFixed(1) + '\\u00B0';

    const cb = document.getElementById('celestial-body');
    const cp = azimuthToPosition(d.celestial.sun.azimuth, 38);
    cb.style.left = cp.x + '%'; cb.style.top = cp.y + '%';
    if (mode === 'sun') { cb.className = 'celestial-body sun'; cb.innerHTML = '\\u2600\\uFE0F'; }
    else { cb.className = 'celestial-body moon'; cb.innerHTML = '\\uD83C\\uDF19'; }

    d.lights.forEach(light => {
      const pos = azimuthToPosition(light.azimuth, 38);
      const isOn = light.state === 'on' && light.brightness > 0;
      const color = `rgb(${light.rgb[0]},${light.rgb[1]},${light.rgb[2]})`;
      const dim = `rgba(${light.rgb[0]},${light.rgb[1]},${light.rgb[2]},0.3)`;
      const opacity = isOn ? 0.3 + (light.brightness_pct/100)*0.7 : 0.2;
      const scale = isOn ? 0.8 + (light.brightness_pct/100)*0.4 : 0.8;

      const el = document.createElement('div');
      el.className = 'light';
      el.style.left = pos.x + '%'; el.style.top = pos.y + '%';
      el.innerHTML = `<div class="light-circle ${isOn?'on':'off'}"
        style="background:${isOn?color:'rgba(30,30,40,0.8)'};--light-color:${color};--light-color-dim:${dim};transform:scale(${scale});opacity:${opacity}">
        <span class="light-direction">${light.direction}</span>
        <span class="light-brightness">${light.brightness_pct}%</span></div>`;
      container.appendChild(el);

      const li = document.createElement('div');
      li.className = 'light-item';
      li.innerHTML = `<div class="light-item-indicator" style="background:${isOn?color:'#333'};box-shadow:${isOn?'0 0 10px '+dim:'none'}"></div>
        <div class="light-item-info"><div class="light-item-name">${light.direction} - ${light.entity_id.split('.')[1]}</div>
        <div class="light-item-details">${isOn?light.brightness_pct+'% \\u00B7 '+light.kelvin+'K':'Off'}</div></div>`;
      list.appendChild(li);
    });
    document.getElementById('lights-update-time').textContent = new Date(d.celestial.timestamp).toLocaleTimeString();
  } catch(e) { console.error('Lights fetch error:', e); }
}

/* ===== TAB 3: Deploy ===== */
async function checkGit() {
  const badge = document.getElementById('deploy-badge');
  const btnDeploy = document.getElementById('btn-deploy');
  badge.textContent = 'Checking...';
  badge.className = 'deploy-badge';
  try {
    const r = await fetch('/app/dashboard/api/git');
    const d = await r.json();
    if (!d.configured) {
      badge.textContent = 'Git not configured';
      badge.className = 'deploy-badge unconfigured';
      document.getElementById('git-branch').innerHTML = '<em>Git repo not found. Ensure git is installed and the apps directory is a git repo.</em>';
      document.getElementById('git-commit').textContent = '';
      document.getElementById('git-changes').textContent = '';
      btnDeploy.disabled = true;
      return;
    }
    if (d.error) {
      badge.textContent = 'Error';
      badge.className = 'deploy-badge error';
      document.getElementById('git-branch').textContent = d.error;
      return;
    }
    document.getElementById('git-branch').innerHTML = 'Branch: <code>' + d.branch + '</code>';
    document.getElementById('git-commit').innerHTML = 'Latest: <code>' + d.last_commit + '</code>';
    document.getElementById('git-changes').textContent = d.has_local_changes ? 'Local changes detected' : 'Clean working tree';

    if (d.commits_behind !== null && d.commits_behind > 0) {
      badge.textContent = d.commits_behind + ' commit' + (d.commits_behind > 1 ? 's' : '') + ' behind';
      badge.className = 'deploy-badge behind';
      btnDeploy.disabled = false;
    } else {
      badge.textContent = 'Up to date';
      badge.className = 'deploy-badge uptodate';
      btnDeploy.disabled = true;
    }
  } catch(e) {
    badge.textContent = 'Error';
    badge.className = 'deploy-badge error';
    console.error('Git check error:', e);
  }
}

async function deploy() {
  if (!confirm('Pull latest code from GitHub? AppDaemon will auto-reload changed apps.')) return;
  const badge = document.getElementById('deploy-badge');
  const output = document.getElementById('deploy-output');
  const btnDeploy = document.getElementById('btn-deploy');
  badge.textContent = 'Deploying...';
  badge.className = 'deploy-badge deploying';
  btnDeploy.disabled = true;
  output.classList.add('visible');
  output.textContent = 'Running git pull...\\n';
  try {
    const r = await fetch('/app/dashboard/api/deploy', {method:'POST'});
    const d = await r.json();
    output.textContent += d.output || '';
    if (d.error) output.textContent += '\\nError: ' + d.error;
    if (d.success) {
      badge.textContent = 'Deployed!';
      badge.className = 'deploy-badge uptodate';
      setTimeout(checkGit, 3000);
    } else {
      badge.textContent = 'Deploy failed';
      badge.className = 'deploy-badge error';
    }
  } catch(e) {
    output.textContent += '\\nFetch error: ' + e.message;
    badge.textContent = 'Deploy failed';
    badge.className = 'deploy-badge error';
  }
}

async function fetchLogs() {
  try {
    const r = await fetch('/app/dashboard/api/logs');
    const d = await r.json();
    const viewer = document.getElementById('log-viewer');
    viewer.textContent = d.lines.join('\\n');
    viewer.scrollTop = viewer.scrollHeight;
  } catch(e) {
    document.getElementById('log-viewer').textContent = 'Failed to load logs: ' + e.message;
  }
}

/* ===== Init ===== */
fetchTopology();
fetchLights();
startPolling();
</script>
</body>
</html>'''
