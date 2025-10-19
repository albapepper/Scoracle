from fastapi import APIRouter, Path, Query, HTTPException
import time
from app.models.schemas import PlayerFullResponse, TeamFullResponse
from app.routers import player as player_router_mod
from app.routers import team as team_router_mod
from app.routers import autocomplete as autocomplete_router_mod
from app.adapters.google_rss import get_entity_mentions
from app.services.apisports import apisports_service
from app.db.local_dbs import suggestions_from_local_or_upstream, get_player_by_id, get_team_by_id

router = APIRouter()

@router.get("/{sport}/players/{player_id}")
async def sport_player_summary(sport: str, player_id: str):
    s = sport.upper()
    if s == 'NBA':
        info = await apisports_service.get_basketball_player_basic(player_id)
    elif s in ('EPL', 'FOOTBALL'):
        # Try provider first; if API key is missing or call fails, fall back to local DB
        try:
            info = await apisports_service.get_football_player_basic(player_id)
        except Exception:
            row = get_player_by_id(s, int(player_id))
            if not row:
                raise HTTPException(status_code=404, detail="Player not found")
            # Map to a minimal summary compatible with clients
            info = {
                "id": row["id"],
                "first_name": (row["name"] or "").split(" ")[0] if row.get("name") else None,
                "last_name": " ".join((row.get("name") or "").split(" ")[1:]) or None,
                "position": None,
                "team": {"id": None, "name": row.get("current_team"), "abbreviation": row.get("current_team")},
            }
    else:
        raise HTTPException(status_code=501, detail=f"Player summary not implemented for sport {s}")
    return {"summary": info, "sport": s, "id": player_id}

@router.get("/{sport}")
async def sport_home(sport: str):
    s = sport.upper()
    return {"sport": s, "available_sports": ["NBA", "NFL", "FOOTBALL"], "version": "0.1.0"}

@router.get("/{sport}/search")
async def sport_search(sport: str, query: str = Query(...), entity_type: str = Query("player")):
    s = sport.upper()
    et = (entity_type or "player").lower()
    if et not in {"player", "team"}:
        raise HTTPException(status_code=400, detail="entity_type must be 'player' or 'team'")
    if len((query or "").strip()) < 2:
        return {"query": query, "entity_type": et, "sport": s, "results": []}
    if et == "player":
        rows = await apisports_service.search_players(query, s)
        results = [{
            "entity_type": "player",
            "id": str(r.get("id")),
            "name": f"{(r.get('first_name') or '').strip()} {(r.get('last_name') or '').strip()}".strip() or "Unknown",
            "sport": s,
            "additional_info": {"source": "api-sports", "team_abbr": r.get("team_abbr")}
        } for r in rows]
    else:
        rows = await apisports_service.search_teams(query, s)
        results = [{
            "entity_type": "team",
            "id": str(r.get("id")),
            "name": r.get("name") or r.get("abbreviation") or "Unknown",
            "sport": s,
            "additional_info": {"source": "api-sports", "abbr": r.get("abbreviation")}
        } for r in rows]
    return {"query": query, "entity_type": et, "sport": s, "results": results}

@router.get("/{sport}/players/{player_id}/stats")
async def sport_player_stats(sport: str, player_id: str, season: str | None = Query(None)):
    s = sport.upper()
    if s == 'NBA':
        stats = await apisports_service.get_basketball_player_statistics(player_id, season)
    else:
        raise HTTPException(status_code=501, detail=f"Player stats not implemented for sport {s}")
    return {"player_id": player_id, "sport": s, "season": season or "current", "stats": stats}

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
    s = sport.upper()
    if s == 'NBA':
        info = await apisports_service.get_basketball_team_basic(team_id)
    elif s in ('EPL', 'FOOTBALL'):
        try:
            info = await apisports_service.get_football_team_basic(team_id)
        except Exception:
            row = get_team_by_id(s, int(team_id))
            if not row:
                raise HTTPException(status_code=404, detail="Team not found")
            info = {
                "id": row["id"],
                "name": row["name"],
                "abbreviation": row["name"],
                "city": None,
                "conference": None,
                "division": None,
            }
    else:
        raise HTTPException(status_code=501, detail=f"Team summary not implemented for sport {s}")
    return {"summary": info, "sport": s, "id": team_id}

@router.get("/{sport}/teams/{team_id}/stats")
async def sport_team_stats(sport: str, team_id: str, season: str | None = Query(None)):
    s = sport.upper()
    if s == 'NBA':
        stats = await apisports_service.get_basketball_team_statistics(team_id, season)
    else:
        raise HTTPException(status_code=501, detail=f"Team stats not implemented for sport {s}")
    return {"team_id": team_id, "sport": s, "season": season or "current", "stats": stats}

@router.get("/{sport}/teams/{team_id}/full", response_model=TeamFullResponse)
async def sport_team_full(sport: str, team_id: str, season: str | None = Query(None), include_mentions: bool = Query(True)):
    return await team_router_mod.get_team_full(team_id=team_id, season=season, include_mentions=include_mentions, sport=sport)

@router.get("/{sport}/autocomplete/{entity_type}")
async def sport_autocomplete_proxy(sport: str, entity_type: str, q: str = Query(...), limit: int = Query(8, ge=1, le=15)):
    _t0 = time.perf_counter()
    entity = (entity_type or "").strip().lower()
    if entity not in {"player", "team"}:
        raise HTTPException(status_code=400, detail="entity_type must be 'player' or 'team'")
    if len((q or "").strip()) < 2:
        return {"query": q, "entity_type": entity, "sport": sport, "results": [], "_elapsed_ms": int((time.perf_counter()-_t0)*1000)}
    results = await suggestions_from_local_or_upstream(entity, sport, q, limit)
    return {"query": q, "entity_type": entity, "sport": sport, "results": results[:limit], "_elapsed_ms": int((time.perf_counter()-_t0)*1000), "_provider": "local-sqlite+api-sports"}

@router.get("/{sport}/teams/{team_id}/mentions")
async def sport_team_mentions(sport: str, team_id: str):
    mentions = await get_entity_mentions("team", team_id, sport)
    return {"team_id": team_id, "sport": sport.upper(), "mentions": mentions}


@router.get("/{sport}/teams/{team_id}/roster")
async def sport_team_roster_stub(sport: str, team_id: str, season: str | None = Query(None)):
    return {"team_id": team_id, "sport": sport.upper(), "season": season or "current", "roster": []}
