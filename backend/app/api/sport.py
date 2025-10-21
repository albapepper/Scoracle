from fastapi import APIRouter, Path, Query, HTTPException
import time
from app.models.schemas import PlayerFullResponse, TeamFullResponse
from app.routers import player as player_router_mod
from app.routers import team as team_router_mod
from app.routers import autocomplete as autocomplete_router_mod
from app.adapters.google_rss import get_entity_mentions, get_entity_mentions_with_debug
from app.db.local_dbs import get_player_by_id as local_get_player_by_id, get_team_by_id as local_get_team_by_id, search_players as local_search_players, search_teams as local_search_teams
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
    elif s == 'NFL':
        try:
            info = await apisports_service.get_nfl_player_basic(player_id)
        except Exception:
            row = get_player_by_id(s, int(player_id))
            if not row:
                raise HTTPException(status_code=404, detail="Player not found")
            name = row.get("name") or ""
            parts = name.split(" ")
            info = {
                "id": row["id"],
                "first_name": parts[0] if parts else None,
                "last_name": " ".join(parts[1:]) if len(parts) > 1 else None,
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
    s = sport.upper()
    md = await get_entity_mentions_with_debug("player", player_id, s)
    mentions = md.get("mentions", [])
    # Enrich with entity_info for widgets
    entity_info = None
    try:
        if s == 'NBA':
            entity_info = await apisports_service.get_basketball_player_basic(player_id)
        elif s in ('EPL', 'FOOTBALL'):
            entity_info = await apisports_service.get_football_player_basic(player_id)
        elif s == 'NFL':
            entity_info = await apisports_service.get_nfl_player_basic(player_id)
    except Exception:
        entity_info = None
    if not isinstance(entity_info, dict):
        # Fallback to local DB for name
        row = local_get_player_by_id(s, int(player_id))
        if row:
            entity_info = {
                "id": int(player_id),
                "first_name": (row.get("name") or "").split(" ")[0] or None,
                "last_name": " ".join((row.get("name") or "").split(" ")[1:]) or None,
                "position": None,
                "team": {"id": None, "name": row.get("current_team"), "abbreviation": row.get("current_team")},
            }
    # Build alongside entities: scan titles/descriptions for local-db entities
    alongside = _summarize_comentions_for_mentions(s, mentions, target_entity=("player", str(player_id)))
    # Sort mentions by recency just in case
    try:
        mentions_sorted = sorted(mentions, key=lambda m: (m.get("pub_ts") or 0), reverse=True)
    except Exception:
        mentions_sorted = mentions
    return {"player_id": player_id, "sport": s, "entity_info": entity_info, "mentions": mentions_sorted, "alongside_entities": alongside, "_debug": md.get("debug", {}), "_echo": {"player_id": player_id}}

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
    elif s == 'NFL':
        try:
            info = await apisports_service.get_nfl_team_basic(team_id)
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
    return {"query": q, "entity_type": entity, "sport": sport, "results": results[:limit], "_elapsed_ms": int((time.perf_counter()-_t0)*1000), "_provider": "local-sqlite"}

@router.get("/{sport}/teams/{team_id}/mentions")
async def sport_team_mentions(sport: str, team_id: str):
    s = sport.upper()
    md = await get_entity_mentions_with_debug("team", team_id, s)
    mentions = md.get("mentions", [])
    entity_info = None
    try:
        if s == 'NBA':
            entity_info = await apisports_service.get_basketball_team_basic(team_id)
        elif s in ('EPL', 'FOOTBALL'):
            entity_info = await apisports_service.get_football_team_basic(team_id)
        elif s == 'NFL':
            entity_info = await apisports_service.get_nfl_team_basic(team_id)
    except Exception:
        entity_info = None
    if not isinstance(entity_info, dict):
        row = local_get_team_by_id(s, int(team_id))
        if row:
            entity_info = {
                "id": int(team_id),
                "name": row.get("name"),
                "abbreviation": row.get("name"),
                "city": None,
                "conference": None,
                "division": None,
            }
    alongside = _summarize_comentions_for_mentions(s, mentions, target_entity=("team", str(team_id)))
    try:
        mentions_sorted = sorted(mentions, key=lambda m: (m.get("pub_ts") or 0), reverse=True)
    except Exception:
        mentions_sorted = mentions
    return {"team_id": team_id, "sport": s, "entity_info": entity_info, "mentions": mentions_sorted, "alongside_entities": alongside, "_debug": md.get("debug", {}), "_echo": {"team_id": team_id}}


def _summarize_comentions_for_mentions(sport: str, mentions: list[dict], target_entity: tuple[str, str]) -> list[dict]:
    """Extract other local entities mentioned across the RSS items and return counts.

    Searches both players and teams for the sport using simple phrase extraction from titles and descriptions.
    """
    te_type, te_id = target_entity
    counts: dict[tuple[str, str], dict] = {}
    # Helper to accumulate
    def add_hit(e_type: str, e_id: str, name: str):
        key = (e_type, e_id)
        if key == (te_type, te_id):
            return
        entry = counts.get(key)
        if not entry:
            entry = {"entity_type": e_type, "id": e_id, "name": name, "hits": 0}
            counts[key] = entry
        entry["hits"] += 1

    # Extract candidate phrases (bigrams/trigrams) and query local db
    def extract_phrases(text: str) -> list[str]:
        import re
        # Keep words; allow hyphens and apostrophes within words
        words = re.findall(r"[A-Za-z][A-Za-z\-'\.]+", text or "")
        phrases = []
        n = len(words)
        for size in (3, 2):  # trigrams then bigrams
            for i in range(n - size + 1):
                phrase = " ".join(words[i:i+size]).strip()
                if len(phrase) >= 4:
                    phrases.append(phrase)
        # Also include single long tokens (>=5 chars)
        for w in words:
            if len(w) >= 5:
                phrases.append(w)
        # Deduplicate while preserving order
        seen = set()
        uniq = []
        for p in phrases:
            pl = p.lower()
            if pl in seen:
                continue
            seen.add(pl)
            uniq.append(p)
        return uniq[:10]  # budget

    for item in mentions:
        text = f"{item.get('title') or ''}. {item.get('description') or ''}"
        for phrase in extract_phrases(text):
            # Try players then teams; small limits
            try:
                for r in local_search_players(sport, phrase, limit=2):
                    add_hit("player", str(r.get("id")), r.get("name") or "")
                for r in local_search_teams(sport, phrase, limit=2):
                    add_hit("team", str(r.get("id")), r.get("name") or "")
            except Exception:
                continue
    out = list(counts.values())
    out.sort(key=lambda x: x["hits"], reverse=True)
    return out[:20]


@router.get("/{sport}/teams/{team_id}/roster")
async def sport_team_roster_stub(sport: str, team_id: str, season: str | None = Query(None)):
    return {"team_id": team_id, "sport": sport.upper(), "season": season or "current", "roster": []}

@router.get("/{sport}/players/{player_id}/seasons")
async def sport_player_seasons(sport: str, player_id: str):
    """Temporary seasons endpoint to avoid 404s; returns a reasonable default current season per sport."""
    s = sport.upper()
    from app.core.config import settings
    defaults = settings.API_SPORTS_DEFAULTS.get(s, {})
    season = defaults.get("season") or "current"
    return {"player_id": player_id, "sport": s, "seasons": [str(season)]}
