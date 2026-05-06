# `assets/sweet-home-3d/`

Sweet Home 3D source files for the home model.

- `*.sh3d` — the model file(s). Treat these as source of truth; everything in `assets/renders/` is derived from them.
- Texture overrides, custom furniture exports — also live here.

Keep one `.sh3d` per major version of the model so we have something to roll back to. Don't gitignore them — they're small enough and they're our canonical artifact.
