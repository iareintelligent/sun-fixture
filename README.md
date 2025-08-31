# Celestial Lighting System

An AppDaemon application for Home Assistant that automatically adjusts Philips Hue lights based on sun and moon positions, creating natural lighting that follows celestial patterns.

## Overview

This system runs on Home Assistant Green and provides:
- **Automatic lighting control** based on real-time sun/moon positions
- **Natural color temperature** transitions throughout the day
- **Moon phase-aware** nighttime lighting with subtle colors
- **Physical override** via Lutron Aurora dimmer (Friends of Hue device)
- **Smart scheduling** with 60-second update intervals for smooth transitions

## Architecture

The system consists of:
- **AppDaemon Add-on**: Python runtime environment for Home Assistant
- **Celestial App**: Main Python application with astronomical calculations
- **Home Assistant Integration**: WebSocket connection for real-time control
- **Philips Hue Bridge**: Zigbee communication with bulbs and Aurora dimmer
- **Ephem Library**: Precise moon position and phase calculations

## Features

### Daytime Mode (Sun Above Horizon)
- Color temperature follows sun elevation (2000K-6500K)
- Brightness adjusts based on sun position
- Warm sunrise/sunset colors
- Cool midday light

### Nighttime Mode (Sun Below Horizon)
- Moon phase determines color and intensity
- Subtle RGB colors based on moon altitude
- Automatic dimming for late night
- New moon = minimal light

### Aurora Dimmer Integration
- **Click**: Toggle override mode on/off
- **Rotate**: Manual brightness control when in override
- **Auto-resume**: Returns to celestial control when override disabled

## Installation

### Prerequisites
- Home Assistant Green (or any HA installation)
- AppDaemon Add-on installed
- Philips Hue Bridge configured
- Hue lights and (optionally) Aurora dimmer paired

### Setup Steps

1. **Install AppDaemon Add-on**
   - Navigate to Home Assistant Settings → Add-ons
   - Search for "AppDaemon"
   - Install and start the add-on

2. **Configure AppDaemon**
   - Access AppDaemon configuration
   - Ensure Python packages are available: `ephem`

3. **Deploy Celestial App**
   - Copy `celestial.py` to `/config/appdaemon/apps/`
   - Create `apps.yaml` configuration (see Configuration section)

4. **Configure Home Assistant**
   - Ensure Sun integration is enabled
   - Configure latitude/longitude in HA configuration
   - Set up Hue integration with your bridge

## Configuration

### apps.yaml
```yaml
celestial_lighting:
  module: celestial
  class: CelestialLighting
  lights:
    - light.living_room
    - light.bedroom
    - light.kitchen
  aurora_device_id: "00:17:88:01:XX:XX:XX:XX-XX-XXXX"
  update_interval: 60  # seconds
  location:
    latitude: 37.7749
    longitude: -122.4194
```

### Configuration Parameters
- `lights`: List of Hue light entities to control
- `aurora_device_id`: Device ID from Hue bridge (optional)
- `update_interval`: Seconds between updates (default: 60)
- `location`: Override HA's location if needed

## Development

### Local Development Setup
1. Clone repository to development machine
2. Set up Python virtual environment
3. Install dependencies: `pip install appdaemon ephem`
4. Use Samba share or SSH for file transfer to HA Green

### Testing
- Use AppDaemon's built-in logging
- Monitor via HA Developer Tools → Events
- Test with time simulation in AppDaemon

### File Structure
```
/config/appdaemon/
├── apps/
│   ├── celestial.py       # Main application
│   └── apps.yaml          # Configuration
├── logs/
│   └── appdaemon.log     # Runtime logs
└── compiled/             # AppDaemon cache
```

## Algorithm Details

### Sun Position → Color Temperature
```python
# Elevation ranges from -10° to 90°
# Color temperature from 2000K (horizon) to 6500K (zenith)
kelvin = 2000 + (elevation + 10) * 45
```

### Moon Position → RGB Color
- Phase determines intensity (0-100%)
- Altitude affects color saturation
- Blue-white for high moon, amber for low moon

### Brightness Calculation
- Sun: 100% at zenith, 20% at horizon
- Moon: Scaled by phase percentage
- Override: Manual control via Aurora

## Troubleshooting

### Common Issues

1. **Lights not responding**
   - Check AppDaemon logs: `/config/appdaemon/logs/`
   - Verify Hue bridge connection in HA
   - Ensure light entities are correct

2. **Aurora dimmer not working**
   - Verify device ID in configuration
   - Check Hue event stream in Developer Tools
   - Ensure dimmer is paired as Friends of Hue device

3. **Incorrect sun/moon positions**
   - Verify latitude/longitude in HA configuration
   - Check timezone settings
   - Ensure system time is correct

## Performance

- **CPU Usage**: Minimal (~1% on HA Green)
- **Memory**: ~20MB for AppDaemon + app
- **Network**: REST API calls every 60 seconds
- **Latency**: <100ms response to Aurora events

## Future Enhancements

- [ ] Weather-based adjustments
- [ ] Circadian rhythm optimization
- [ ] Multiple location profiles
- [ ] Vacation/away modes
- [ ] Integration with other smart home systems

## License

MIT License - See LICENSE file for details

## Support

For issues, questions, or contributions:
- GitHub Issues: [your-repo-url]
- Home Assistant Community: [forum-thread]
- Documentation: See ARCHITECTURE.md for detailed system design