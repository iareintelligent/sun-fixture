# Style Guide

Visual conventions for the floorplan dashboard and umbrella project. Populated as we make concrete choices during pilot floor work — don't fill speculatively.

## Base palette

TBD — populated during pilot floor work.

The base render's dark palette is implied by ADR-0001 (rooms read as "off" by default; masks add light). Specific hex values for room "off" tones, wall colors, and floor colors are decided when the SH3D model materials are tuned.

## Light glow treatment

TBD — populated during pilot floor work.

Will document: mask falloff softness, the specific `mix-blend-mode` per layer, brightness-to-opacity scaling curve (likely non-linear — perceived brightness is roughly square-root of measured), color-tinting approach (`mix-blend-mode: multiply` on a pseudo-element vs. CSS filter approach).

## Floor selector visual

TBD — populated during pilot floor work.

Will document: rail width, active vs. inactive treatment, label typography, transition animation (instant vs. fade — leaning instant per the dashboard's glanceability goal).

## Popover treatment

TBD — populated during pilot floor work.

Will document: popover anchor point relative to the tapped room, dim/blur of the underlying floorplan, dismissal interaction, control density.

## Typography

TBD — populated during pilot floor work.

Will document: type family, scale, what shows on the map vs. what shows only in popovers.
