# Vercel to Railway Migration — Session Recap

**Date:** February 21, 2026  
**Scope:** Frontend architecture migration per `ARCHITECTURE-FRONTEND.md`  
**Status:** Core infrastructure complete. Backend swap deferred until Go/PostgREST builds stabilize.

---

## Goals

The `ARCHITECTURE-FRONTEND.md` document defined a target architecture for Scoracle's frontend that diverged from the production state in several fundamental ways. This session's goal was to close those gaps in a single coherent pass.

### Primary Goals

1. **Move from Vercel to Railway** — Replace the Vercel serverless deployment model with Railway's long-lived container model to eliminate cold starts, gain private network access to backend services, and achieve cost predictability for an ad-supported sports site with bursty traffic.

2. **Enable SSR for live data pages** — The frontend was fully static (`output: 'static'`), with all data fetching happening client-side after page load. The architecture doc calls for server-side rendering on pages that show live data (stats, news), so the user receives fully rendered HTML with no loading skeleton on first paint.

3. **Build a multi-backend data abstraction layer** — The backend is migrating from FastAPI (Python) to a Go + PostgREST architecture. The frontend needs to route requests to the correct backend (FastAPI, PostgREST, or Go) based on a central config, with private Railway network URLs on the server and public URLs on the client.

4. **Preserve all existing functionality** — The component bus, SWR caching, lazy tab loading, comparison mode, and client-side interactivity must continue to work exactly as before. SSR is additive — it provides the initial render, then the existing client-side code takes over.

### Secondary Goals

- Remove all Vercel deployment artifacts
- Update environment variable documentation for the Railway model
- Ensure the build passes cleanly with zero errors

### Explicitly Deferred

- **Cloudflare CDN integration** — The architecture doc marks this as a future enhancement for when geographic user distribution becomes a latency concern.
- **Actual PostgREST/Go endpoint wiring** — Both backends have Railway build failures currently. The abstraction layer is built and ready, but all requests route through FastAPI until the other backends stabilize.
- **Root `README.md` update** — Still references Vercel deployment. Should be updated when the Railway deployment is validated in production.
- **`astro-frontend/README.md` update** — Contains outdated information (references React, Tailwind, Tabler icons — none of which are used). Should be rewritten.

---

## Starting State

Before this session, the frontend had:

| Aspect | State |
|---|---|
| Astro output mode | `output: 'static'` — every page pre-rendered at build |
| SSR adapter | None installed |
| Data fetching | 100% client-side via `swrFetch()` in `<script>` blocks |
| First paint | Loading skeletons for all data — profile widgets, stats, news |
| Backend routing | Single `PUBLIC_API_URL` pointing at FastAPI |
| Deployment target | Vercel (serverless, `vercel.json` configs) |
| Private networking | None — all API calls over public internet |
| Server-only code | None — no `src/lib/server/` directory |

---

## What Was Built

The migration was executed in 6 phases.

### Phase 1: Astro Adapter & Hybrid Mode

**Files:** `astro.config.mjs`, `package.json`

- Installed `@astrojs/node` adapter for standalone Node.js SSR
- Configured `adapter: node({ mode: 'standalone' })` in Astro config
- Set `output: 'static'` with adapter present — in Astro 5, this is equivalent to the old `hybrid` mode: pages are static by default, individual pages opt into SSR with `export const prerender = false`
- Added `SITE_URL` env var support for canonical URL configuration
- Updated `start` script to `node dist/server/entry.mjs` for Railway

**Astro 5 note:** The architecture doc references `output: 'hybrid'`, which was removed in Astro 5. The equivalent behavior is `output: 'static'` with an adapter present. Pages use `export const prerender = false` to opt into SSR.

### Phase 2: Multi-Backend Data Abstraction Layer

**New file:** `src/lib/utils/data-sources.ts`

A routing layer that resolves the correct backend URL for each data type. Key design:

