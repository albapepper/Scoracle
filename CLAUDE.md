# CLAUDE.md — Scoracle AI Assistant Guide

## Project Overview

Scoracle is a sports intelligence web platform covering NBA, NFL, and Football (soccer). It provides news aggregation, statistics dashboards, player/team comparisons, and AI-powered insights (similarity matching, transfer predictions, sentiment analysis). The frontend is built with Astro 5 + TypeScript + vanilla JS and deployed on Railway as a Docker container.

## Tech Stack

- **Framework:** Astro 5 with hybrid rendering (static by default, SSR opt-in)
- **Language:** TypeScript (strict mode), vanilla JavaScript for client interactivity
- **Styling:** Native CSS with CSS custom properties (no Tailwind, no CSS-in-JS)
- **Adapter:** `@astrojs/node` in standalone mode for Railway deployment
- **Build:** Astro build with Terser minification, `astro-compress` in production
- **Backend:** FastAPI (Python) — separate repo, accessed via REST API
- **Deployment:** Railway via Docker (multi-stage `node:20-alpine`)

## Quick Reference

```bash
npm install          # Install dependencies
npm run dev          # Dev server at http://localhost:4321
npm run build        # Type-check (astro check) + production build
npm run check        # TypeScript type checking only
npm run start        # Run production server (node dist/server/entry.mjs)
```

Requires Node.js 18+. Copy `.env.example` to `.env` before running. The dev server calls the production API by default.

## Project Structure

```
src/
├── pages/                    # Astro pages (routes)
│   ├── index.astro           # Home — static, crystal ball sport selector
│   ├── news.astro            # News — SSR (prerender = false)
│   ├── stats.astro           # Stats — SSR (prerender = false)
│   ├── co-mentions.astro     # Co-mention analysis page
│   └── 404.astro             # Custom 404
├── components/               # Astro components
│   ├── Header.astro
│   ├── HamburgerMenu.astro         # Uses <details>/<summary> (CSS-only)
│   ├── CrystalBallSelector.astro   # Home page sport carousel
│   ├── ComparisonSearchModal.astro  # Uses <dialog> element
│   ├── PlayerProfileWidget.astro
│   ├── TeamProfileWidget.astro
│   ├── PlayerStatsContentCard.astro
│   ├── TeamStatsContentCard.astro
│   ├── NewsContentCard.astro
│   ├── EntityWidgetPair.astro
│   ├── ProfileWidgetComparison.astro
│   ├── StatsComparison.astro
│   ├── StatsComparisonContent.astro
│   ├── StrengthsWeaknessesComparison.astro
│   ├── SharedArticlesCard.astro
│   ├── SharedContentCard.astro
│   └── tabs/                 # Lazy-loaded tab components
│       ├── NewsTab.astro
│       ├── CoMentionsTab.astro
│       ├── TwitterTab.astro
│       ├── VibesTab.astro
│       ├── PlayerStatsTab.astro
│       ├── TeamStatsTab.astro
│       ├── StrengthsWeaknessesTab.astro
│       ├── SimilarityTab.astro
│       ├── Momentum.astro
│       ├── TransfersTab.astro
│       └── PredictionsTab.astro
├── lib/
│   ├── types/index.ts        # Central type definitions & sport config (SINGLE SOURCE OF TRUTH)
│   ├── server/fetch.ts       # SSR-only fetch utilities (never import client-side)
│   ├── utils/
│   │   ├── data-sources.ts   # Multi-backend URL routing abstraction
│   │   ├── api-fetcher.ts    # SWR cache + request deduplication + page data store
│   │   ├── autocomplete.ts   # Client-side search/autocomplete logic
│   │   ├── entity-data-store.ts  # Preloads all sport JSON for instant search
│   │   ├── component-bus.ts  # Typed inter-component communication registry
│   │   ├── tab-controller.ts # Lightweight tab switching with lazy-load support
│   │   ├── dom.ts            # DOM helpers: showState(), showWidgetState(), escapeHtml()
│   │   ├── co-mentions.ts    # Co-mention analysis utilities
│   │   ├── entity-resolver.ts
│   │   ├── profile-renderer.ts
│   │   ├── position-groups.ts  # Position normalization per sport
│   │   ├── stats-categorizer.ts
│   │   ├── season.ts
│   │   └── date.ts
│   ├── tabs/                 # Client-side tab logic (lazy-loaded modules)
│   │   ├── co-mentions-tab.ts
│   │   ├── momentum-tab.ts
│   │   ├── similarity-tab.ts
│   │   ├── strengths-weaknesses-tab.ts
│   │   └── twitter-tab.ts
│   └── charts/
│       └── pizza-chart.ts    # SVG pizza chart for percentile visualization
├── layouts/
│   └── Layout.astro          # Base HTML layout with SEO meta tags
├── styles/
│   └── global.css            # CSS custom properties, design tokens, base styles
├── assets/images/            # Sport logos (processed by Astro <Image>)
└── env.d.ts                  # Astro environment type declarations
public/
├── favicon.svg
└── data/                     # Bundled JSON for client-side autocomplete
    ├── nba.json
    ├── nfl.json
    └── football.json          # ~78K entities total
docs/
├── planning/                 # Architecture decisions and migration plans
└── progress/                 # Session recaps and changelog
```

