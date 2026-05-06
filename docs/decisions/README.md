# Architecture Decision Records (ADRs)

This directory holds dated, numbered records of decisions that shape the project's architecture or visual direction. ADRs are not requirements documents — they capture the *why* behind a choice that's already been made and the conditions under which it might be revisited.

## Format

Each file is a short markdown document. The format follows [Michael Nygard's ADR template](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions):

```
# ADR-NNNN: <Decision title>

**Status:** proposed | accepted | superseded by ADR-XXXX | deprecated
**Date:** YYYY-MM-DD

## Context
What problem are we solving? What forces are at play (technical, social, organizational)?

## Decision
What did we choose to do?

## Consequences
What becomes easier? What becomes harder? What did we commit to that's hard to undo?

## Reconsideration triggers
Under what specific conditions should we reopen this decision?
```

## Conventions

- **Numbering:** four-digit, monotonic. Never reuse a number, even for superseded ADRs.
- **Filename:** `NNNN-kebab-case-title.md`.
- **Status transitions** are tracked by editing the existing file (changing the Status line and adding a brief "Superseded by ADR-XXXX on YYYY-MM-DD" note). Don't delete superseded ADRs — they document the path we walked.
- **Length:** prefer short. An ADR that runs long is usually mixing decision (in scope here) with implementation plan (not in scope here — that goes in beads issues).
- **Reconsideration triggers** are mandatory. If you can't articulate the conditions under which the decision should be revisited, the decision isn't yet well-understood.

## Index

| # | Title | Status | Date |
|---|---|---|---|
| 0001 | Static isometric floorplan via Sweet Home 3D + Picture Elements | accepted | 2026-05-06 |
