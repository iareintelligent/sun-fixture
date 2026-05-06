# Working notes — 2026-05-06 — Session 1: scaffolding

## What this session was

The user pasted the Bungalow Fortress Automation seed prompt into a fresh Claude Code session. The seed prompt's §6 mandates a scaffolding-only first session: directories, mission docs, ADR-0001, beads epic graph, then stop. This file is the session diary for that pass.

## The repo this session began with

Not a clean slate. The repo at `/Users/topher/code/sun-fixture` was the existing **Celestial Lighting System** (sun-fixture) — an AppDaemon application driving 8 Hue bulbs in a single fixture in a single room, sun-temperature-aware, with a Lutron Aurora dimmer as physical override. It already had:

- A working `appdaemon/apps/celestial.py` plus viz and dashboard scripts.
- A local test harness (`local_test_server.py`, `local_test_ui.html`).
- Top-level docs: `README.md`, `ARCHITECTURE.md`, `PROJECT_PLAN.md`, `SETUP_SSH_KEY.md`.
- A 150-line `AGENTS.md` with substantive bd workflow rules, non-interactive shell guidance, and a "landing the plane" session-end protocol — much stronger than the seed prompt's proposed 3-line replacement.
- Several deploy/update shell scripts at root.
- An already-initialized `.beads/` directory with one open issue (`sun-fixture-nb5: Deploy system dashboard to HA Green`, P1, blocked).
- Uncommitted modifications + untracked files in the working tree.

## Big decision the user made mid-plan

The user expanded scope significantly during plan review. Three things changed:

1. **Repo identity shift to umbrella project.** Not "sun-fixture with a dashboard bolted on" — the new identity is **Bungalow Fortress Automation**, a device management system. The floorplan dashboard is *one face*. Sun-fixture is *one managed subsystem*.
2. **Sun-fixture relocated wholesale.** All sun-fixture code, docs, scripts, tests, env files, and Python config moved into `sun-fixture/` subdirectory via `git mv` (history preserved). The umbrella project starts fresh from root.
3. **Project name signal toward filesystem rename.** The user said "we can even rename the root directory from sun-fixture to bungalow-fortress-automation." That's permission, not a directive — surfaced as a follow-up below.

## Scope expansion: device management system

The seed prompt's mission was a multi-floor isometric floorplan dashboard. The user's clarification expanded it: the dashboard is the *primary visualization* of a broader device-management system that catalogs inputs (Lutron dimmers, motion sensors), catalogs outputs (Hue groups, Nest, sun-fixture, media surfaces), and lets the user view + reassign + define new bindings between them. Read-only is acceptable for MVP. Replacing the Philips Hue app entirely is a stretch goal, explicitly not MVP.

This shows up in:

- `docs/mission.md` Section 2 ("Broader umbrella scope") — full text of the device-management mission.
- `docs/device-inventory.md` (new file beyond the seed prompt) — sibling to room-inventory, organized by device, with separate Inputs and Outputs tables.
- 5 new beads epics (14–18 below).

## What I executed

### Two commits

1. `WIP: pre-scaffolding sun-fixture changes` — captured the user's pre-existing modifications and untracked files (apps.yaml, celestial.py, dashboard, viz, pyproject, README modifications, the local test harness) before any restructuring. Per-file `git add`, no `-A`.
2. `Initial scaffolding: bungalow-fortress-automation umbrella, …` — the scaffolding commit (pending at the time these notes are written).

### Sun-fixture relocation

Used `git mv` for all tracked files (preserves history). Used plain `mv` for the two gitignored ones (`uv.lock`, `.env`). Everything sun-fixture–specific now lives under `sun-fixture/`:

- `sun-fixture/appdaemon/`, `sun-fixture/tests/`
- `sun-fixture/main.py`, `sun-fixture/local_test_server.py`, `sun-fixture/local_test_ui.html`
- `sun-fixture/pyproject.toml`, `sun-fixture/uv.lock`, `sun-fixture/.python-version`
- `sun-fixture/test_*.py`, `sun-fixture/test_requirements.txt`, `sun-fixture/run_tests.sh`
- `sun-fixture/deploy*.sh`, `sun-fixture/quick_deploy.sh`, `sun-fixture/update_*.sh`, `sun-fixture/setup_ssh_key.sh`
- `sun-fixture/README.md`, `sun-fixture/ARCHITECTURE.md`, `sun-fixture/PROJECT_PLAN.md`, `sun-fixture/SETUP_SSH_KEY.md`
- `sun-fixture/.env`, `sun-fixture/.env.example`