## Architecture & Key Patterns

### Rendering Strategy

- **Static by default:** `index.astro`, `co-mentions.astro`, `404.astro` are pre-rendered at build time.
- **SSR for live data:** `news.astro` and `stats.astro` use `export const prerender = false` to server-render with real data from the API, eliminating loading skeletons.
- Pages opt into SSR individually. Astro's `output: 'static'` config with the Node adapter allows this hybrid behavior.

### SSR Data Hydration

SSR pages embed fetched data as JSON in `<script is:inline id="__SSR_DATA__">` tags. Client-side scripts read this on load to avoid re-fetching. If SSR data is missing (e.g., direct navigation), components fall back to client-side fetch.

### Multi-Backend Abstraction (`src/lib/utils/data-sources.ts`)

All API URLs are routed through `data-sources.ts`. The `DATA_SOURCES` config maps each data type (profile, stats, news, etc.) to a backend source (`'fastapi'`, `'postgrest'`, or `'go'`). Currently everything routes to FastAPI. To swap a backend:
1. Change the source in `DATA_SOURCES`
2. Update the URL builder function's `switch` case if needed
3. The rest of the app is unchanged

On the server, private Railway internal URLs are preferred. On the client, public URLs are used.

### Client-Side Caching (`src/lib/utils/api-fetcher.ts`)

- **SWR pattern:** Serves stale data instantly, revalidates in background
- **Request deduplication:** Concurrent requests for the same URL share one fetch
- **ETag support:** Conditional requests for profile/stats endpoints
- **Cache presets:** Aligned with backend TTLs (widget: 30min, stats: 5min, news: 2min)
- **Page data store:** `setPageData()`/`getPageData()` for sharing fetched data between components on the same page

### Component Bus (`src/lib/utils/component-bus.ts`)

A typed pub/sub registry for cross-component communication. Components `register()` their API, and consumers `get()` or `waitFor()` them. This replaces `(window as any)` globals with type-safe access.

### Tab System

- **Tab controller** (`initTabs()`): Handles tab button clicks, CSS class toggling, lazy-load callbacks, and hover-prefetch.
- **Eager tabs** (Stats, News): Load data on page render.
- **Lazy tabs** (Similarity, Momentum, Transfers, etc.): Fetch data only when the tab is first activated.
- **Tab content modules** (`src/lib/tabs/`): Separated from Astro components for lazy loading.

### DOM State Management

Use `showState(container, prefix, activeState)` from `src/lib/utils/dom.ts` to toggle between loading/content/empty/error states. Elements follow the convention `id="{prefix}-{state}"`.

For profile widgets, use `showWidgetState(loadingEl, contentEl, errorEl, state)` which toggles `display: none/flex`.

### Entity Data Store

`entityDataStore` (singleton) preloads all sport JSON files (`public/data/*.json`) in parallel on app startup for instant autocomplete search. It supports both legacy format (separate `players`/`teams` arrays) and v2.0 format (flat `entities` array).

## Coding Conventions

### TypeScript & Types

- **Strict mode** enabled. All types in `src/lib/types/index.ts`.
- **Path aliases:** `@/*` maps to `src/*` (also `@components/*`, `@layouts/*`, `@lib/*`, `@pages/*`).
- **Sport config** is the single source of truth in `src/lib/types/index.ts`. To add a new sport: add to `SportId` type, add to `SPORTS` array, add data JSON to `public/data/`.
- Use `EntityType` (`'player' | 'team'`) and `SportId` (`'NBA' | 'NFL' | 'FOOTBALL'`) types consistently.

### Vanilla JS & HTML

- **No frontend framework** beyond Astro. All interactivity is vanilla JS in `<script>` blocks.
- Prefer **native HTML elements**: `<dialog>` for modals, `<details>`/`<summary>` for collapsibles.
- Use **module-level functions** (not classes). Classes were refactored out; the codebase favors flat functions.
- Zero external JS dependencies for UI. The only dependencies are Astro, its Node adapter, and `astro-compress`.

### CSS

- **CSS custom properties** for all colors (defined in `src/styles/global.css`).
- **Warm neutral palette:** `--bg: #faf9f7`, `--text: #1a1a1a`, etc. Anthropic/NYT inspired.
- **Dark mode** variables exist but dark mode is currently disabled (forced light in Layout.astro).
- **Scoped styles** via `<style scoped>` in Astro components; global styles in `global.css`.
- No shadows. Minimal hover effects. Low blue light aesthetic.
- **Percentile tier colors** use a 5-level scale: elite (green), above (blue), average (amber), below (orange), poor (red).

