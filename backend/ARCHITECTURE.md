# Backend Architecture

The backend is organized into a lean, layered FastAPI application under `backend/app`.

## Directory Layout

```text
backend/app/
  main.py              # FastAPI application factory & router mounting
  config.py            # Pydantic Settings (environment-driven configuration)
  routers/             # Thin HTTP route definitions (no business logic)
    sport.py           # Sport & entity endpoints (search, sync, mentions, stats)
    widgets.py         # Server-rendered player widget envelope (ETag + caching)
    news.py            # News & mentions aggregation
    twitter.py         # Stub social router
    reddit.py          # Stub social router
  services/            # Business logic & integration boundaries
    widget_service.py  # Payload assembly for player widgets
    news_service.py    # RSS + News API aggregation & caching
    apisports.py       # API-Sports provider abstraction
    cache.py           # In-memory caches (widget_cache, basic_cache)
  database/            # Local SQLite helpers & seeding utilities
    local_dbs.py       # Per-sport player/team storage & search
    seed_local_dbs.py  # Seeding script (API or static fallback)
    inspect_local_db.py# Inspection utilities
    provider_ingestion.py # Unified provider ingestion (replaces legacy registry)
  models/              # Pydantic schemas & envelopes
  utils/               # Cross-cutting utilities (constants, http_client)
  adapters/            # Currently empty (previous transitional re-exports removed)
```text

## Layer Responsibilities

- Routers: HTTP shape, parameter validation, simple orchestration (no heavy logic).
- Services: Sport/news/widget logic, upstream provider calls, caching decisions.
- Database: Local persistence for autocomplete & offline operation; no ORM used.
- Models: Stable API response shapes (e.g., `WidgetEnvelope`, diagnostics, error envelopes).
- Utils: Small generic helpers (HTTP client lifecycle, constants).

## Caching & Performance

Widgets use an in-memory cache keyed by `widgets:player:{SPORT}:{PLAYER_ID}:{SEASON}:v{VERSION}` with TTL (default 600s) and ETag for conditional GETs (304 support). Headers advertise `stale-while-revalidate` semantics to allow client-side grace periods.

## Migration Notes

The legacy `app/api` package and `core/config.py` have been removed. All imports should target:

```python
from app.config import settings
from app.routers import sport  # example
from app.services import widget_service
```

## Adding A New Feature

1. Define or extend a Pydantic model under `models/` if you need structured output.
2. Implement logic in a new or existing service module.
3. Create a router module that calls the service and returns serialized models.
4. Mount the router in `main.py` with an explicit prefix & tag.
5. Add caching or ETag only in the service / composition layer—avoid mixing it directly into routers.

## Testing / Health

Use `/api/health` for a basic liveness probe. Future work: add a `tests/` directory with async tests exercising critical routers and cache behavior.

## Recent Improvements

- Legacy `registry.py` removed; unified ingestion via `services/provider_ingestion.py`.
- Structured error codes & correlation IDs implemented (`utils/errors.py`, middleware).
- Rate limiting middleware added (configurable via `RATE_LIMIT_*` settings).

---
Last updated: 2025-11-07
