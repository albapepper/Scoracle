# Replace Static Autofill JSONs with PostgREST Fetch Script

**Date:** 2026-03-15
**Scope:** Automated autofill data refresh from PostgREST materialized views, with build-time cache busting

## Goal

The autofill JSON files in `public/data/` were stale snapshots generated manually from the old FastAPI backend on 2025-12-25. After dramatic DB changes and the migration to a new PostgREST backend, these files needed replacement. A new `autofill_entities` materialized view is now available per sport schema on PostgREST. The goal was to create a repeatable, automated way to pull fresh autofill data from PostgREST and write lean static JSON files for instant client-side autocomplete.

## What Was Done

### Phase 1: Build-time fetch script

Created `scripts/fetch-autofill.mjs` — a lightweight Node script that:
1. Iterates over the three sports (NBA, NFL, Football)
2. Fetches `GET /autofill_entities` from PostgREST with `Accept-Profile: {sport}` header for schema selection
3. Strips each entity to only the fields autocomplete needs: `id`, `name`, `type`, `position`, and `meta.team`
4. For teams, prefers `meta.full_name` over the short `name` (e.g., "Atlanta Hawks" instead of "Hawks")
5. Writes to `public/data/{sport}.json` in the v2.0 entities format that `entity-data-store.ts` already supports

The PostgREST URL defaults to the production instance but is configurable via `POSTGREST_URL` env var.

### Phase 2: Build pipeline integration

- Added `"fetch-data"` npm script to `package.json`
- Added `RUN npm run fetch-data` to the Dockerfile build stage, before `npm run build`, so every Railway deploy gets fresh data automatically

### Phase 3: CDN/browser cache busting

After deploying, the old JSON files were still served due to CDN (Fastly/Varnish) and browser caching — the URL `/data/nba.json` was identical before and after deploy.

Fixed by injecting a build-time cache-busting version:
- `astro.config.mjs`: Added `vite.define.__DATA_VERSION__` set to `Date.now()` at build time
- `entity-data-store.ts`: Appends `?v={version}` to data file fetch URLs
- `src/env.d.ts`: TypeScript declaration for the `__DATA_VERSION__` global

Each deploy compiles a unique timestamp into the JS bundle, so the fetch URL changes (e.g., `/data/nba.json?v=1773628213207`), busting both CDN and browser caches. Within a single deploy, the version is constant so CDN caching still works.

## Files Changed

| File | Change |
|------|--------|
| `scripts/fetch-autofill.mjs` | **New** — PostgREST fetch + transform script |
| `package.json` | Added `fetch-data` script |
| `Dockerfile` | Added `RUN npm run fetch-data` before build step |
| `astro.config.mjs` | Added `vite.define.__DATA_VERSION__` for cache busting |
| `src/lib/utils/entity-data-store.ts` | Append `?v={version}` to data file fetch URLs |
| `src/env.d.ts` | Added `__DATA_VERSION__` global type declaration |
| `public/data/nba.json` | Replaced — now v2.0 format, 594 entities (was 778), 39 KB (was 75 KB) |
| `public/data/nfl.json` | Replaced — now v2.0 format, 1,860 entities (was 3,351), 139 KB (was 322 KB) |
| `public/data/football.json` | Replaced — now v2.0 format, 3,375 entities (was 15,768), 253 KB (was 1.8 MB) |

## Verification

- `npm run fetch-data`: All three sports fetched successfully from PostgREST
- `npm run build`: 0 errors, builds cleanly with `__DATA_VERSION__` inlined
- Confirmed `?v=` cache-busting parameter present in compiled `entity-data-store` output
- No changes required to `entity-data-store.ts` parsing — existing v2.0 code path handles the new format

## Result

Autofill data is now sourced directly from the PostgREST `autofill_entities` materialized views at build time, replacing the old manually-committed JSON snapshots. The files are significantly leaner (total: 431 KB vs 2.2 MB) since only autocomplete-relevant fields are retained. To refresh data: run `npm run fetch-data` locally, or redeploy on Railway (the Dockerfile handles it automatically). CDN/browser cache staleness is eliminated by build-time version injection.
