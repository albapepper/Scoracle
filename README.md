# Scoracle – Sports News & Advanced Statistics Platform

Scoracle is a modern web application that aggregates near‑real‑time sports news (Google News RSS) and statistics (API‑Sports provider) across multiple leagues. It delivers unified, cached API responses and rich interactive visualizations via a React frontend.

## ✨ Key Features

| Area | Highlights |
|------|-----------|
| Multi‑Sport | Pluggable sport context (currently NBA focus; NFL/EPL scaffolding) |
| Lean Endpoints | Sport-first endpoints return summaries; rich stats via client widgets |
| Smart Caching | Tiered in‑memory TTL caches for summaries and stats (invalidate naturally via TTL) |
| Mentions & Links | Configurable News API (fallback to refined Google RSS) |
| React Query | Automatic request dedupe + caching on frontend |
| Entity Preload Cache | Client context seeds detail pages to eliminate blank loading states |
| Error Envelope | Consistent JSON error contract for all unhandled exceptions |
| Sport‑First Paths | Canonical `/api/v1/{sport}/...` routes for multi‑sport expansion |
| Architecture Migration | Transitional layering toward `api/`, `domain/`, `adapters/`, `repositories/` |

## 🧱 Evolving Backend Architecture (Phase 1 ➜ Phase 2)

Current state is a lean backend exposing sport‑first endpoints with minimal aggregation. Most rich visualizations are handled on the frontend via provider widgets. Backend modules under `services/` will continue to be slimmed.

## 🗂 Project Structure (Transitional)
```
scoracle/
├── backend/
│   ├── app/
│   │   ├── main.py                # FastAPI app factory & router mounting
│   │   ├── core/                  # Settings, config
│   │   ├── models/                # Pydantic schemas (PlayerFullResponse, ErrorEnvelope, etc.)
│   │   ├── api/                   # Sport-first routes
│   │   ├── adapters/              # (New) Re-export wrappers for external services (RSS)
│   │   ├── services/              # (Legacy) External integration logic (to be relocated)
│   │   ├── repositories/          # Entity registry abstraction (SQLite)
│   │   └── domain/                # (Future) Core domain logic (stats transforms)
│   ├── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/                 # PlayerPage, TeamPage consume `/full` endpoints
│   │   ├── context/               # SportContext, EntityCacheContext
│   │   ├── services/              # `api.js` (axios + typed helper methods)
│   │   └── visualizations/        # D3 components (radar, bar charts)
├── api/
│   └── index.py                   # Vercel serverless entrypoint mounting FastAPI app
├── instance/
│   └── localdb/                   # Read-only SQLite seeds bundled for serverless
├── vercel.json                    # Vercel config (builds, routes, functions)
└── README.md
```

## 🚀 Getting Started

### Prerequisites

* Python 3.11+ (tested)
* Node.js 18+

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
 
React dev server proxies to `http://localhost:8000` (see `package.json` `proxy`).

## 📦 Caching Strategy

Layered in-memory TTL caches (`app/services/cache.py`):

* `basic_cache` – Player/team summaries (180–300s TTL)
* `stats_cache` – Season stats (300s TTL)
* Percentile cache removed – app now presents raw metrics only

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
GET /api/v1/{sport}/players/{player_id}
GET /api/v1/{sport}/players/{player_id}/stats
GET /api/v1/{sport}/players/{player_id}/mentions
GET /api/v1/{sport}/teams/{team_id}
GET /api/v1/{sport}/teams/{team_id}/stats
GET /api/v1/{sport}/teams/{team_id}/mentions
GET /api/v1/{sport}/entities?entity_type=player|team   # lean dump for client-side indexing
```

### Health & Maintenance

| Endpoint | Purpose |
|----------|---------|
| `GET /api/health` | Liveness probe |

## 🧮 Percentile Calculation

Percentiles are computed lazily per unique (entity, sport, season) from fetched stat distributions (service: `stats_percentile_service`). Missing stats yield `null` percentiles. Cached separately with a longer TTL to amortize CPU.

## 🗂 Frontend Data Layer

* React Query caches lean summaries keyed by `[entity, id, sport]`.
* `EntityCacheContext` stores lightweight summaries (player/team) seeded from Mentions → Stats navigation to eliminate initial spinner.

## 🔄 Navigation Flow

1. User selects sport and entity type (player or team) and searches.
2. Mentions page loads basic summary entity info (API provided) + news (configured News API when available, otherwise Google RSS fallback).
3. Clicking "View Stats" preloads summary into `EntityCacheContext`.
4. Player/Team page mounts: seeds state from cache immediately, then React Query fetch resolves full payload.

## 🔑 API Keys

Provider: API‑Sports. Set your key via environment variable `API_SPORTS_KEY`.

Optional provider: News API. Supply `NEWS_API_KEY` (default placeholder `YOUR_NEWS_API_KEY`). When configured, the backend queries the News API first for entity mentions and transparently falls back to Google RSS when no results are returned or if the key is missing. You can also override `NEWS_API_ENDPOINT` if you are proxying another compatible service.

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
   - Optional: `NEWS_API_KEY`, `NEWS_API_ENDPOINT`
4. Deploy. After deploy:
   - App UI: `https://<your-domain>/`
   - API docs: `https://<your-domain>/api/docs`
   - Health: `https://<your-domain>/api/health`

Notes:

- The serverless filesystem is read‑only; the app opens SQLite in read‑only mode automatically on Vercel.
- If bundle size grows, consider splitting sport DBs or moving them to an external object store/CDN.

## 📄 License

MIT License.
