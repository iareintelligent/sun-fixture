# Operating instructions for AI assistants in this project

This file is the persistent brief for any AI assistant working on the **Bungalow Fortress Automation** umbrella project. The project is multi-week and multi-session; treat your context window as ephemeral and the repo as canonical.

## Three operating principles, in priority order

1. **Persist everything in the repo.** Decisions, learnings, user statements, things you'd want a future session to know — write them down in `docs/` (especially `docs/working-notes/` for session diaries and `docs/decisions/` for ADRs) or in a bd issue. Don't trust your context to survive.
2. **Use judgment about decomposition.** Some epics are clear enough to break into tasks now; others are stubs whose details we'll work out when we get there. You decide which is which, and the user will tell you if you got it wrong. The goal is a useful working set, not a complete plan.
3. **Ask the user when you need something only they can provide.** You can't take photos, run Photoshop, prompt an image generator, audit the Hue Bridge in person, deploy YAML to the user's HA instance, or physically configure a wall tablet. When a task requires any of those, label it `human-only` and surface it clearly. The user is fine being told "I need you to do X before I can continue."

## Session entry point

`bd ready --json` is the first thing you run in a session. It returns unblocked issues sorted by priority. Pick one and claim it (`bd update <id> --claim`). When done, close it (`bd close <id>`). End the session by following the "Landing the Plane" protocol in `AGENTS.md`.

## Human-only task types

Any of the following is a task only the user can execute. You can produce drafts, specifications, checklists, and procedures for *every* one of them, but you cannot run them yourself:

- Photography of any kind.
- Sweet Home 3D modeling beyond writing a modeling checklist.
- Photoshop work (mask painting, exposure adjustment, color grading).
- AI image generation (if/when we use it).
- Physical Hue Bridge audits and bulb pairing.
- Lutron Caseta or Aurora device pairing/configuration.
- Deployment of YAML to the Home Assistant instance.
- Wall-tablet provisioning (mount, kiosk-mode browser, screen-on/off rules).
- Renaming the repo's filesystem directory (e.g., `sun-fixture/` → `bungalow-fortress-automation/`).
- Anything that requires being in the user's home or on their network with their hands.

Drafts and specifications for these *are* in scope and welcome.

## Work-order rule

The pipeline from physical home to working dashboard has a strict order. Don't skip steps:

```
model  →  render  →  mask  →  composite  →  YAML  →  deployment
```

Concretely: don't start writing Lovelace YAML for a room before you have at least a base render of its floor; don't paint masks for a room before the SH3D model is right; don't try to deploy before the YAML is locally valid.

## Pushback list

Push back, in any session, if:

- The user asks you to skip the inventory step and "just start building." Without `docs/room-inventory.md` (and `docs/device-inventory.md`) populated, every later step is guessing.
- The user asks you to start the pilot floor before the Sweet Home 3D model exists.
- The user asks for a feature that contradicts `docs/mission.md` (e.g., free-rotation 3D dollhouse, support for entities the home doesn't have).
- A `bd ready` task lacks enough specificity to know what "done" looks like — either rewrite it or surface the ambiguity to the user.
- A task you're working on grows past one session's worth of work — split it instead of pushing through.
- You notice you're about to do something this file lists as `human-only`.
- You realize an MVP feature isn't represented anywhere in the epic graph.
- You're about to commit something that overrides the user's pre-existing uncommitted work without explicit permission.

Pushback isn't optional politeness — it's the main mechanism keeping a multi-session, mostly-human-driven project from drifting.

## Where to look first

| Looking for | File |
|---|---|
| Project scope, "done" criteria | `docs/mission.md` |
| Why we chose static isometric instead of three.js | `docs/decisions/0001-visual-direction.md` |
| What rooms / lights exist | `docs/room-inventory.md` (once populated) |
| What inputs / outputs / bindings exist | `docs/device-inventory.md` (once populated) |
| What the previous session decided / left open | latest file in `docs/working-notes/` |
| The next concrete task | `bd ready --json` |
| Sun-fixture's existing automation logic | `sun-fixture/appdaemon/apps/celestial.py` |
| bd workflow rules + landing-the-plane protocol | `AGENTS.md` |

## A note on minimalism

This is a long project. Don't add abstractions, scripts, helpers, or scaffolding "just in case." The user has been explicit: three similar lines is better than a premature abstraction. Add tooling when there's a real need.
