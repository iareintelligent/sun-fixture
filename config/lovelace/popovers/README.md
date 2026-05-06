# `config/lovelace/popovers/`

Per-room popover YAML fragments. Each room's popover is a small file (e.g., `kitchen.yaml`, `master-bedroom.yaml`) included from `floorplan-dashboard.yaml`.

Popovers contain a room's *non-light* controls: climate, media, covers, scenes. **Lights are NOT in the popover** — they're controllable directly from the map.

Popovers should be consistent across rooms in their layout but vary in which controls appear, based on the room inventory in `docs/room-inventory.md`.

Likely implementation: bubble-card or a custom Picture Elements popup, decided during epic 8.
