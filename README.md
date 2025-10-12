git clone https://github.com/albapepper/scoracle.git
docker-compose up
# Scoracle – Sports News & Advanced Statistics Platform

Scoracle is a modern web application that aggregates near‑real‑time sports news (Google News RSS) and statistics (balldontlie and future data providers) across multiple leagues. It delivers unified, cached API responses and rich interactive visualizations via a React frontend.

## ✨ Key Features

| Area | Highlights |
|------|-----------|
| Multi‑Sport | Pluggable sport context (currently NBA focus; NFL/EPL scaffolding) |
| Unified Aggregation | Single `/full` endpoints combine summary + stats + percentiles + mentions |
| Smart Caching | Tiered in‑memory TTL caches for summaries, stats, percentiles (invalidate naturally via TTL) |
| Mentions & Links | Google RSS query refinement w/ entity name resolution |
| React Query | Automatic request dedupe + caching on frontend |
| Entity Preload Cache | Client context seeds detail pages to eliminate blank loading states |
| Error Envelope | Consistent JSON error contract for all unhandled exceptions |
| Sport‑First Paths | Optional `/api/v1/{sport}/...` variants for future multi‑sport expansion |
| Architecture Migration | Transitional layering toward `api/`, `domain/`, `adapters/`, `repositories/` |

## 🧱 Evolving Backend Architecture (Phase 1 ➜ Phase 2)

Current state uses legacy `routers/` & `services/` plus new facade modules under `app/api/` & `app/adapters/` for a non‑breaking migration. Next phase: move logic into `domain/` (pure business rules), `adapters/` (upstream I/O), and `repositories/` (persistence), trimming old folders when parity is reached.

## 🗂 Project Structure (Transitional)
```
scoracle/
├── backend/
│   ├── app/
│   │   ├── main.py                # FastAPI app factory & router mounting
│   │   ├── core/                  # Settings, config
│   │   ├── models/                # Pydantic schemas (PlayerFullResponse, ErrorEnvelope, etc.)
│   │   ├── routers/               # (Legacy) routed endpoints (player, team, mentions, links, autocomplete, home)
│   │   ├── api/                   # (New) sport-first + re-export bridging layer
│   │   ├── adapters/              # (New) Re-export wrappers for external services (RSS, balldontlie)
│   │   ├── services/              # (Legacy) External integration logic (to be relocated)
│   │   ├── repositories/          # Entity registry abstraction (SQLite)
│   │   └── domain/                # (Future) Core domain logic (stats transforms, percentile calc wrappers)
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── pages/                 # PlayerPage, TeamPage consume `/full` endpoints
│   │   ├── context/               # SportContext, EntityCacheContext
│   │   ├── services/              # `api.js` (axios + typed helper methods)
│   │   └── visualizations/        # D3 components (radar, bar charts)
├── docker-compose.yml
└── README.md
```

## 🚀 Getting Started

### Prerequisites
* Python 3.11+ (tested)  
* Node.js 18+  
* Docker (optional but recommended for parity)

### Run Entire Stack (Docker)
```powershell
git clone https://github.com/albapepper/Scoracle.git
cd Scoracle
docker compose up --build
```

