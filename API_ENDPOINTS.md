# API Endpoints Reference

This document lists all API endpoints currently defined in the Scoracle backend. Use this to identify endpoints that are no longer needed and can be removed.

## Base URL
All endpoints are prefixed with `/api/v1` unless otherwise noted.

## Health & Info
- `GET /health` - Health check endpoint
- `GET /` - Root endpoint with API info
- `GET /api/docs` - Swagger UI documentation
- `GET /api/redoc` - ReDoc documentation
- `GET /api/openapi.json` - OpenAPI schema

---

## Sports Router (`/api/v1/{sport}`)
- `GET /api/v1/{sport}` - Get sport metadata
- `GET /api/v1/{sport}/search` - Search players or teams (query param: `query`, `entity_type`)

---

## Players Router (`/api/v1/{sport}/players`)
- `GET /api/v1/{sport}/players/{player_id}` - Get player summary
- `GET /api/v1/{sport}/players/{player_id}/stats` - Get player statistics (optional: `season` param)
- `GET /api/v1/{sport}/players/{player_id}/mentions` - Get player mentions
- `GET /api/v1/{sport}/players/{player_id}/seasons` - Get available seasons for player
- `GET /api/v1/{sport}/players/{player_id}/widget/basic` - Get basic player widget HTML
- `GET /api/v1/{sport}/players/{player_id}/widget/offense` - Get offense player widget HTML
- `GET /api/v1/{sport}/players/{player_id}/widget/defensive` - Get defensive player widget HTML
- `GET /api/v1/{sport}/players/{player_id}/widget/special-teams` - Get special teams player widget HTML (NFL only)
- `GET /api/v1/{sport}/players/{player_id}/widget/discipline` - Get discipline player widget HTML (NFL only)

---

## Teams Router (`/api/v1/{sport}/teams`)
- `GET /api/v1/{sport}/teams/{team_id}` - Get team summary
- `GET /api/v1/{sport}/teams/{team_id}/stats` - Get team statistics (optional: `season` param)
- `GET /api/v1/{sport}/teams/{team_id}/mentions` - Get team mentions
- `GET /api/v1/{sport}/teams/{team_id}/roster` - Get team roster
- `GET /api/v1/{sport}/teams/{team_id}/widget/basic` - Get basic team widget HTML
- `GET /api/v1/{sport}/teams/{team_id}/widget/offense` - Get offense team widget HTML
- `GET /api/v1/{sport}/teams/{team_id}/widget/defensive` - Get defensive team widget HTML
- `GET /api/v1/{sport}/teams/{team_id}/widget/special-teams` - Get special teams team widget HTML (NFL only)
- `GET /api/v1/{sport}/teams/{team_id}/widget/discipline` - Get discipline team widget HTML (NFL only)

---

## Catalog Router (`/api/v1/{sport}`)
- `GET /api/v1/{sport}/entities` - Get all entities dump (query param: `entity_type` = "player" or "team")
- `GET /api/v1/{sport}/sync/players` - Sync players data (for IndexedDB)
- `GET /api/v1/{sport}/sync/teams` - Sync teams data (for IndexedDB)
- `GET /api/v1/{sport}/bootstrap` - Get bootstrap dataset (query params: `entity_type`, `etag`)

---

## News Router (`/api/v1`)
- `GET /api/v1/news/mentions/{entity_type}/{entity_id}` - Get news mentions for entity
- `GET /api/v1/news/fast` - Fast news endpoint
- `GET /api/v1/news/fast/{entity_type}/{entity_id}` - Fast news for specific entity
- `GET /api/v1/news/debug` - News debug endpoint

---

## Widgets Router (`/api/v1`)
- `GET /api/v1/widgets/player/{player_id}` - Get player widget (query params: `sport`, `season`, `debug`)

---

## Twitter Router (`/api/v1`)
- `GET /api/v1/twitter/{entity_type}/{entity_id}` - Get Twitter mentions for entity

---

## Reddit Router (`/api/v1`)
- `GET /api/v1/reddit/{entity_type}/{entity_id}` - Get Reddit mentions for entity

---

## Notes for Review

1. **Widget endpoints**: There are multiple widget endpoints per entity type (basic, offense, defensive, special-teams, discipline). Consider if all are needed.

2. **Search endpoint**: `/api/v1/{sport}/search` - Check if this is still used since autocomplete was moved to frontend IndexedDB.

3. **Sync endpoints**: `/api/v1/{sport}/sync/players` and `/api/v1/{sport}/sync/teams` - These were added for IndexedDB sync. Verify they're being used.

4. **Bootstrap endpoint**: `/api/v1/{sport}/bootstrap` - Check if this is still needed with IndexedDB implementation.

5. **Social media endpoints**: Twitter and Reddit routers - Verify if these are actively used.

6. **News endpoints**: Multiple news endpoints exist. Review which ones are actually called by the frontend.

7. **Legacy router**: There's a `sport.py` router file that may be deprecated (per README, it was decomposed into sports/players/teams/catalog).