### New umbrella scaffolding

```
docs/                  mission.md, decisions/, working-notes/, room+device inventories, style-guide stub, photography-protocol stub, design-reference stub
assets/                sweet-home-3d/, photos/, renders/, masks/, composites/, debug/  (each with a README explaining purpose)
config/                lovelace/{floorplan-dashboard,fallback-dashboard}.yaml + popovers/, packages/, themes/
scripts/               README only — nothing yet
README.md              umbrella, ≤200 lines, scope + status + resume instructions
CLAUDE.md              operating principles, human-only list, work-order rule, pushback list
AGENTS.md              augmented (banner prepended; existing 150 lines preserved)
.gitignore             augmented (*.psd, assets/photos/raw/, secrets.yaml, Thumbs.db)
```

### ADR-0001

Captured the visual direction: static isometric per-floor renders from Sweet Home 3D, composed in Picture Elements with per-light masks blended via `mix-blend-mode: lighten` (opacity ← brightness, multiply pseudo-element ← color). Status: accepted, dated 2026-05-06. Includes mandatory "Reconsideration triggers" section.

### Beads graph

`bd init` skipped — already initialized. Issue prefix `sun-fixture-` retained.

**18 epics created** (13 from seed prompt + 5 from scope expansion). IDs:

| # | Title | ID | Type/Pri |
|---|---|---|---|
| 1 | Repository scaffolding | sun-fixture-90m | chore/P1 |
| 2 | Room and light inventory | sun-fixture-k6g | epic/P1 |
| 3 | Sweet Home 3D model of the home | sun-fixture-32f | epic/P2 |
| 4 | Pilot floor — end-to-end pipeline | sun-fixture-de5 | epic/P2 |
| 5 | Per-light mask blending technique | sun-fixture-o9p | epic/P2 |
| 6 | Floor switching navigation | sun-fixture-5cw | epic/P3 |
| 7 | Remaining floors | sun-fixture-iym | epic/P3 |
| 8 | Room popover system | sun-fixture-pd4 | epic/P3 |
| 9 | Hue color rendering on the map | sun-fixture-6uk | epic/P3 |
| 10 | Multi-domain controls | sun-fixture-6b9 | epic/P3 |
| 11 | Fallback dashboard | sun-fixture-ock | epic/P3 |
| 12 | Wall tablet deployment & kiosk mode | sun-fixture-b32 | epic/P4 |
| 13 | Acceptance and 'done' verification | sun-fixture-17h | epic/P4 |
| 14 | Device input registry (NEW) | sun-fixture-lre | epic/P2 |
| 15 | Device output registry (NEW) | sun-fixture-yz6 | epic/P2 |
| 16 | Input-to-output behavior assignment (NEW) | sun-fixture-125 | epic/P3 |
| 17 | Sun-fixture as managed subsystem (NEW) | sun-fixture-o79 | epic/P3 |
| 18 | Hue app replacement — stretch (NEW) | sun-fixture-dv8 | epic/P4 |

**Dependencies wired:**
- `3 ← 2`, `4 ← 3`, `7 ← 4`, `10 ← 8`, `12 ← 7`, `12 ← 10`, `13 ← 12`
- `14 ← 2`, `15 ← 2`, `16 ← 14`, `16 ← 15`, `17 ← 15`

**Decomposition decisions:**

