# Scoracle – Sports News & Advanced Statistics Platform

Scoracle is a modern web application that aggregates near‑real‑time sports news (Google News RSS) and statistics (API‑Sports provider) across multiple leagues. It delivers unified, cached API responses and rich interactive visualizations via a React frontend.

## ✨ Key Features

| Area | Highlights |
|------|-----------|
| Multi‑Sport | Pluggable sport context (NBA focus; NFL + FOOTBALL (soccer) parity) |
| Lean Endpoints | Sport-first endpoints return summaries; rich stats via client widgets |
| Smart Caching | Tiered in‑memory TTL caches for summaries and stats (invalidate naturally via TTL) |
| Mentions & Links | Google News RSS pipeline (no external news dependency) |
| Lightweight Data Layer | Typed hooks replace prior React Query usage; local caching and ETag/304 support via axios wrapper |
| Entity Preload Cache | Client context seeds detail pages to eliminate blank loading states |
| Error Envelope | Consistent JSON error contract for all unhandled exceptions |
| Sport‑First Paths | Canonical `/api/v1/{sport}/...` routes for multi‑sport expansion |
| Architecture Focus | Lean FastAPI stack + local SQLite seeds (no registry/services bloat) |

## 🧱 Evolving Backend Architecture (Phase 1 ➜ Phase 2)

Current state is a lean backend exposing sport‑first endpoints with minimal aggregation. Most rich visualizations are handled on the frontend via provider widgets. Backend modules under `services/` will continue to be slimmed.

## 🗂 Project Structure (Current)

```text
scoracle/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI app + router mounting
│   │   ├── config.py        # Pydantic settings
│   │   ├── database/        # local SQLite helpers + seeds
│   │   ├── models/          # Widget envelope schemas
│   │   ├── routers/         # sports, players, teams, catalog, widgets, news, reddit, twitter
│   │   ├── services/        # apisports, cache, news_fast, widgets, social stubs
│   │   └── utils/           # constants, errors, middleware
│   ├── requirements.txt
├── api/
│   └── index.py             # Vercel serverless entry mounting backend/app
├── frontend/                # React app (Vite)
├── instance/localdb/        # bundled SQLite snapshots
├── scripts/                 # misc helper scripts
└── vercel.json
```

> **2025-11 update:** the legacy `sport` router has been decomposed into dedicated `sports.py`, `players.py`, `teams.py`, and `catalog.py` routers. The backend autocomplete endpoint was removed—autocomplete now runs entirely in the frontend using IndexedDB bootstrap data.

### Router layout

- `sports.py` – sport metadata and `/api/v1/{sport}/search`
- `players.py` – player summaries, stats, mentions, widget HTML
- `teams.py` – team summaries, stats, mentions, widget HTML
- `catalog.py` – `/entities`, `/sync/*`, and `/bootstrap` dataset exports
- `widgets.py`, `news.py`, `twitter.py`, `reddit.py` – unchanged specialized routers

## 🚀 Getting Started

### Prerequisites

- Python 3.11+ (tested)
- Node.js 18+

### Backend Local Dev (Windows PowerShell)

```powershell
Copy-Item .env.example .env -Force
./local.ps1 backend            # runs API on :8000
```

