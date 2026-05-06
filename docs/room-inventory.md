# Room Inventory

Source-of-truth catalog of every room in the home, the lights in each, and the non-light entities (climate, media, covers, sensors) attached to each. Required input for:

- Sweet Home 3D modeling (dimensions).
- Per-light mask planning (light count and rough position).
- Lovelace YAML generation (entity IDs).
- Room popover content (which controls show up).

**Status:** template only. The user fills this in. AI assistants must not guess rows.

## How to populate

1. Walk each room with a phone or tablet that has the Home Assistant app. For each room:
   - Note the room's floor and approximate L × W × H in meters.
   - Open the HA Devices view filtered to that room (or pull entity IDs from the Hue Bridge listing helper script in epic 2).
   - Record every `light.*` entity in the room and whether each is color, color-temperature-only, or white-only.
   - Record every other relevant entity: `climate.*`, `media_player.*`, `cover.*`, `sensor.*` (occupancy/temperature), `binary_sensor.*` (motion).
2. Add a row per room. Use the example row's format.
3. Don't worry about getting it perfect — the inventory will be revisited during the pilot floor and again during remaining floors. But do try to capture every Hue light in the home; missing lights in the inventory means missing masks in the dashboard.

## Schema

| Column | Notes |
|---|---|
| Room | Human-readable room name. Match what you'd say out loud. |
| Floor | `B` (basement), `1` (ground), `2`, `3`, `A` (attic) — whatever your home actually has. |
| Dimensions (L×W×H, m) | Length, width, ceiling height in meters. Decimal OK. |
| Hue light entities | Comma-separated `light.*` IDs. |
| Hue types | `c` color, `t` CCT-only, `w` white-only — same order as the entity IDs. |
| Other entities | Comma-separated full entity IDs (climate, media, cover, sensors, etc.) |
| Notes | Anything weird, anything to remember when modeling, anything broken. |

## Inventory

| Room | Floor | Dimensions (L×W×H, m) | Hue light entities | Hue types | Other entities | Notes |
|---|---|---|---|---|---|---|
| EXAMPLE — replace | 1 | 4.2×3.6×2.4 | `light.kitchen_overhead`, `light.kitchen_island_pendant_1`, `light.kitchen_island_pendant_2` | c, c, c | `climate.kitchen`, `media_player.kitchen_homepod`, `binary_sensor.kitchen_motion` | Pendants are on a single Lutron dimmer; overhead is on the Hue dimmer at the door. |

## Counts (fill in as you go)

- **Total rooms:** _TBD_
- **Total Hue lights:** _TBD_
- **Total floors:** _TBD_

These three numbers gate several modeling and budgeting decisions; update them as you populate the table.
