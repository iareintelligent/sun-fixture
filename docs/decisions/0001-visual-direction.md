# ADR-0001: Static isometric floorplan via Sweet Home 3D + Picture Elements

**Status:** accepted
**Date:** 2026-05-06

## Context

The project's primary user-facing artifact is a multi-floor visualization of the home in which every Philips Hue light renders live in its true location with its real-time color and brightness. Several visual approaches were on the table:

1. **Live three.js dollhouse** — the home rendered as a real 3D model in the browser, with free camera rotation, real-time lighting calculations, and per-bulb light sources.
2. **Hand-drawn 2D floorplan** with light icons that change color, similar to many existing Home Assistant floorplan dashboards.
3. **Fixed-angle isometric view per floor**, rendered as PNGs with per-light masks composited at runtime — the "Reddit-trend" aesthetic the user has been gravitating toward.

The user's stated preferences:
- A 3D dollhouse aesthetic, not a flat plan view.
- The view should feel calm and architectural, not interactive 3D.
- The user has strong Photoshop skills and time to use them.
- The user has accurate dimensions for every room.
- The user has 9–12 rooms across multiple floors.

## Decision

We are building **fixed-angle isometric per-floor views** as the rendering surface. Specifically:

- **Modeling:** The user constructs a Sweet Home 3D model of the home from real dimensions, including walls and at least placeholder furniture.
- **Per-floor rendering:** From the SH3D model, the user exports an isometric "lights-off" base render per floor as a PNG.
- **Per-light masks:** For each Hue bulb, the user paints (in Photoshop) a white-on-transparent PNG mask representing where that bulb's light falls on the scene.
- **Compositing in HA:** A Lovelace **Picture Elements** card stacks the base render plus per-light masks. Each mask is bound to its bulb's HA `light.*` entity. Mask **opacity** is driven by the bulb's brightness; mask **tint** is applied via `mix-blend-mode: multiply` (or a CSS pseudo-element) using the bulb's current RGB. Masks stack with `mix-blend-mode: lighten` so overlapping pools blend additively rather than occluding each other.
- **Floor switching:** A vertical floor-selector rail on the left edge swaps which composite is shown.

This is **not** a live three.js dashboard. The view is static-angle. Adding free rotation later means a separate redesign.

## Consequences

Things this commits us to:

1. **Sweet Home 3D as a tool.** Modeling time is the dominant cost for the pilot floor and a recurring cost any time furniture or layout changes meaningfully. The `.sh3d` file is the source of truth for floor renders; lose it and we re-model.
2. **No live 3D dashboard.** If at some future date we want a free-rotation dollhouse, we redesign the rendering layer from the ground up. The decision to add rotation is *not* a small follow-on.
3. **Per-light mask production scales linearly with bulb count.** Number of Hue lights in the house ≈ Photoshop hours for the masking phase. We've been told the count is in the dozens, not hundreds, so this is bounded but real.
4. **Dark base palette is locked in.** Rooms read as "off" by default — the masks add light, they don't subtract it. A pastel/light-mode aesthetic isn't compatible with this rendering technique without re-rendering every base.
5. **The Picture Elements card carries the rendering.** This means we accept its limits: layered absolute-positioned elements, CSS-driven blend modes, no GPU shaders. Performance ceiling is whatever a tablet's browser can paint smoothly.
6. **One canonical aspect ratio per floor.** All composites for a given floor must match the base render's dimensions exactly, or stacking breaks. Modeling discipline matters.

Things this makes easier:

- No 3D engine to debug, no shader code to write, no per-frame rendering math.
- Photoshop is a tool the user already has skill in.
- The masks can be iteratively refined without touching code.
- The static composites are debuggable: if a mask looks wrong, you open it in an image viewer.

## Reconsideration triggers

Reopen this ADR if:

- **Tablet performance** turns out to be inadequate — the wall tablet can't render the composite at glanceable framerate (>20 FPS during state changes, no perceptible lag when toggling a bulb).
- **Modeling time per floor** exceeds the budget the user is willing to spend (rough cap: a weekend per floor for a furnished, accurate model).
- **A single floor's mask count exceeds 25 lights** — at that density the mask painting workload may push us toward a generative or procedural approach rather than hand-painted.
- **The rendering technique can't represent a category of bulb the user adds** (e.g., a strip light or a bulb with a complex spatial falloff that hand-painted masks can't approximate).
- **The user discovers an off-the-shelf HA card** that does this well enough that we don't need to roll our own composition layer.
