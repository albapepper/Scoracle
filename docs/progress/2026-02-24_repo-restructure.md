# Repository Restructure & Cleanup

**Date:** 2026-02-24
**Scope:** Full repository organization overhaul
**Commits:** `d6cb36e` (restructure), follow-up (audit fixes)

## Goal

Reorganize the Scoracle repository from a nested `astro-frontend/` subdirectory layout (a relic of framework experimentation with Svelte and React) into a clean, flat Astro project structure. Clean up all stale references to removed frameworks, Vercel deployment, and ghost directories.

## What Was Done

### Phase 1: Flatten `astro-frontend/` into root

Moved all 72 tracked files from `astro-frontend/` to the repo root using `git mv` to preserve history:

- `astro-frontend/src/` -> `src/`
- `astro-frontend/public/` -> `public/`
- `astro-frontend/astro.config.mjs` -> `astro.config.mjs`
- `astro-frontend/tsconfig.json` -> `tsconfig.json`
- `astro-frontend/package.json` replaced the root delegator `package.json`

The root `package.json` was previously a thin wrapper that just ran `cd astro-frontend && npm <command>`. It was replaced with the actual project `package.json`, renamed from `scoracle-astro-frontend` to `scoracle`, with the `engines` field added.

### Phase 2: Consolidate docs

- `planning_docs/` -> `docs/planning/`
- `progress_docs/` -> `docs/progress/`

### Phase 3: Clean `.gitignore`

Rewrote from 57 lines to 46 lines:

- Removed 26 lines of Python entries (`__pycache__`, `venv/`, `.eggs/`, etc.) -- no Python in this repo
- Removed ghost directory entries (`/frontend/`, `/statsdb/`, `/lib/`, `/lib64/`)
- Removed `.vercel` entry
- Added missing entries: `.railway/`, `.claude/`, `docker-compose.override.*`, `.env.production`, `Thumbs.db`, `*.log`
- Fixed header from `# Node.js / React` to separate sections

### Phase 4: Clean orphaned configs

- **`.vscode/tasks.json`** -- Replaced orphaned Python seeder task (`python -m app.database.seed_local_dbs`) with Dev Server, Build, and Type Check tasks
- **`.claude/settings.local.json`** -- Removed 20 stale entries (Windows paths to `c:\Users\albap\...\backend\`, Python commands, SQLite commands). Kept 13 relevant entries. Untracked the file and added `.claude/` to `.gitignore` since it's per-developer local config

### Phase 5: Fix stale Vercel references

- **`src/layouts/Layout.astro`** -- Replaced hardcoded `https://scoracle.vercel.app/og-image.png` with dynamic `SITE_URL`-based resolution. Made OG/Twitter image meta tags conditional (omitted when no image exists rather than emitting a broken URL). Updated structured data to conditionally include image.
- **`astro.config.mjs`** -- Changed fallback site URL from `scoracle.vercel.app` to `scoracle.up.railway.app`
- **`.env.example`** -- Changed `SITE_URL` from Vercel to Railway domain
- **`README.md`** -- Fixed `SITE_URL` default in environment variables table

### Phase 6: Fix image filenames

Renamed sport logo files to remove spaces and normalize casing:

- `NBA logo.png` -> `nba-logo.png`
- `NFL logo.png` -> `nfl-logo.png`
- `fifa logo.png` -> `fifa-logo.png`

Updated the imports in `CrystalBallSelector.astro` accordingly.

### Phase 7: Docker/Railway compatibility

Updated files from the merged Docker PR (#34) to work with the flat structure:

- **`Dockerfile`** -- Removed all `astro-frontend/` path nesting. `WORKDIR` changed from `/app/astro-frontend` to `/app`. `COPY` commands updated accordingly.
- **`.dockerignore`** -- Removed stale `astro-frontend/node_modules` and `astro-frontend/dist` entries. Added `.env*`, `.claude`, `.astro`, `*.md` to prevent secrets and unnecessary files from entering Docker build context.

### Phase 8: Minor cleanup

- **`docs/planning/ARCHITECTURE-FRONTEND.md`** -- Updated Astro config example from `output: 'server'` (Astro 4) to `output: 'static'` (Astro 5 hybrid equivalent)
- **`package.json`** -- Populated `keywords` and `author` fields
- **`public/data/README.md`** -- Updated to reflect actual filenames (`nba.json`, not `nba-players.json`) and removed stale copy instructions referencing `/frontend/` and `/scoracle-svelte/`
- **`docs/planning/VERCEL_TO_RAILWAY_MIGRATION.md`** -- Updated 5 path references from `astro-frontend/` to flat paths
- **`docs/progress/2026-02-23_vanilla-js-refactor.md`** -- Updated scope path

### Merge conflict resolution

The restructure commit was rebased on top of PR #34 (Docker/Railway container deployment). A merge conflict in `README.md`'s Deployment section was resolved by combining the container-based deployment instructions from the PR with the private network URL documentation from the restructure.

## Files Changed

### Restructure commit: 85 files changed, +216/-423

- 72 files renamed (`astro-frontend/` -> root)
- 3 docs renamed (`planning_docs/` and `progress_docs/` -> `docs/`)
- 5 files deleted (duplicate `astro-frontend/` configs)
- 5 files modified (root configs and docs)

### Audit fixes commit

- 10 files modified (Layout.astro, .gitignore, .dockerignore, Dockerfile, README, package.json, architecture doc, CrystalBallSelector.astro, migration doc, data README)
- 3 files renamed (image files)
- 1 file untracked (.claude/settings.local.json)

## Verification

- `npm install` -- 445 packages installed successfully
- `npm run check` -- 0 errors, 0 warnings, 6 pre-existing hints
- `npm run build` -- Successful build: 3 static pages, 2 SSR routes, all assets compressed

## Result

The repository is now a standard flat Astro project with no unnecessary nesting, no stale framework references, and clean Docker/Railway deployment configs. All documentation accurately reflects the current architecture.
