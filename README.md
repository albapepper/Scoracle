# Scoracle – Sports Intelligence Platform

A modern web app for sports news, statistics, and AI-powered insights across NBA, NFL, and Football (soccer).

## Features

- **Multi-Sport Support** – NBA, NFL, and Football with unified API
- **News Aggregation** – Real-time Google News RSS with co-mention detection
- **Statistics Dashboard** – Season stats with percentile rankings and pizza charts
- **Player Comparison** – Side-by-side stat comparisons with shareable URLs
- **AI-Powered Insights** – Similarity matching, transfer predictions, sentiment analysis
- **Instant Search** – Client-side autocomplete with 78K+ entities
- **Dark/Light Mode** – System-aware theming with manual override

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Vercel                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              Astro Frontend (SSR/Static)              │  │
│  │  • News page with tabbed interface                    │  │
│  │  • Stats page with comparison feature                 │  │
│  │  • Client-side search from bundled JSON               │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        Railway                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              FastAPI Backend (Python)                 │  │
│  │  • Widget/Profile endpoints                           │  │
│  │  • News aggregation                                   │  │
│  │  • ML predictions & similarity                        │  │
│  │  • PostgreSQL + Redis caching                         │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Project Structure

```
scoracle/
├── astro-frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── home.astro      # Sport selector (crystal ball UI)
│   │   │   ├── news.astro      # News + social intel tabs
│   │   │   └── stats.astro     # Stats + comparison feature
│   │   ├── components/
│   │   │   ├── NewsContentCard.astro   # Tabbed news interface
│   │   │   ├── StatsContentCard.astro  # Tabbed stats interface
│   │   │   ├── ProfileWidget.astro     # Entity info display
│   │   │   ├── CrystalBallSelector.astro
│   │   │   └── tabs/           # Individual tab components
│   │   └── lib/
│   │       ├── types/          # Sport config & TypeScript types
│   │       ├── utils/          # API fetcher, autocomplete, caching
│   │       └── charts/         # Pizza chart visualization
│   └── public/data/            # Bundled JSON for instant search
│       ├── nba.json
│       ├── nfl.json
│       └── football.json       # 78K+ players & teams
├── vercel.json
└── README.md
```

## Pages & Features

### Home (`/`)

Interactive sport selector with crystal ball carousel. Supports keyboard navigation and persists selection to localStorage.

### News (`/news?sport=NBA&type=player&id=123`)

Tabbed interface for entity intelligence:

- **News** – Google News RSS articles
- **Co-mentions** – Related entities mentioned together
- **Twitter** – Live tweets (when configured)
- **Reddit** – Discussion threads
- **Vibes** – AI sentiment analysis

### Stats (`/stats?sport=NBA&type=player&id=123`)

Statistics dashboard with:

- **Stats** – Season statistics with pizza chart percentiles
- **Similarity** – Players/teams with similar profiles (64D embeddings)
- **Transfers** – AI transfer predictions with probabilities
- **Predictions** – Next-game performance forecasts

**Comparison Mode:** Add `&compareType=player&compareId=456` for side-by-side comparisons.

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Astro 5, TypeScript, Native CSS |
| Hosting | Vercel (frontend), Railway (backend) |
| Backend | FastAPI, PostgreSQL, Redis |
| Data | Google News RSS, bundled JSON autocomplete |

### Frontend Optimizations

- **SWR Caching** – Stale-while-revalidate with TTL presets
- **Request Deduplication** – Prevents duplicate in-flight requests
- **Lazy Tab Loading** – Tabs fetch data only when activated
- **Entity Preloading** – Instant search from bundled data
- **Console Stripping** – Production builds remove debug logs

## Getting Started

### Prerequisites

- Node.js 18+ (or Bun)

### Local Development

```bash
cd astro-frontend
cp .env.example .env
npm install
npm run dev
```

The frontend runs on `http://localhost:4321` and calls the production API by default.

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PUBLIC_API_URL` | Backend API base URL | `https://scoracle-data-production.up.railway.app/api/v1` |

## API Reference

Backend hosted at: `https://scoracle-data-production.up.railway.app`

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/widget/profile/{type}/{id}` | Entity info, stats, percentiles |
| `GET /api/v1/news?sport={SPORT}` | Sport-wide news |
| `GET /api/v1/news/{name}?sport={SPORT}` | Entity-specific news |
| `GET /api/v1/intel/twitter` | Twitter feed |
| `GET /api/v1/intel/reddit` | Reddit posts |
| `GET /api/v1/ml/similar/{type}/{id}` | Similar entities |
| `GET /api/v1/ml/transfers/predictions/{id}` | Transfer predictions |
| `GET /api/v1/ml/predictions/{type}/{id}/next` | Next-game forecast |

Full API docs: <https://scoracle-data-production.up.railway.app/docs>

## Deployment

### Vercel (Frontend)

1. Connect repo to Vercel
2. Set Root Directory: `astro-frontend`
3. Add env var: `PUBLIC_API_URL=https://scoracle-data-production.up.railway.app/api/v1`
4. Deploy

## License

MIT