- **`DATA_SOURCES` config object** — maps each data type (profile, stats, news, twitter, similarity, vibe, momentum) to a backend source (`'fastapi'`, `'postgrest'`, or `'go'`). Currently all set to `'fastapi'`. Swapping a backend is a one-line change.
- **`getBaseUrl(source)`** — resolves the base URL for a backend, using private Railway internal URLs on the server (`typeof window === 'undefined'`) and public URLs on the client.
- **URL builder functions** — `profileUrl()`, `statsUrl()`, `newsUrl()`, `twitterStatusUrl()`, `twitterFeedUrl()`, `similarityUrl()`, `vibeUrl()`, `transfersUrl()`. Each function builds the correct URL shape for the active backend source.

**Environment variables introduced:**

| Variable | Context | Purpose |
|---|---|---|
| `FASTAPI_INTERNAL_URL` | Server-only | Private Railway URL for FastAPI |
| `POSTGREST_INTERNAL_URL` | Server-only | Private Railway URL for PostgREST |
| `GO_INTERNAL_URL` | Server-only | Private Railway URL for Go backend |
| `PUBLIC_POSTGREST_URL` | Client + Server | Public URL for PostgREST |
| `PUBLIC_GO_API_URL` | Client + Server | Public URL for Go backend |
| `SITE_URL` | Build time | Canonical site URL for SEO |

### Phase 3: Server-Side Fetch Utilities

**New file:** `src/lib/server/fetch.ts`

Server-only fetch functions used exclusively in Astro frontmatter (never in client `<script>` blocks). Astro's tree-shaking guarantees this code never reaches the browser.

- `serverFetch<T>(url, timeout)` — generic fetch with 5-second timeout, `AbortController`, and typed error handling via `SSRFetchResult<T>`
- `fetchProfile(sport, type, id)` — fetches player/team profile
- `fetchStats(sport, type, id)` — fetches stats + percentiles
- `fetchNews(sport, type, id)` — fetches news articles
- `fetchStatsPageData(sport, type, id)` — parallel fetch of profile + stats for the stats page
- `fetchNewsPageData(sport, type, id)` — parallel fetch of profile + news for the news page

All functions use `data-sources.ts` URL builders, so they automatically target the correct backend and use private network URLs when running on Railway.

### Phase 4: SSR Page Conversion

This was the most complex phase. Two pages were converted to SSR, and 7 components were updated to support server-rendered data.

#### Pages converted to SSR

**`src/pages/stats.astro`** and **`src/pages/news.astro`**:

- Added `export const prerender = false` — opts these pages out of static pre-rendering
- Frontmatter reads query params from `Astro.url.searchParams` (sport, type, id)
- Frontmatter calls `fetchStatsPageData()` or `fetchNewsPageData()` to fetch data server-side
- Data is passed to components as props (`initialData`, `initialStats`, `initialNews`)
- Data is also serialized into a `<script is:inline id="__SSR_DATA__" type="application/json">` tag for client-side hydration
- Page title is dynamically set from server-fetched entity name (e.g., "LeBron James Stats - Scoracle")

**Pages that remain static:** `index.astro`, `404.astro`, `co-mentions.astro` — these don't need live data on first paint.

#### SSR data flow

```
User requests /stats?sport=NBA&type=player&id=123
    |
    v
Astro SSR server reads URL params
    |
    v
fetchStatsPageData() fetches profile + stats in parallel
    | (private Railway network in production)
    v
Data passed to components as props
    |
    +---> PlayerProfileWidget renders HTML with real data (no skeleton)
    +---> PlayerStatsContentCard embeds stats as JSON for client
    +---> <script id="__SSR_DATA__"> embeds all data for hydration
    |
    v
Fully rendered HTML sent to user (single round trip)
    |
    v
Client-side <script> blocks hydrate:
    +---> Read embedded JSON instead of fetching
    +---> Populate component bus (so other components can access the data)
    +---> Register interactive behavior (comparison, tab switching)
    +---> Lazy tabs (Momentum, Similarity, etc.) still fetch on demand
```