### File Naming

- Astro components: `PascalCase.astro`
- TypeScript modules: `kebab-case.ts`
- Image files: `kebab-case.png` (no spaces)

### XSS Prevention

Use `escapeHtml()` from `src/lib/utils/dom.ts` when rendering any user-provided or API-provided strings into HTML.

## Environment Variables

| Variable | Context | Description |
|----------|---------|-------------|
| `PUBLIC_API_URL` | Client + Server | FastAPI backend base URL |
| `SITE_URL` | Build time | Canonical URL for SEO meta tags |
| `FASTAPI_INTERNAL_URL` | Server only | Private Railway network URL for SSR fetches |
| `NODE_ENV` | Runtime | `development` or `production` |

`PUBLIC_` prefix variables are available in client-side `<script>` blocks via `import.meta.env.PUBLIC_*`. Private variables (no prefix) are only available in Astro frontmatter (server context).

See `.env.example` for the full list including future PostgREST and Go backend variables.

## API Endpoints (Backend)

Backend at: `https://scoracle-data-production.up.railway.app`

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/profile/{type}/{id}?sport={SPORT}` | Entity profile |
| `GET /api/v1/stats/{type}/{id}?sport={SPORT}` | Stats + percentiles |
| `GET /api/v1/news/{type}/{id}?sport={SPORT}` | Google News articles |
| `GET /api/v1/twitter/status` | Twitter integration status |
| `GET /api/v1/twitter/journalist-feed?q={name}&sport={SPORT}` | Journalist tweets |
| `GET /api/v1/similarity/{type}/{id}?sport={SPORT}` | Similar entities (64D embeddings) |
| `GET /api/v1/ml/vibe/{type}/{id}?sport={SPORT}` | Sentiment/vibe score |
| `GET /api/v1/ml/transfers/predictions/{id}` | Transfer predictions |
| `GET /api/v1/ml/predictions/{type}/{id}/next` | Next-game forecast |

## Deployment

- **Platform:** Railway using Docker (`Dockerfile` + `railway.toml`)
- **Container:** Multi-stage build: `node:20-alpine` build stage + runtime stage
- **Runtime command:** `node dist/server/entry.mjs`
- **Port:** 3000
- **Health check:** `GET /` with 15s timeout
- Set environment variables in Railway dashboard (not in code)

## Progress Documentation

After completing any major edit — new feature, new file/folder, or significant refactor — generate a markdown summary and save it to `docs/progress/`. This is **mandatory**, not optional.

### When to write a progress entry

- Adding a new feature or page
- Creating new files or directories
- Significant refactoring (restructuring, renaming, rewriting modules)
- Architectural changes (new patterns, dependency changes, config overhauls)
- Bug fixes that required non-trivial investigation or multi-file changes

Do **not** write a progress entry for minor edits like typo fixes, comment updates, or single-line config tweaks.

### File naming

```
docs/progress/YYYY-MM-DD_short-description.md
```

Use today's date and a kebab-case slug describing the work. Examples:
- `2026-03-02_ssr-news-page.md`
- `2026-03-05_tab-system-refactor.md`

### Required format

```markdown
# Title of Change

**Date:** YYYY-MM-DD
**Scope:** What areas were affected (e.g., `src/components/`, `src/lib/utils/`)
**Commit(s):** `abc1234`

## Goal

2-3 sentences explaining the purpose and rationale.

## What Was Done

Detailed breakdown with numbered subsections for each major change.
Include implementation details, design decisions, and trade-offs.

## Files Changed

List or table of modified/added/deleted files with brief descriptions.

## Verification

Build checks, test results, and confirmation that changes work.
Include quantitative info where relevant (lines changed, file counts).
```

### Key principles

- Write in **narrative style** as a session recap for future reference
- Include **technical depth** — implementation details, not just high-level summaries
- Document **design decisions** and why alternatives were rejected
- Show **verification evidence** — that the build passes and changes work
- Keep it **concise but complete** — a future developer (or AI) should understand what happened and why

## Important Constraints

- **Server-only imports:** Never import `src/lib/server/fetch.ts` from client-side `<script>` blocks. Astro tree-shakes it out when only imported in frontmatter.
- **No console.log in production:** Terser drops `console.*` in production builds. Use `import.meta.env.DEV` guards for debug logging.
- **Private network URLs:** `*.railway.internal` hostnames only work server-side within Railway's private network. They must never appear in client-side code.
- **Sport IDs are uppercase** in API calls (`NBA`, `NFL`, `FOOTBALL`) but **lowercase** in file paths and URL slugs (`nba`, `nfl`, `football`).
