#!/usr/bin/env python3
"""
Test script for Celestial Lighting System
Simulates Aurora dimmer events to test the AppDaemon app
"""

import asyncio
import websocket
import json
import time
from datetime import datetime
import argparse

class CelestialLightingTester:
    def __init__(self, ha_url, ha_token):
        """Initialize the tester with Home Assistant connection details"""
        self.ha_url = ha_url.replace("http://", "ws://").replace("https://", "wss://")
        self.ha_token = ha_token
        self.ws = None
        self.msg_id = 1
        
    def connect(self):
        """Connect to Home Assistant WebSocket API"""
        ws_url = f"{self.ha_url}/api/websocket"
        print(f"Connecting to {ws_url}...")
        
        self.ws = websocket.WebSocket()
        self.ws.connect(ws_url)
        
        # Wait for auth request
        auth_msg = json.loads(self.ws.recv())
        print(f"Auth required: {auth_msg['type']}")
        
        # Send auth
        self.ws.send(json.dumps({
            "type": "auth",
            "access_token": self.ha_token
        }))
        
        # Check auth response
        auth_result = json.loads(self.ws.recv())
        if auth_result["type"] == "auth_ok":
            print("✅ Authentication successful")
            return True
        else:
            print(f"❌ Authentication failed: {auth_result}")
            return False
    
    def send_event(self, event_type, event_data):
        """Send an event to Home Assistant"""
        msg = {
            "id": self.msg_id,
            "type": "fire_event",
            "event_type": event_type,
            "event_data": event_data
        }
        self.msg_id += 1
        
        print(f"Sending event: {event_type}")
        print(f"  Data: {json.dumps(event_data, indent=2)}")
        
        self.ws.send(json.dumps(msg))
        response = json.loads(self.ws.recv())
        
        if response.get("success"):
            print("  ✅ Event sent successfully")
        else:
            print(f"  ❌ Failed to send event: {response}")
        
        return response.get("success", False)
    
    def simulate_button_press(self):
        """Simulate Aurora button press (cycles through modes)"""
        print("\n🔘 Simulating button press...")
        
        # Initial press event
        self.send_event("hue_event", {
            "id": "lutron_aurora_19_button",
            "device_id": "131f93a35892fd3c7a0cc89d3a585d9e",
            "unique_id": "c802b8c6-fec8-4be9-b97c-35ace6246161",
            "type": "initial_press",
            "subtype": 1,
            "metadata": {
                "time_fired": datetime.utcnow().isoformat() + "Z",
                "origin": "LOCAL",
                "context": {
                    "id": f"test_{int(time.time())}",
                    "parent_id": None,
                    "user_id": None
                }
            }
        })
        
        # Wait 100ms
        time.sleep(0.1)
        
        # Release event
        self.send_event("hue_event", {
            "id": "lutron_aurora_19_button",
            "device_id": "131f93a35892fd3c7a0cc89d3a585d9e",
            "unique_id": "c802b8c6-fec8-4be9-b97c-35ace6246161",
            "type": "short_release",
            "subtype": 1,
            "metadata": {
                "time_fired": datetime.utcnow().isoformat() + "Z",
                "origin": "LOCAL",
                "context": {
                    "id": f"test_{int(time.time())}",
                    "parent_id": None,
                    "user_id": None
                }
            }
        })
    
    def simulate_clockwise_rotation(self, steps=200):
        """Simulate clockwise rotation (increase brightness)"""
        print(f"\n🔄 Simulating clockwise rotation ({steps} steps)...")
        
        self.send_event("hue_event", {
            "device_id": "131f93a35892fd3c7a0cc89d3a585d9e",
            "unique_id": "9615fc6f-1c14-4d8e-ba11-c6ce7c6a1446",
            "type": "start",
            "subtype": "clock_wise",
            "duration": 400,
            "steps": steps,
            "metadata": {
                "time_fired": datetime.utcnow().isoformat() + "Z",
                "origin": "LOCAL",
                "context": {
                    "id": f"test_{int(time.time())}",
                    "parent_id": None,
                    "user_id": None
                }
            }
        })
    
    def simulate_counter_clockwise_rotation(self, steps=200):
        """Simulate counter-clockwise rotation (decrease brightness)"""
        print(f"\n🔄 Simulating counter-clockwise rotation ({steps} steps)...")
        
        self.send_event("hue_event", {
            "device_id": "131f93a35892fd3c7a0cc89d3a585d9e",
            "unique_id": "9615fc6f-1c14-4d8e-ba11-c6ce7c6a1446",
            "type": "start",
            "subtype": "counter_clock_wise",
            "duration": 400,
            "steps": steps,
            "metadata": {
                "time_fired": datetime.utcnow().isoformat() + "Z",
                "origin": "LOCAL",
                "context": {
                    "id": f"test_{int(time.time())}",
                    "parent_id": None,
                    "user_id": None
                }
            }
        })
    
    def run_full_test(self):
        """Run a full test sequence"""
        print("\n" + "="*50)
        print("Starting Full Test Sequence")
        print("="*50)
        
        # Test 1: Cycle through all modes
        print("\n📋 Test 1: Mode Cycling")
        print("Expected: Sun → Moon → Off → Sun")
        
        for i in range(3):
            self.simulate_button_press()
            time.sleep(2)  # Wait for lights to update
            print(f"  Mode change {i+1} complete")
        
        # Test 2: Brightness adjustment in Sun mode
        print("\n📋 Test 2: Brightness Control in Sun Mode")
        
        # Make sure we're in Sun mode
        self.simulate_button_press()  # Should be back to Sun
        time.sleep(2)
        
        # Increase brightness
        print("  Increasing brightness...")
        self.simulate_clockwise_rotation(300)
        time.sleep(2)
        
        # Decrease brightness
        print("  Decreasing brightness...")
        self.simulate_counter_clockwise_rotation(500)
        time.sleep(2)
        
        # Test 3: Moon mode with brightness
        print("\n📋 Test 3: Moon Mode Brightness")
        
        # Switch to Moon mode
        self.simulate_button_press()
        time.sleep(2)
        
        # Adjust brightness in moon mode
        print("  Adjusting moon brightness...")
        self.simulate_clockwise_rotation(200)
        time.sleep(2)
        
        # Test 4: Off mode (should not respond to rotation)
        print("\n📋 Test 4: Off Mode")
        
        # Switch to Off mode
        self.simulate_button_press()
        time.sleep(2)
        
        # Try to adjust brightness (should have no effect)
        print("  Testing rotation in off mode (should have no effect)...")
        self.simulate_clockwise_rotation(200)
        time.sleep(2)
        
        print("\n" + "="*50)
        print("Test Sequence Complete!")
        print("="*50)
        print("\nCheck AppDaemon logs to verify:")
        print("  1. Mode changes logged correctly")
        print("  2. Brightness adjustments logged")
        print("  3. Correct lights activated in each mode")
        print("  4. No errors in the log")
    
    def run_interactive(self):
        """Run in interactive mode"""
        print("\n" + "="*50)
        print("Interactive Test Mode")
        print("="*50)
        print("\nCommands:")
        print("  b - Button press (cycle mode)")
        print("  c - Clockwise rotation (increase brightness)")
        print("  a - Counter-clockwise rotation (decrease brightness)")
        print("  f - Run full test sequence")
        print("  q - Quit")
        print("")
        
        while True:
            cmd = input("Enter command: ").lower().strip()
            
            if cmd == 'b':
                self.simulate_button_press()
            elif cmd == 'c':
                steps = input("  Steps (default 200): ").strip()
                steps = int(steps) if steps else 200
                self.simulate_clockwise_rotation(steps)
            elif cmd == 'a':
                steps = input("  Steps (default 200): ").strip()
                steps = int(steps) if steps else 200
                self.simulate_counter_clockwise_rotation(steps)
            elif cmd == 'f':
                self.run_full_test()
            elif cmd == 'q':
                print("Goodbye!")
                break
            else:
                print("Unknown command. Try again.")
    
    def close(self):
        """Close WebSocket connection"""
        if self.ws:
            self.ws.close()
            print("Connection closed")


def main():
    parser = argparse.ArgumentParser(description='Test Celestial Lighting System')
    parser.add_argument('--url', default='http://homeassistant.local:8123',
                        help='Home Assistant URL')
    parser.add_argument('--token', required=True,
                        help='Home Assistant long-lived access token')
    parser.add_argument('--mode', choices=['full', 'interactive'], default='interactive',
                        help='Test mode: full (automated) or interactive')
    
    args = parser.parse_args()
    
    # Create tester
    tester = CelestialLightingTester(args.url, args.token)
    
    try:
        # Connect to Home Assistant
        if not tester.connect():
            print("Failed to connect to Home Assistant")
            return 1
        
        # Run tests
        if args.mode == 'full':
            tester.run_full_test()
        else:
            tester.run_interactive()
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"Error: {e}")
        return 1
    finally:
        tester.close()
    
    return 0


if __name__ == "__main__":
    exit(main())