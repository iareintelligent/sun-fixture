# Sun-Fixture

A monorepo containing:
1. Python backend that determines celestial positioning and color temperature
2. React TypeScript frontend with MUI, Recoil, and TanStack Query

## Project Components

### Backend
- Python web service for celestial calculations
  - Sun/moon position relative to Earth coordinates
  - Color temperature calculations for sun/moon
  - REST API endpoints

### Frontend
- React + TypeScript application
  - Material UI components
  - Recoil for state management
  - TanStack Query for API communication
  - Visualization of light fixtures

### Integration
- Connect to Philips Hue API
- Control light bulbs based on celestial data
- Virtual bulb visualization

## Implementation Plan
1. Setup monorepo structure
2. Create Python backend with celestial calculation library
3. Implement REST API endpoints
4. Build React frontend with state management
5. Develop Philips Hue integration
6. Create bulb visualization UI
7. Connect frontend to backend API