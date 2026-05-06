# Mission

This file is the source of truth for project scope. Two sections:

1. **Floorplan dashboard mission** — verbatim from the original seed prompt that kicked off this project. Captures the original, narrower mission.
2. **Broader umbrella scope** — Bungalow Fortress Automation, the device-management project of which the floorplan dashboard is the primary visualization.

Both are in scope. The floorplan dashboard is the most concrete near-term deliverable; the broader umbrella explains *why* it has the shape it does.

---

## 1. Floorplan dashboard mission

Build a custom Home Assistant Lovelace dashboard that replaces the default room/entity list with a **multi-floor isometric floorplan view of the user's actual home**, where:

- Every Philips Hue light in the house appears in its true location, with the correct color and brightness rendered live on the floorplan as the bulb's state changes.
- Floor switching uses a vertical floor-selector rail on the left edge of the dashboard.
- Tapping a room opens a popover with that room's non-light controls (climate, media, covers, scenes). Lights are controllable from the map directly.
- The dashboard is the primary interface on at least one wall-mounted tablet and works on the user's phone.
- A traditional fallback dashboard view exists in parallel for guests, kids, and emergencies — same data, different presentation.

**Visual direction (decided, recorded in ADR-0001):** 3D dollhouse aesthetic rendered as a **fixed-angle isometric view per floor**. The 3D model is built in Sweet Home 3D from the user's room dimensions; per-floor isometric renders (lights-off base, plus per-light masks for color/brightness blending) are exported as PNGs and composed in Home Assistant via the Picture Elements card. This is *not* a live-rotating three.js dollhouse — the view is static-angle, which matches the Reddit-trend aesthetic the user wants and dramatically simplifies the tooling stack.

**Constraints and starting state:**

- Home Assistant is already running and operational.
- Every light in the house is a Philips Hue bulb, exposed to HA as `light.*` entities.
- The user has 9–12 rooms across multiple floors.
- The user has accurate room dimensions for every room.
- The user has strong Photoshop skills and the time to use them.
- The user does *not* yet have: a Sweet Home 3D model of the home, photos of every room, exported isometric renders, or a populated room/light inventory.

**Out of scope** (do not propose work on these unless explicitly asked later):

- Replacing Hue with another lighting system.
- Building HA integrations from scratch.
- Energy / solar / EV dashboards (separate dashboard, not this one).
- Cameras / security / NVR (separate dashboard).
- Voice assistant configuration.
- Free-rotation 3D dollhouse with live three.js rendering. We chose static isometric. Revisit only if static proves inadequate.

**"Done" looks like:**

A wall-mounted tablet shows the isometric dashboard at idle. Walking into the kitchen and turning on the Hue lights via the wall switch causes the kitchen on the dashboard to light up with the same color the bulbs emit, within ~2 seconds. Tapping the bedroom on the dashboard opens a popover with the bedroom's thermostat, speaker, and blinds controls. The user has not opened the standard Home Assistant UI in three weeks because they didn't need to.

---

## 2. Broader umbrella scope: Bungalow Fortress Automation

The floorplan dashboard is one face of a larger system: a Home Assistant–backed **device management system** for the user and their wife to use *in conjunction with* the home's physical switches and sensors.

### Core capabilities the umbrella should provide

- **Input device registry.** Every input the home exposes — Lutron dimmers (e.g., Lutron Aurora Friends-of-Hue dimmers), motion sensors, future wall switches, future occupancy sensors — has an entry. Entries record HA entity ID, physical location, type, and current behavior bindings.
- **Output device registry.** Every output the home controls — Philips Hue groups, the Nest thermostat, the existing sun-fixture, media surfaces (Spotify rooms, PlayStation power state) — has an entry. Entries record HA entity ID, capabilities (color/CCT/dimmable, on/off, etc.), and current state.
- **Behavior assignment.** The user can view, unassign, reassign, and define new behaviors mapping inputs to outputs. Examples:
  - "This dimmer in the bedroom controls those Hue lights, and at night also dims the sun-fixture."
  - "When motion is detected in the hallway between 11 PM and 6 AM, fade the hallway Hue group to 20% red."
  - "Disable any light automation in the kid's room when Spotify is playing there."
- **Read-only is acceptable for MVP.** Showing the bound behaviors and current state of every device is the minimum bar. Edit-mode (rebinding inputs/outputs from the dashboard) is the next layer.
- **Sun-fixture as a managed subsystem.** The existing sun-fixture AppDaemon code (in `sun-fixture/`) keeps running. It surfaces in the dashboard as a single output ("sun fixture, 8 bulbs, single fixture in [room]") with read-out of current celestial-driven color/brightness curve. Eventually, the user can override or disable it from the dashboard.
- **The floorplan dashboard is the primary visualization.** Every room shows its lights live. Tapping a room reveals its non-light controls and the input devices bound to it. Tapping an input device shows what it currently controls.
- **Stretch goal — replace the Philips Hue app.** Long-term, every action the user does in the Hue app (bulb pairing, room organization, scene editing, schedules) should be doable from this dashboard. **Explicitly NOT MVP.** Tracked here so MVP decisions stay compatible with eventual feasibility.

### Why this matters

The user wants to stop using the Philips Hue app, the Lutron app, and (eventually) the Nest app. They want a single surface — wall tablet and phone — that reflects their home's actual structure and lets them reason about device behavior in spatial terms. Device manufacturers' apps are siloed; the home is not.

### Sun-fixture's place in the umbrella

The original repo was `sun-fixture/` — a single AppDaemon application driving 8 Hue bulbs in a single fixture in a single room, color-tempering them based on sun and moon position, with a Lutron Aurora dimmer as physical override. That codebase still works and still runs. Under this umbrella it becomes:

- **One output device** (or 8, if we register each bulb individually — TBD during epic 15 design).
- **One input device** (the Aurora dimmer), already bound by the existing AppDaemon code.
- **One bound behavior** (celestial color tempering with manual override), already encoded in `sun-fixture/appdaemon/apps/celestial.py`.

The sun-fixture's existing code is the proof-of-concept that the umbrella's mental model — inputs, outputs, and bindings — is realistic. The umbrella project is essentially a generalization of what sun-fixture does for one fixture, applied to every device in the home, with a spatial visualization on top.

### Done at the umbrella level

The user opens the wall tablet at idle, sees the floorplan with live light state, and can:
1. Identify any input device's current binding.
2. See any output device's current state.
3. Toggle, dim, or recolor any light from the map.
4. Open any room's non-light controls (climate, media, covers).
5. Override the sun-fixture's celestial mode without leaving the dashboard.
6. Optionally — and *only* if MVP+ work is greenlit — rebind an input to a different set of outputs, or define a new behavior, from the dashboard.

The Philips Hue app, the Lutron app, and Home Assistant's default UI are not opened during normal household use.