#### Components updated

**Profile widgets** (`PlayerProfileWidget.astro`, `TeamProfileWidget.astro`):

- Accept `initialData` prop
- When present: render HTML server-side with real data (name, logo, subtitle, details), show content immediately (no skeleton), embed data in a `<script class="ssr-profile-data" type="application/json">` tag
- Client-side script checks `data-has-ssr="true"`, calls `hydrateFromSSR()` to populate class fields (entity name, position, position group) and register on the component bus, then skips the network fetch
- When `initialData` is absent (e.g., comparison widget loads a second entity): existing client-fetch behavior is preserved unchanged

**Content cards** (`PlayerStatsContentCard.astro`, `TeamStatsContentCard.astro`, `NewsContentCard.astro`):

- Accept `initialStats` or `initialNews` prop
- Embed the data as JSON in the DOM for the tab managers to find

**Tab managers** (`PlayerStatsTab.astro`, `TeamStatsTab.astro`, `NewsTab.astro`):

- Added `getSSRData()` method that checks the parent content card for embedded JSON
- `load()` checks SSR data first; if found, uses it directly and skips the network fetch
- If SSR data is absent, falls back to the existing `swrFetch()` path unchanged

### Phase 5: Railway Deployment Configuration

- Updated `package.json` `start` script: `"start": "node dist/server/entry.mjs"`
- Removed `vercel.json` (root)
- Removed `astro-frontend/vercel.json`
- Removed `.vercelignore`

Railway will auto-detect the Node.js project and use the `start` script.

### Phase 6: Environment & Cleanup

- Rewrote `astro-frontend/.env.example` with full documentation of all environment variables organized by category (site URL, public URLs, private URLs, Node env)
- Added `is:inline` directives to all `<script type="application/json">` tags to silence Astro build hints

---

## Files Changed

### Created (3 files)

| File | Purpose |
|---|---|
| `src/lib/utils/data-sources.ts` | Multi-backend routing abstraction (FastAPI / PostgREST / Go) |
| `src/lib/server/fetch.ts` | Server-only SSR fetch utilities with timeout and error handling |
| `src/lib/server/` (directory) | Container for server-only code |

### Modified (12 files)

| File | Changes |
|---|---|
| `astro.config.mjs` | `@astrojs/node` adapter, `SITE_URL` env, standalone mode |
| `package.json` | `@astrojs/node` dep, `start` script for Railway |
| `pages/stats.astro` | SSR opt-in, frontmatter data fetch, JSON hydration, dynamic title |
| `pages/news.astro` | SSR opt-in, frontmatter data fetch, JSON hydration, dynamic title |
| `components/PlayerProfileWidget.astro` | `initialData` prop, server-side HTML, `hydrateFromSSR()` |
| `components/TeamProfileWidget.astro` | `initialData` prop, server-side HTML, `hydrateFromSSR()` |
| `components/PlayerStatsContentCard.astro` | `initialStats` prop, SSR data embed |
| `components/TeamStatsContentCard.astro` | `initialStats` prop, SSR data embed |
| `components/NewsContentCard.astro` | `initialNews` prop, SSR data embed |
| `components/tabs/PlayerStatsTab.astro` | `getSSRData()` — reads embedded stats before network fetch |
| `components/tabs/TeamStatsTab.astro` | `getSSRData()` — reads embedded stats before network fetch |
| `components/tabs/NewsTab.astro` | `getSSRData()` — reads embedded news before network fetch |

### Updated (1 file)

| File | Changes |
|---|---|
| `.env.example` | Full Railway env var documentation (public, private, PostgREST, Go) |

### Removed (3 files)

| File | Reason |
|---|---|
| `vercel.json` (root) | Vercel no longer used |
| `astro-frontend/vercel.json` | Vercel no longer used |
| `.vercelignore` | Vercel no longer used |

---

## Architecture Alignment

How the implementation maps to each principle in `ARCHITECTURE-FRONTEND.md`:

