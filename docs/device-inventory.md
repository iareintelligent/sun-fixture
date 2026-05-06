# Device Inventory

Catalog of input and output devices spanning the home, alongside `room-inventory.md`. Where `room-inventory.md` is organized by *room*, this file is organized by *device*. Same underlying data, different cut.

This file exists because the umbrella project is a device management system: inputs (dimmers, motion sensors) drive outputs (lights, thermostats, the sun-fixture, media). The bindings between them are the thing the user wants to be able to view, unassign, and reassign from the dashboard.

**Status:** template only. The user fills this in. Many entries can be reused/derived from `room-inventory.md` once both are populated; for the MVP they're maintained by hand and reconciled.

## Inputs

Devices that *generate* state changes the home reacts to.

### Schema

| Column | Notes |
|---|---|
| Device | Human-readable name. |
| HA entity / device ID | Best identifier HA has. For some inputs (Lutron Auroras as Friends-of-Hue), this is a Hue device ID rather than an HA entity. |
| Type | `dimmer`, `motion`, `occupancy`, `contact`, `wall_switch`, `media_state`, etc. |
| Room | Room name, matches `room-inventory.md`. |
| Currently bound to | What this input currently drives. Free text, but try to use device names from the Outputs table below. |
| Notes | Quirks, battery state, known issues. |

### Inputs table

| Device | HA entity / device ID | Type | Room | Currently bound to | Notes |
|---|---|---|---|---|---|
| EXAMPLE — replace | `00:17:88:01:XX:XX:XX:XX-XX-XXXX` | dimmer (Lutron Aurora) | Living Room | Sun-fixture (8 bulbs) | Friends-of-Hue device, click toggles celestial override, rotate sets brightness. |

## Outputs

Devices that *receive* commands and change physical state.

### Schema

| Column | Notes |
|---|---|
| Device | Human-readable name (e.g., "Kitchen Overhead", "Sun Fixture"). |
| HA entity ID | Full `light.*`, `climate.*`, `media_player.*` etc. For grouped outputs (sun-fixture's 8 bulbs), one row may represent the group; record member entities in Notes. |
| Capabilities | `color`, `cct`, `white`, `dimmable`, `on/off`, `temperature`, `media`, etc. |
| Room | Room name. |
| Driven by | What input(s) currently drive this. Match Inputs table. |
| Subsystem | `direct` (HA controls it), `sun-fixture` (managed by AppDaemon celestial logic), `nest`, `hue-bridge`, etc. |
| Notes | Brand, model, anything weird. |

### Outputs table

| Device | HA entity ID | Capabilities | Room | Driven by | Subsystem | Notes |
|---|---|---|---|---|---|---|
| EXAMPLE — replace | `light.sun_fixture_n` | color, cct, dimmable | Living Room | Aurora dimmer (override only); celestial logic otherwise | sun-fixture | One of 8 bulbs in the sun-fixture compass; managed by `sun-fixture/appdaemon/apps/celestial.py`. |

## Counts (fill in as you go)

- **Total inputs:** _TBD_
- **Total outputs:** _TBD_
- **Subsystems:** _TBD_

## Reconciliation note

When `room-inventory.md` and this file diverge — e.g., a Hue light appears in one but not the other — treat `room-inventory.md` as authoritative for *physical placement* and this file as authoritative for *control bindings*. Eventually a single tool (likely the Hue Bridge listing helper script from epic 2) will populate both.
