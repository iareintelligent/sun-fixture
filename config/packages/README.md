# `config/packages/`

Home Assistant [packages](https://www.home-assistant.io/docs/configuration/packages/) — reusable YAML bundles that group related entities, automations, scripts, scenes, and helpers.

Likely contents (populated during epic 10):
- Room groupings (`group.kitchen_lights`, etc.).
- Per-room scene definitions (movie mode, good morning, etc.).
- Helper entities (input_selects, input_booleans) that drive the dashboard state.
- Any HA template sensors needed by the floorplan dashboard.

These get deployed to Home Assistant's `packages/` directory. The deploy mechanism is TBD — could share infrastructure with `sun-fixture/`'s deploy scripts, could be a new path. Decide during epic 10.
