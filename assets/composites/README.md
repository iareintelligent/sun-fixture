# `assets/composites/`

Final per-floor composite images served to Home Assistant.

In the simplest version of the rendering pipeline, the Picture Elements card composes base + masks live in the browser, and this directory holds *previews* of the composed result for documentation purposes.

If/when we move any composition step offline (e.g., baking down brightness-static layers), the baked outputs go here too.

Naming mirrors the renders: `floor-<id>-composite.png`.
