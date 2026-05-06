# `scripts/`

Helper scripts for the umbrella project. Empty at scaffolding time — scripts get added when we have a concrete need, not preemptively.

Likely first arrivals:
- A Hue Bridge listing helper (epic 2 child task) that prints every Hue light/device with its HA entity ID and Bridge metadata so the user can populate `docs/room-inventory.md` and `docs/device-inventory.md`.
- A render/mask filename validator that checks every entity ID referenced in the Lovelace YAML has a corresponding mask file in `assets/masks/`.

Sun-fixture–specific scripts (deploy, update) live in `sun-fixture/`, not here. This directory is for the umbrella project.
