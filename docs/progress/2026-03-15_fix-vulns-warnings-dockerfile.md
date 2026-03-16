# Fix Vulnerabilities, TypeScript Warnings, and Dockerfile Build Speed

**Date:** 2026-03-15
**Scope:** Resolve all npm vulnerabilities, eliminate TypeScript warnings, optimize Docker build time

## Goal

The Railway build reported 10 npm vulnerabilities (7 moderate, 3 high), 6 TypeScript hints during `astro check`, and a total build time of 77.73 seconds. The goal was to reach 0 vulnerabilities, 0 warnings, and reduce Docker build time.

## What Was Done

### Phase 1: Vulnerability Fixes

- Updated `devalue` override from `5.6.3` to `5.6.4`, fixing both moderate CVEs (GHSA-cfw5-2vxh-fr84, GHSA-mwv9-gp5h-frr4 — prototype pollution in `devalue.parse` and `devalue.unflatten`).
- Updated `astro-compress` from `2.3.9` to `2.4.0`. The old version bundled its own `astro@5.16.8` as a transitive dependency, which carried additional vulnerable packages. The new version uses `astro: "*"` as a peer dependency, deduplicating to the project's `astro@5.18.0`.

### Phase 2: TypeScript Warning Cleanup

Removed unused `apiUrl` class properties and their constructor assignments from 12 files. These were vestigial from before the migration to `data-sources.ts` URL builders — each class declared `private apiUrl`, assigned it from a DOM `data-api-url` attribute, but never read it afterward.

**Files modified (declaration + assignment removed):**
- `src/components/PlayerProfileWidget.astro`
- `src/components/ProfileWidgetComparison.astro`
- `src/components/StatsComparison.astro`
- `src/components/StatsComparisonContent.astro`
- `src/components/StrengthsWeaknessesComparison.astro`
- `src/components/TeamProfileWidget.astro`
- `src/components/tabs/NewsTab.astro`
- `src/components/tabs/PlayerStatsTab.astro`
- `src/components/tabs/TeamStatsTab.astro`
- `src/lib/tabs/similarity-tab.ts`
- `src/lib/tabs/twitter-tab.ts`
- `src/lib/utils/entity-resolver.ts` (removed unused `apiUrl` function parameter + updated JSDoc)

### Phase 3: Dockerfile Optimization

Restructured from a 2-stage to a 3-stage Docker build to eliminate the `RUN chown -R app:app /app` bottleneck, which was recursing through ~350 node_modules directories and taking ~18 seconds on Railway.

**Before (2-stage):**
1. Build stage: `npm ci` + `astro build`
2. Runtime stage: `npm ci --omit=dev` + `COPY dist` + `RUN chown -R app:app /app`

**After (3-stage):**
1. Build stage: `npm ci` + `astro build` (unchanged)
2. Deps stage: `npm ci --omit=dev` (isolated)
3. Runtime stage: `COPY --chown=app:app` from both stages (no `RUN chown`)

Using `--chown=app:app` on COPY directives sets ownership during the copy operation, avoiding the expensive recursive walk entirely.

## Files Changed

| File | Change |
|------|--------|
| `package.json` | Updated `astro-compress` to `2.4.0`, `devalue` override to `5.6.4` |
| `package-lock.json` | Regenerated (3 packages removed, 6 changed) |
| `Dockerfile` | Restructured to 3-stage build with `--chown` on COPY |
| 12 source files | Removed unused `apiUrl` declarations (see list above) |

## Verification

- `npm audit`: 0 vulnerabilities (was 10 in Railway build stage, 4 in runtime stage)
- `npm run build` (`astro check && astro build`): 0 errors, 0 warnings, 0 hints (was 12 hints)
- Estimated Railway build time improvement: ~15-18 seconds from Dockerfile `chown` elimination

## Result

The project now builds cleanly with zero vulnerabilities and zero TypeScript diagnostics. The Dockerfile optimization should reduce Railway build time from ~78s to ~60s by eliminating the recursive `chown` bottleneck. The 3-stage build pattern also provides better layer caching — production dependencies are isolated in their own stage, so they only rebuild when `package.json` changes.
