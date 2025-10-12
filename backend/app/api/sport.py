from fastapi import APIRouter, Path, Query, HTTPException
from app.adapters.balldontlie_api import get_player_info, get_player_stats, get_team_info, get_team_stats
from app.models.schemas import PlayerFullResponse, TeamFullResponse
from app.routers import player as player_router_mod
from app.routers import team as team_router_mod
from app.routers import autocomplete as autocomplete_router_mod
from app.adapters.google_rss import get_entity_mentions

router = APIRouter()

@router.get("/{sport}/players/{player_id}")
async def sport_player_summary(sport: str, player_id: str):
    info = await get_player_info(player_id, sport, basic_only=True)
    return {"summary": info, "sport": sport.upper(), "id": player_id}

@router.get("/{sport}/players/{player_id}/stats")
async def sport_player_stats(sport: str, player_id: str, season: str | None = Query(None)):
    stats = await get_player_stats(player_id, sport, season=season)
    return {"player_id": player_id, "sport": sport.upper(), "season": season or "current", "stats": stats}

@router.get("/{sport}/players/{player_id}/full", response_model=PlayerFullResponse)
async def sport_player_full(sport: str, player_id: str, season: str | None = Query(None), include_mentions: bool = Query(True)):
    # Proxy to existing player endpoint with sport injected
    return await player_router_mod.get_player_full(player_id=player_id, season=season, include_mentions=include_mentions, sport=sport)

@router.get("/{sport}/players/{player_id}/mentions")
async def sport_player_mentions(sport: str, player_id: str):
    mentions = await get_entity_mentions("player", player_id, sport)
    return {"player_id": player_id, "sport": sport.upper(), "mentions": mentions}

@router.get("/{sport}/teams/{team_id}")
async def sport_team_summary(sport: str, team_id: str):
    info = await get_team_info(team_id, sport, basic_only=True)
    return {"summary": info, "sport": sport.upper(), "id": team_id}

@router.get("/{sport}/teams/{team_id}/stats")
async def sport_team_stats(sport: str, team_id: str, season: str | None = Query(None)):
    stats = await get_team_stats(team_id, sport, season=season)
    return {"team_id": team_id, "sport": sport.upper(), "season": season or "current", "stats": stats}

@router.get("/{sport}/teams/{team_id}/full", response_model=TeamFullResponse)
async def sport_team_full(sport: str, team_id: str, season: str | None = Query(None), include_mentions: bool = Query(True)):
    return await team_router_mod.get_team_full(team_id=team_id, season=season, include_mentions=include_mentions, sport=sport)

@router.get("/{sport}/autocomplete/{entity_type}")
async def sport_autocomplete_proxy(sport: str, entity_type: str, q: str = Query(...), limit: int = Query(8, ge=1, le=15)):
    # Proxy to existing autocomplete with sport injected
    # We can’t call the router method directly with Request/Response, so reimplement thin call
    # by delegating to the same service used by autocomplete for deterministic behavior.
    from app.services.apisports import apisports_service
    entity = entity_type.strip().lower()
    if entity not in {"player", "team"}:
        raise HTTPException(status_code=400, detail="Entity type must be 'player' or 'team'")
    if len((q or "").strip()) < 2:
        return {"query": q, "entity_type": entity, "sport": sport, "results": []}
    if entity == "player":
        rows = await apisports_service.search_players(q, sport)
        results = [{
            "id": r.get("id"),
            "label": f"{(r.get('first_name') or '').strip()} {(r.get('last_name') or '').strip()}".strip(),
            "entity_type": "player",
            "sport": sport,
            "team_abbr": r.get("team_abbr"),
        } for r in rows]
    else:
        rows = await apisports_service.search_teams(q, sport)
        results = [{
            "id": r.get("id"),
            "label": r.get("name") or r.get("abbreviation") or str(r.get("id")),
            "entity_type": "team",
            "sport": sport,
            "team_abbr": r.get("abbreviation"),
        } for r in rows]
    return {"query": q, "entity_type": entity, "sport": sport, "results": results[:limit]}

@router.get("/{sport}/teams/{team_id}/mentions")
async def sport_team_mentions(sport: str, team_id: str):
    mentions = await get_entity_mentions("team", team_id, sport)
    return {"team_id": team_id, "sport": sport.upper(), "mentions": mentions}
