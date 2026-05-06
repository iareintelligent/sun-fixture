# `assets/masks/`

Per-light Photoshop-painted PNG masks. White-on-transparent. One file per Hue light entity.

Naming: match the HA entity ID, e.g., `light.kitchen_overhead.png`. The Lovelace YAML binds each mask to its entity.

These are stacked above the base render with `mix-blend-mode: lighten`. Brightness drives opacity; color drives a multiply-tinted overlay. See ADR-0001 for the full technique.

Subdirectories by floor are fine when there are many masks (e.g., `masks/floor-1/`, `masks/floor-2/`); update the YAML paths accordingly.