Frontend: [http://localhost:3000](http://localhost:3000)  
API Docs: [http://localhost:8000/api/docs](http://localhost:8000/api/docs)  
Health: [http://localhost:8000/api/health](http://localhost:8000/api/health)

### Backend Local Dev (Windows PowerShell)

```powershell
cd backend
python -m venv venv
./venv/Scripts/Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

API docs: [http://localhost:8000/api/docs](http://localhost:8000/api/docs)

### Frontend Local Dev

```powershell
cd frontend
npm install
npm start
```
React dev server proxies to `http://localhost:8000` (see `package.json` `proxy`).

### Quick One-Liners

```powershell
cd backend; ./venv/Scripts/Activate.ps1; uvicorn app.main:app --reload --port 8000
```

```bash
cd backend && source venv/bin/activate && uvicorn app.main:app --reload --port 8000
```

## 🔐 Configuration & Environment

Environment variables (optional) via `.env` in project root:

```env

```env
BALLDONTLIE_API_KEY=override_token
REGISTRY_DB_PATH=instance/registry.db
BALDONTLIE_DEBUG=0
```
Defaults are defined in `app/core/config.py`.

### API Provider: API-Sports

Autocomplete and global search now use API-Sports across sports. Configure your key:

* Windows PowerShell (local runs):
   * `$env:API_SPORTS_KEY = "<your-key>"`
* Docker Compose:
   * Ensure `API_SPORTS_KEY` is set in your shell environment before `docker compose up`.

Optional league/season overrides:

* `API_SPORTS_EPL_SEASON` (e.g., `2024`)
* `API_SPORTS_NBA_LEAGUE`, `API_SPORTS_NBA_SEASON`
* `API_SPORTS_NFL_LEAGUE`, `API_SPORTS_NFL_SEASON`

EPL basic player/team lookups are served via API-Sports. NBA/NFL detailed stats still use legacy routes while migration proceeds.

## 📦 Caching Strategy

Layered in-memory TTL caches (`app/services/cache.py`):

* `basic_cache` – Player/team summaries (180–300s TTL)
* `stats_cache` – Season stats (300s TTL)
* `percentile_cache` – Derived percentiles (30m TTL)

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

```json
```
HTTPExceptions preserve their code & message. Schema: `ErrorEnvelope`.

## 📘 API Overview

Base prefix: `/api/v1`

### Aggregated "Full" Endpoints (Recommended)

Return summary + stats + percentiles (+ optional mentions):

* `GET /api/v1/player/{player_id}/full?season=2023-2024&include_mentions=true&sport=NBA`
* `GET /api/v1/team/{team_id}/full?season=2023-2024&include_mentions=false&sport=NBA`

Example response (player):

```json
{
   "summary": {"id": "237", "sport": "NBA", "full_name": "LeBron James", ...},
   "season": "2023-2024",
   "stats": {"points_per_game": 25.1, ...},
   "percentiles": {"points_per_game": 92.3, ...},
   "mentions": [ {"title": "...", "link": "..."} ]
}
```

### Classic Resource Endpoints

| Type | Endpoint | Notes |
|------|----------|-------|
| Player summary+stats | `GET /api/v1/player/{id}?season=YYYY-YYYY` | Legacy combined format |
| Player seasons list | `GET /api/v1/player/{id}/seasons` | Placeholder static list currently |
| Player percentiles | `GET /api/v1/player/{id}/percentiles` | On-demand percentile calc |
| Team summary+stats | `GET /api/v1/team/{id}?season=...` | Legacy combined format |
| Team roster | `GET /api/v1/team/{id}/roster` | Placeholder empty list |
| Team percentiles | `GET /api/v1/team/{id}/percentiles` | On-demand percentile calc |
| Mentions | `GET /api/v1/mentions/{entity_type}/{id}` | RSS + basic info |
| Links | `GET /api/v1/links/{entity_type}/{id}` | Related link variants |
| Search | `GET /api/v1/search?q=lebron&sport=NBA` | Autocomplete/search |

### Sport‑First Variants

Allow future multi-sport frontends to pick a canonical style:

```text

```text
GET /api/v1/{sport}/players/{player_id}
GET /api/v1/{sport}/players/{player_id}/stats
GET /api/v1/{sport}/players/{player_id}/mentions
GET /api/v1/{sport}/teams/{team_id}
GET /api/v1/{sport}/teams/{team_id}/stats
GET /api/v1/{sport}/teams/{team_id}/mentions
```

### Health & Maintenance

| Endpoint | Purpose |
|----------|---------|
| `GET /api/health` | Liveness probe |
| `POST /api/v1/registry/refresh/{sport}` | Force registry (re)ingest |
| `GET /api/v1/registry/counts` | Registry status counts |

## 🧮 Percentile Calculation

Percentiles are computed lazily per unique (entity, sport, season) from fetched stat distributions (service: `stats_percentile_service`). Missing stats yield `null` percentiles. Cached separately with a longer TTL to amortize CPU.

## 🗂 Frontend Data Layer

* React Query caches `playerFull` / `teamFull` keyed by `[typeFull, id, season, sport]`.
* `EntityCacheContext` stores lightweight summaries (player/team) seeded from Mentions → Stats navigation to eliminate initial spinner (optimistic hydration).

## 🔄 Navigation Flow

1. User searches entity → selects result.
2. Mentions page loads summary + news.
3. Clicking "View Stats" preloads summary into `EntityCacheContext`.
4. Player/Team page mounts: seeds state from cache immediately, then React Query fetch resolves full payload.

## 🛠 Local Troubleshooting

| Issue | Fix |
|-------|-----|
| CORS error | Ensure frontend dev server proxy or add origin to `BACKEND_CORS_ORIGINS`. |
| 404 on player route | Verify new prefixed route `/api/v1/player/{id}` not old root style. |
| Empty mentions | RSS may have no hits; try broader name variant or verify internet access. |
| Stale data | TTL caches keep data warm; restart app or wait for expiry. |

## 🧭 Roadmap (Next Phases)

| Phase | Goal |
|-------|-----|
| 2 | Migrate logic: `services/` → `adapters/` & `domain/` (remove duplication) |
| 2 | Add Redis (optional) for multi-instance cache coherence |
| 3 | Implement real seasons + roster sources (replace placeholders) |
| 3 | OpenAPI → TypeScript type generation (`openapi-typescript`) |
| 4 | Add comparison & trend endpoints |
| 4 | Auth & favorites |

## 🔑 API Keys

Currently using balldontlie public API key (config default). Override with environment variable `BALLDONTLIE_API_KEY`.

## 📤 Deployment

See `docs/deployment/cloud-run.md` for Google Cloud Run steps (build images, push to Artifact Registry, deploy services, set concurrency/timeouts).

## 🧰 Developer Productivity

### PowerShell Helper (Windows)

Use `dev.ps1` from repository root:

```powershell
./dev.ps1 backend   # start backend only
./dev.ps1 frontend  # start frontend only
./dev.ps1 up        # start both (backend job + frontend)
./dev.ps1 types     # generate OpenAPI TypeScript types
```

### Make Targets (macOS/Linux)

```bash
make backend    # backend with reload
make frontend   # react dev server
make up         # run both concurrently
make types      # generate TS types from OpenAPI
```

## 🧾 TypeScript API Types

Run after backend schema changes (ensure backend running so OpenAPI is reachable):

```bash
npm run api:types
```

Output: `frontend/src/types/api.ts` (do not edit manually).

## 📄 License

MIT License. See `LICENSE` (add if not present).

---
Questions or ideas? Open an issue or start a discussion – contributions welcome.
