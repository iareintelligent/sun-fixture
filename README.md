# Bungalow Fortress Automation

A Home Assistant–backed device management system for the home, with a multi-floor isometric floorplan dashboard as its primary visualization. The umbrella project under which the existing **sun-fixture** AppDaemon application is one managed subsystem among many.

## What this is

The end-state target is a wall-mounted tablet (and phone view) that:

- Shows the home as a fixed-angle isometric floorplan, one composite per floor.
- Renders every Philips Hue light in its true location, with live color and brightness.
- Lets the user view, unassign, reassign, and define new behaviors mapping inputs (Lutron dimmers, motion sensors) to outputs (Hue lights, Nest thermostat, sun-fixture, media surfaces).
- Provides a fallback traditional dashboard for guests and emergencies.

Read [`docs/mission.md`](docs/mission.md) for the full scope. Read [`docs/decisions/0001-visual-direction.md`](docs/decisions/0001-visual-direction.md) for the rendering approach. The seed prompt that started this project is preserved in the user's conversation history; the canonical written record lives in `docs/`.

## Current status

**Scaffolded.** Directory tree in place, mission docs written, ADR-0001 accepted, beads epic graph populated. **No implementation has begun.** No room/light inventory yet; no Sweet Home 3D model; no renders, masks, or composites; no working YAML beyond placeholders.

The next concrete steps live in the beads issue graph — see `bd ready` to find them.

## Repository layout

```
.
├── README.md                  ← you are here
├── CLAUDE.md                  ← operating instructions for AI sessions
├── AGENTS.md                  ← bd workflow rules + non-interactive shell rules
├── docs/                      ← mission, decisions, working notes, inventories
│   ├── mission.md
│   ├── decisions/             ← ADR-format decision records
│   ├── working-notes/         ← session-by-session decisions + open questions
│   ├── room-inventory.md      ← (template) every room and the lights in it
│   ├── device-inventory.md    ← (template) every input and output device
│   ├── style-guide.md         ← (stub) populated during pilot floor
│   ├── photography-protocol.md← (stub) populated when modeling needs photos
│   └── design-reference.md    ← user-curated visual references
├── assets/                    ← SH3D models, photos, renders, masks, composites
├── config/                    ← Lovelace YAML, HA packages, themes
├── scripts/                   ← helper scripts (added when needed)
└── sun-fixture/               ← existing celestial-lighting subsystem (kept)
```

## How to resume work in a new session

1. `cd ~/code/sun-fixture` (the directory may eventually be renamed `bungalow-fortress-automation` — see working notes).
2. `bd ready --json` to see unblocked work.
3. Read `docs/mission.md` and `docs/decisions/` to refresh context.
4. Read the latest file in `docs/working-notes/` to see where the previous session left off.
5. Follow `AGENTS.md` for the work flow (claim, work, close, push).

## What an AI assistant can vs can't do here

**Can:**
- Read code, design YAML, write Python, write docs, scaffold structure, draft procedures.
- Decompose epics into tasks in bd, link discovered work, manage the issue graph.
- Write specifications and checklists for things humans must execute (e.g., a Sweet Home 3D modeling checklist, a Photoshop masking procedure).

**Can't (these are human-only):**
- Take photos of rooms.
- Build the Sweet Home 3D model itself (can write the modeling checklist; can't open SH3D and click).
- Paint Photoshop masks (can write the procedure; can't run Photoshop).
- Run AI image generation locally (if used).
- Audit the Hue Bridge in person.
- Deploy YAML to the Home Assistant instance.
- Provision the wall tablet.
- Rename `~/code/sun-fixture/` → `~/code/bungalow-fortress-automation/` (a filesystem rename the user can do when convenient).

When an AI session hits one of these, the right move is to label the bd task `human-only`, surface it clearly, and continue with whatever else is unblocked.

## Sun-fixture subsystem

The original repo was the [sun-fixture](sun-fixture/README.md) Celestial Lighting System: an AppDaemon app driving 8 Hue bulbs in a single fixture in a single room, color-tempering them based on sun and moon position, with a Lutron Aurora dimmer as physical override. It still works and still runs. Under the umbrella, it becomes one of many managed subsystems. See `sun-fixture/README.md` for its own documentation.