| Epic | Decision |
|---|---|
| 1 (Repository scaffolding) | **Decomposed into 10 child tasks**, 9 closed during this session; 1 (write working-notes/0001 — this very file) closed when this commit lands. |
| 2 (Inventory) | **Decomposed into 3 child tasks**: Hue Bridge listing helper script (open, P2), inventory templates (closed, linked discovered-from to epic 1's template task), [HUMAN-ONLY] fill-in (open, P1, label `human-only`). |
| 3–18 | **Stubs.** Decompose when the work nears. Per seed prompt §1.2, the goal is a useful working set, not a complete plan. |

**Existing issue `sun-fixture-nb5` (Deploy system dashboard to HA Green)** left open and untouched. It's real sun-fixture work that remains valid under the umbrella.

## Pushbacks made (per seed prompt §1.3 and §8)

1. **AGENTS.md replacement.** The seed prompt's 3-line AGENTS.md is weaker than the existing 150-line file. I preserved the existing content and prepended a small banner pointing to mission/CLAUDE.md, instead of overwriting.
2. **`bd init`.** Already done in commit `bdd3f1d`. Skipped.
3. **Brownfield reconciliation.** The seed prompt assumes a clean slate; this is brownfield. Added the entire reconciliation section to the plan, the wholesale `sun-fixture/` subdirectory move, and the `docs/sun-fixture/` route was abandoned in favor of `sun-fixture/` once the user clarified scope.
4. **Mission scope.** The seed prompt's mission was floorplan-only. The user's clarification was umbrella-wide. I added 5 new epics (14–18) to reflect that. If the user wants any of those reframed, easy to revise.
5. **Pre-existing user WIP.** Not touched. Committed first as a separate commit so my scaffolding commit is clean.

## User follow-ups (things only the user can do)

1. **Sanity-check sun-fixture deployment scripts after the relocation.** The `deploy*.sh` and `update_*.sh` scripts now live in `sun-fixture/`. Any hardcoded paths inside them (e.g., references to `appdaemon/apps/celestial.py` rather than to a path resolved from script location) likely need updating before the next deploy. I deliberately did not edit script contents this session — that's a discrete follow-up. **Consider filing a bd task** for it before the next deploy attempt.
2. **Decide whether to rename the repo directory.** The user said `~/code/sun-fixture/` → `~/code/bungalow-fortress-automation/` would be acceptable. This is a filesystem-level rename: would change cwd, IDE workspace path, possibly any shell aliases. Do when convenient.
3. **Decide whether to update the bd issue-prefix.** Currently `sun-fixture-`. To switch to a project-wide one (e.g., `bfa-`, `bungalow-`), edit `.beads/config.yaml` to set `issue-prefix:` explicitly. Existing issue IDs don't change retroactively; only new issues pick up the new prefix. Cosmetic.
4. **Optionally,** retitle `sun-fixture-nb5` (Deploy system dashboard to HA Green) if it's now ambiguous — does "system dashboard" still mean the sun-fixture viz, or the new Bungalow Fortress dashboard? My read: it's still the sun-fixture viz dashboard from `sun-fixture/appdaemon/apps/system_dashboard.py`. Worth confirming.

## Open questions surfaced for next session

1. **Should every Hue bulb be its own output entity in the registry, or should sun-fixture's 8 bulbs be grouped as a single output?** Decide during epic 15 design. The mask-painting workflow probably wants per-bulb outputs (one mask per physical bulb), but the behavior-assignment workflow might prefer per-fixture outputs.
2. **Where do behavior bindings live persistently?** HA's automations? A package YAML in `config/packages/`? A sidecar file? Affects epic 16 design.
3. **What's the input device language for Lutron Aurora devices?** Aurora dimmers are Friends-of-Hue, so they're paired with the Hue Bridge but exposed to HA in a non-standard way. The existing `sun-fixture/appdaemon/apps/celestial.py` handles Aurora click/rotate events. Clarify whether epic 14 treats the Aurora as one input (with click + rotate as facets) or two inputs (click + rotate as separate entities).

## Mental model handoff for the next session

- Source of truth for the project's scope is `docs/mission.md`.
- Source of truth for the rendering technique decision is `docs/decisions/0001-visual-direction.md`.
- Next concrete work-able task on `bd ready` is most likely **the Hue Bridge listing helper script (sun-fixture-k6g.1, P2)**, since the [HUMAN-ONLY] inventory fill-in is the user's job and not unblocked-for-AI in the same sense.
- Do **not** start any of epics 3–18 until the inventory (epic 2) is meaningfully populated.
- The work-order rule from CLAUDE.md is the discipline that keeps this from drifting: model → render → mask → composite → YAML → deployment.
