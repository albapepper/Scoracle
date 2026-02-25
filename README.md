# Scoracle -- Sports Intelligence Platform

A web app for sports news, statistics, and AI-powered insights across NBA, NFL, and Football (soccer).

## Features

- **Multi-Sport Support** -- NBA, NFL, and Football with unified API
- **News Aggregation** -- Real-time Google News RSS with co-mention detection
- **Statistics Dashboard** -- Season stats with percentile rankings and pizza charts
- **Player Comparison** -- Side-by-side stat comparisons with shareable URLs
- **AI-Powered Insights** -- Similarity matching, transfer predictions, sentiment analysis
- **Instant Search** -- Client-side autocomplete with 78K+ entities

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Railway                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              Astro Frontend (SSR/Static)              │  │
│  │  • News page with tabbed interface                    │  │
│  │  • Stats page with comparison feature                 │  │
│  │  • Client-side search from bundled JSON               │  │
│  └──────────────────────┬────────────────────────────────┘  │
│                         │ private network                    │
│  ┌──────────────────────▼────────────────────────────────┐  │
│  │              FastAPI Backend (Python)                  │  │
│  │  • Profile & stats endpoints                          │  │
│  │  • News aggregation                                   │  │
│  │  • ML predictions & similarity                        │  │
│  │  • PostgreSQL + Redis caching                         │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Project Structure

```
scoracle/
├── src/
│   ├── pages/
│   │   ├── index.astro           # Sport selector (crystal ball UI)
│   │   ├── news.astro            # News + social intel tabs (SSR)
│   │   ├── stats.astro           # Stats + comparison feature (SSR)
│   │   ├── co-mentions.astro     # Co-mention analysis
│   │   └── 404.astro
│   ├── components/
│   │   ├── PlayerProfileWidget.astro
│   │   ├── TeamProfileWidget.astro
│   │   ├── NewsContentCard.astro
│   │   ├── PlayerStatsContentCard.astro
│   │   ├── CrystalBallSelector.astro
│   │   └── tabs/                 # Individual tab components
│   ├── lib/
│   │   ├── types/                # Sport config & TypeScript types
│   │   ├── utils/                # API fetcher, autocomplete, caching
│   │   ├── server/               # SSR-only fetch utilities
│   │   ├── tabs/                 # Lazy-loaded tab modules
│   │   └── charts/               # Pizza chart visualization
│   ├── layouts/
│   │   └── Layout.astro
│   └── styles/
│       └── global.css
├── public/data/                  # Bundled JSON for instant search
│   ├── nba.json
│   ├── nfl.json
│   └── football.json             # 78K+ players & teams
├── docs/
│   ├── planning/                 # Architecture decisions
│   └── progress/                 # Session recaps
├── astro.config.mjs
├── tsconfig.json
└── package.json
```

## Pages

### Home (`/`)

Interactive sport selector with crystal ball carousel. Supports keyboard navigation and persists selection to localStorage.

### News (`/news?sport=NBA&type=player&id=123`)

Tabbed interface for entity intelligence:

- **News** -- Google News RSS articles
- **Co-mentions** -- Related entities mentioned together
- **Twitter** -- Journalist tweets (when configured)
- **Vibes** -- AI sentiment analysis

### Stats (`/stats?sport=NBA&type=player&id=123`)

Statistics dashboard with:

- **Stats** -- Season statistics with pizza chart percentiles
- **Strengths & Weaknesses** -- Derived from percentile analysis
- **Similarity** -- Players/teams with similar profiles (64D embeddings)
- **Momentum** -- Form-based momentum analysis (Football teams)
- **Transfers** -- AI transfer predictions with probabilities
- **Predictions** -- Next-game performance forecasts

**Comparison Mode:** Add `&compareType=player&compareId=456` for side-by-side comparisons.

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Astro 5, TypeScript, vanilla JS, native CSS |
| Hosting | Railway (frontend + backend, private network) |
| Backend | FastAPI, PostgreSQL, Redis |
| Data | Google News RSS, bundled JSON autocomplete |

### Frontend Optimizations

- **SWR Caching** -- Stale-while-revalidate with TTL presets
- **Request Deduplication** -- Prevents duplicate in-flight requests
- **SSR Hydration** -- Stats and news pages server-render with real data (no loading skeleton)
- **Lazy Tab Loading** -- Tabs fetch data only when activated
- **Entity Preloading** -- Instant search from bundled data
- **Console Stripping** -- Production builds remove debug logs

## Getting Started

### Prerequisites

- Node.js 18+

### Local Development

```bash
cp .env.example .env
npm install
npm run dev
```

The frontend runs on `http://localhost:4321` and calls the production API by default.

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PUBLIC_API_URL` | Backend API base URL | `https://scoracle-data-production.up.railway.app/api/v1` |
| `SITE_URL` | Canonical site URL (SEO) | `https://scoracle.vercel.app` |
| `FASTAPI_INTERNAL_URL` | Private Railway URL for SSR | _(set in Railway dashboard)_ |

See `.env.example` for the full list including future PostgREST and Go backend variables.

## API Reference

Backend hosted at: `https://scoracle-data-production.up.railway.app`

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/profile/{type}/{id}?sport={SPORT}` | Entity profile |
| `GET /api/v1/stats/{type}/{id}?sport={SPORT}` | Stats + percentiles |
| `GET /api/v1/news/{type}/{id}?sport={SPORT}` | Entity news |
| `GET /api/v1/twitter/status` | Twitter integration status |
| `GET /api/v1/twitter/journalist-feed?q={name}&sport={SPORT}` | Journalist tweets |
| `GET /api/v1/similarity/{type}/{id}?sport={SPORT}` | Similar entities |
| `GET /api/v1/ml/vibe/{type}/{id}?sport={SPORT}` | Vibe/sentiment score |
| `GET /api/v1/ml/transfers/predictions/{id}` | Transfer predictions |
| `GET /api/v1/ml/predictions/{type}/{id}/next` | Next-game forecast |

Full API docs: <https://scoracle-data-production.up.railway.app/docs>

## Deployment

### Railway

Deploys from the repository root using `Dockerfile` + `railway.toml`. Set environment variables in the Railway dashboard:

```
PUBLIC_API_URL=https://scoracle-data-production.up.railway.app/api/v1
FASTAPI_INTERNAL_URL=http://scoracle-data.railway.internal:8000/api/v1
SITE_URL=https://<your-railway-domain>
NODE_ENV=production
```

The container runs `node dist/server/entry.mjs` for SSR.

## License

MIT
