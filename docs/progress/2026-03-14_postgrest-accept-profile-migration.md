# Migrate Frontend to PostgREST Accept-Profile Headers and Go API

**Date:** 2026-03-14
**Scope:** Replace FastAPI-proxied endpoints with direct PostgREST (Accept-Profile) and Go API calls

## Goal

The backend moved from a FastAPI wrapper approach to direct PostgREST access using the `Accept-Profile` header for per-sport schema selection (`nba`, `nfl`, `football`). News and twitter endpoints moved to a dedicated Go API. The frontend needed to adopt these new backend patterns across all API call sites.

## What Was Done

### Phase 1: Core Infrastructure

- **`data-sources.ts`** — Full rewrite of the multi-backend abstraction layer:
  - Introduced `FetchTarget` type (`{ url, headers }`) as the return type for all URL builders, coupling the URL with its required headers (e.g. `Accept-Profile`) in a single call.
  - Added `postgrestHeaders()` helper that sets `Accept-Profile: {sport}` and `Accept: application/vnd.pgrst.object+json` (for single-row queries).
  - Updated `DATA_SOURCES` config: `profile`/`stats` routed to `'postgrest'`, `news`/`twitter` routed to `'go'`.
  - PostgREST URL patterns now use view-based access (`/players?id=eq.{id}`, `/player_stats?player_id=eq.{id}&season=eq.{season}`) instead of the old RPC pattern.
  - Stats URLs now include `season` parameter via `getCurrentSeason()` from `season.ts`.
  - `newsUrl()` and `twitterFeedUrl()` gained optional `limit` and `sport` parameters.
  - Go API localhost fallback updated to include `/api/v1` prefix.

- **`api-fetcher.ts`** — Added `headers` field to `FetcherOptions` interface and threaded it through the entire fetch chain: `swrFetch()` -> `dedupedFetch()` -> `revalidate()` -> `prefetch()`. Extra headers are merged alongside ETag headers in the fetch call. Updated `fetchTwitterStatus()` to use the centralized `twitterStatusUrl()` builder instead of accepting a raw `apiUrl` parameter.

- **`server/fetch.ts`** — Updated `serverFetch()` to accept and merge `extraHeaders` with its existing `Accept: application/json`. Updated `fetchProfile()`, `fetchStats()`, `fetchNews()` to destructure `{ url, headers }` from the URL builders.

### Phase 2: Environment Configuration

- **`.env.example`** — Uncommented `PUBLIC_POSTGREST_URL`, `POSTGREST_INTERNAL_URL`, `PUBLIC_GO_API_URL`, `GO_INTERNAL_URL` with production-ready values.
- **`env.d.ts`** — Added TypeScript type declarations for all 6 backend environment variables.

### Phase 3: Client-Side Call Site Migration

Centralized ~25 scattered call sites that built URLs with string templates (`${this.apiUrl}/profile/player/${id}?sport=...`) to use the URL builder functions from `data-sources.ts`.

**Profile endpoints (7 files):**
- `PlayerProfileWidget.astro`, `TeamProfileWidget.astro`, `ProfileWidgetComparison.astro`, `EntityWidgetPair.astro` (deleted upstream during rebase), `SharedArticlesCard.astro` (deleted upstream), `SharedContentCard.astro` (deleted upstream), `twitter-tab.ts`, `entity-resolver.ts`

**Stats endpoints (5 files):**
- `PlayerStatsTab.astro`, `TeamStatsTab.astro`, `StatsComparison.astro`, `StatsComparisonContent.astro`, `StrengthsWeaknessesComparison.astro`

**News endpoints (4 files):**
- `NewsTab.astro`, `SharedContentCard.astro` (deleted upstream), `SharedArticlesCard.astro` (deleted upstream), `co-mentions.ts`

**Twitter endpoints (3 files):**
- `twitter-tab.ts`, `SharedContentCard.astro` (deleted upstream)

**Similarity (1 file):**
- `similarity-tab.ts` — centralized through `similarityUrl()` for consistency (still routes to FastAPI since no PostgREST view exists yet)

### Bug Fix

Fixed `SharedArticlesCard.astro` (deleted upstream during rebase) which was passing entity **name** as the URL path segment (`/news/LeBron%20James?sport=NBA`) instead of entity type + ID. The Go API requires a numeric entity ID and would have returned HTTP 400.

## Files Changed

**Modified (18 files in final commit after rebase):**
- `src/lib/utils/data-sources.ts` — full rewrite
- `src/lib/utils/api-fetcher.ts` — headers support
- `src/lib/server/fetch.ts` — headers passthrough
- `src/env.d.ts` — type declarations
- `.env.example` — env var configuration
- `src/components/PlayerProfileWidget.astro` — profile call
- `src/components/TeamProfileWidget.astro` — profile call
- `src/components/ProfileWidgetComparison.astro` — profile call
- `src/components/StatsComparison.astro` — stats call
- `src/components/StatsComparisonContent.astro` — stats call
- `src/components/StrengthsWeaknessesComparison.astro` — stats call
- `src/components/tabs/PlayerStatsTab.astro` — stats call
- `src/components/tabs/TeamStatsTab.astro` — stats call
- `src/components/tabs/NewsTab.astro` — news call
- `src/lib/tabs/twitter-tab.ts` — profile + twitter calls
- `src/lib/tabs/similarity-tab.ts` — similarity call
- `src/lib/utils/entity-resolver.ts` — profile call
- `src/lib/utils/co-mentions.ts` — news call

## Verification

- `npm run build` passes with 0 errors, 0 warnings (15 hints for now-unused `apiUrl` class fields which can be cleaned up separately).
- Commit `226daa5`.

## Result

The frontend now calls PostgREST directly with `Accept-Profile` headers for profile and stats endpoints, and the Go API for news and twitter. All API routing is centralized in `data-sources.ts` via `FetchTarget` tuples. ML endpoints (vibe, predictions, transfers) and similarity remain on FastAPI. The `DATA_SOURCES` config object in `data-sources.ts` remains the single switch point for routing any endpoint to a different backend.

**Important:** PostgREST must be configured to allow `Accept-Profile` in CORS `Access-Control-Allow-Headers` for browser-side requests to succeed.