API docs: [http://localhost:8000/api/docs](http://localhost:8000/api/docs)

### Frontend Local Dev

```powershell
./local.ps1 frontend
```
 
React dev server proxies to `http://localhost:8000` (see `frontend/package.json` `proxy`).

### Local Tooling

- Use `local.ps1` instead of Makefile:

```powershell
./local.ps1 backend   # start FastAPI on :8000
./local.ps1 frontend  # start CRA dev server on :3000
./local.ps1 up        # run both (backend in a job)
./local.ps1 types     # generate OpenAPI TS types -> frontend/src/types/api.ts
```

TypeScript is fully enabled in the frontend and JS/JSX sources were migrated. The compiler is configured with `allowJs: false`.

## 📦 Caching Strategy

Layered in-memory TTL caches (`app/services/cache.py`):

- `basic_cache` – Player/team summaries (180–300s TTL)
- `stats_cache` – Season stats (300s TTL)
- Percentile cache removed – app now presents raw metrics only

Cache keys are sport + entity + season namespaced. No manual invalidation yet; rely on TTL + ephemeral process restarts. Future: pluggable Redis backend.

## 🧪 Error Handling

All unexpected exceptions are wrapped into a consistent envelope:

```json
{
   "error": {
      "message": "Internal server error",
      "code": 500,
      "path": "http://localhost:8000/api/v1/player/123"
   }
}

```

HTTPExceptions preserve their code & message. Schema: `ErrorEnvelope`.

## 📘 API Overview

Base prefix: `/api/v1`

### Sport‑First API

```text
GET /api/v1/{sport}                               # router metadata
GET /api/v1/{sport}/search?query=...&entity_type=player|team

GET /api/v1/{sport}/players/{player_id}
GET /api/v1/{sport}/players/{player_id}/stats
GET /api/v1/{sport}/players/{player_id}/mentions
GET /api/v1/{sport}/players/{player_id}/widget/*   # HTML widgets for embeds

GET /api/v1/{sport}/teams/{team_id}
GET /api/v1/{sport}/teams/{team_id}/stats
GET /api/v1/{sport}/teams/{team_id}/mentions
GET /api/v1/{sport}/teams/{team_id}/widget/*

GET /api/v1/{sport}/entities?entity_type=player|team   # catalog router
GET /api/v1/{sport}/sync/players
GET /api/v1/{sport}/sync/teams
GET /api/v1/{sport}/bootstrap
```

### Health & Maintenance

| Endpoint | Purpose |
|----------|---------|
| `GET /api/health` | Liveness probe |

## 🧮 Percentile Calculation

Percentile math has been removed from the backend to keep the deployment lightweight. Historical references to `stats_percentile_service` or percentile caches can be ignored—the current API only returns raw stats from API‑Sports.

## 🗂 Frontend Data Layer

- React Query caches lean summaries keyed by `[entity, id, sport]`.
- `EntityCacheContext` stores lightweight summaries (player/team) seeded from Mentions → Stats navigation to eliminate initial spinner.

## 🔍 Autocomplete (Frontend)

Autocomplete now runs entirely in the browser using IndexedDB data seeded from `/api/v1/{sport}/bootstrap` (or the bundled JSON files inside `frontend/public/data`). The deprecated `/api/v1/{sport}/autocomplete/{entity_type}` endpoint has been removed. If you need to refresh the bundled data, regenerate the JSON snapshots and redeploy; the frontend will automatically sync IndexedDB on first load for each sport.

## 🔄 Navigation Flow

1. User selects sport and entity type (player or team) and searches.
2. Mentions page loads basic summary entity info (API provided) plus news fetched from Google News RSS via the lean `news_fast` pipeline.
3. Clicking "View Stats" preloads summary into `EntityCacheContext`.
4. Player/Team page mounts: seeds state from cache immediately, then React Query fetch resolves full payload.

## 🔑 API Keys

Provider: API‑Sports. Set your key via environment variable `API_SPORTS_KEY`.

Frontend widgets (optional): to enable API‑Sports client-side widgets, add a React environment variable in `frontend/.env`:

```bash
# frontend/.env
REACT_APP_APISPORTS_KEY=your_api_sports_key_here
```

Alternatively, you can set `REACT_APP_APISPORTS_WIDGET_KEY` for compatibility. At runtime, a temporary key can be provided via localStorage (`APISPORTS_WIDGET_KEY`) or URL query `?apisportsKey=...` for quick testing.

## 📤 Deployment (Vercel)

This repo is configured for Vercel:

- Frontend: React app under `frontend/` is built with `@vercel/static-build` and served as a static site.
- Backend: FastAPI app is exposed as a Python Serverless Function at `/api` via `api/index.py`.
- Local SQLite seeds under `instance/localdb/` are bundled read‑only and used by sync endpoints to seed the client’s IndexedDB.

Steps:

1. Connect the repository to Vercel.
2. No framework selection needed; `vercel.json` handles builds and routes.
3. Environment variables (Project → Settings → Environment Variables):
   - `API_SPORTS_KEY`
4. Deploy. After deploy:
   - App UI: `https://<your-domain>/`
   - API docs: `https://<your-domain>/api/docs`
   - Health: `https://<your-domain>/api/health`

Notes:

- The serverless filesystem is read‑only; the app opens SQLite in read‑only mode automatically on Vercel.
- If bundle size grows, consider splitting sport DBs or moving them to an external object store/CDN.

## 📄 License

MIT License.