| Principle | Target | Status |
|---|---|---|
| Pre-render static pages at build | `index`, `404`, `co-mentions` are static | Done |
| SSR for live data pages | `stats`, `news` use `prerender = false` | Done |
| `@astrojs/node` standalone adapter | Installed and configured | Done |
| Server-to-server private network fetch | `src/lib/server/fetch.ts` uses `data-sources.ts` URL resolution | Done |
| No loading skeleton on SSR pages | Profile widgets render server-side with real data | Done |
| Islands architecture | Interactive `<script>` blocks hydrate selectively | Unchanged (already aligned) |
| Railway hosting | `npm start` runs `node dist/server/entry.mjs` | Done |
| Private networking via internal hostnames | Env vars: `FASTAPI_INTERNAL_URL`, `POSTGREST_INTERNAL_URL`, `GO_INTERNAL_URL` | Done |
| PostgREST for stats | `data-sources.ts` supports `postgrest` source | Ready, not wired (backend builds failing) |
| Go backend for news/twitter | `data-sources.ts` supports `go` source | Ready, not wired (backend builds failing) |
| Cost model: no serverless overages | Railway long-lived container, no Vercel dependency | Done |
| No cold starts | Railway container mode | Done (deployment-side) |
| Cloudflare CDN | Future enhancement | Deferred per architecture doc |

---

## How to Swap Backends

When PostgREST or Go builds are stable on Railway, the swap is isolated to one file:

```typescript
// src/lib/utils/data-sources.ts

export const DATA_SOURCES: DataSourceConfig = {
  profile: 'fastapi',       // change to 'postgrest' when ready
  stats: 'postgrest',       // <-- swap this
  news: 'go',               // <-- swap this
  twitter: 'go',            // <-- swap this
  similarity: 'fastapi',
  vibe: 'fastapi',
  momentum: 'postgrest',    // <-- swap this
};
```

Then set the private network URLs in Railway's service dashboard:

```
POSTGREST_INTERNAL_URL=http://postgrest.railway.internal:3000
GO_INTERNAL_URL=http://scoracle-go.railway.internal:8080
```

If PostgREST returns a different response shape than FastAPI, add a response transformation in the relevant URL builder or in `src/lib/server/fetch.ts`. The rest of the app (components, tabs, charts) remains unchanged.

---

## Build Verification

Final build output:

```
Result (57 files):
- 0 errors
- 0 warnings
- 6 hints (pre-existing unused variables, unrelated to migration)

Prerendered static routes:
  /404.html
  /co-mentions/index.html
  /index.html

SSR routes (server-rendered on request):
  /stats
  /news

Server entrypoint: dist/server/entry.mjs
Adapter: @astrojs/node (standalone)
```

---

## Open Items for Future Sessions

1. **Validate Railway deployment end-to-end** — Deploy the built SSR server to Railway, configure env vars in the dashboard, and verify that stats/news pages render correctly with server-fetched data.

2. **Wire PostgREST endpoints** — Once PostgREST views are defined in Postgres and the Railway build succeeds, change `DATA_SOURCES.stats` and `DATA_SOURCES.momentum` to `'postgrest'`. May require response shape transformations.

3. **Wire Go backend endpoints** — Once the Go service builds are stable, change `DATA_SOURCES.news` and `DATA_SOURCES.twitter` to `'go'`.

4. **Update root `README.md`** — Still references Vercel deployment, Vercel architecture diagram, and `vercel.json`. Should reflect the Railway setup.

5. **Rewrite `astro-frontend/README.md`** — Contains outdated references to React, Tailwind, Tabler icons, and Vercel. None of these are used.

6. **Add `Cache-Control` headers to SSR responses** — The architecture doc notes that SSR responses can be cached at the edge when Cloudflare is added. Adding appropriate cache headers now prepares for that.

7. **Region alignment** — Verify that the Astro Railway service, PostgREST, and Neon Postgres are all in the same AWS region (e.g., `us-east-1`).
