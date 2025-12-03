"""Sport metadata and search endpoints."""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query

from app.database.json_db import search_players as local_search_players, search_teams as local_search_teams
from app.services.apisports import apisports_service

router = APIRouter(tags=["sports"])
logger = logging.getLogger(__name__)


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
    results = []
    try:
        if et == "player":
            rows = await apisports_service.search_players(query, s)
            results = [
                {
                    "entity_type": "player",
                    "id": str(r.get("id")),
                    "name": f"{(r.get('first_name') or '').strip()} {(r.get('last_name') or '').strip()}".strip()
                    or "Unknown",
                    "sport": s,
                    "additional_info": {"source": "api-sports", "team_abbr": r.get("team_abbr")},
                }
                for r in rows
            ]
        else:
            rows = await apisports_service.search_teams(query, s)
            results = [
                {
                    "entity_type": "team",
                    "id": str(r.get("id")),
                    "name": r.get("name") or r.get("abbreviation") or "Unknown",
                    "sport": s,
                    "additional_info": {"source": "api-sports", "abbr": r.get("abbreviation")},
                }
                for r in rows
            ]
    except Exception:
        if et == "player":
            rows = local_search_players(s, query, limit=15)
            results = [
                {
                    "entity_type": "player",
                    "id": str(r.get("id")),
                    "name": r.get("name") or "Unknown",
                    "sport": s,
                    "additional_info": {"source": "local"},
                }
                for r in rows
            ]
        else:
            rows = local_search_teams(s, query, limit=15)
            results = [
                {
                    "entity_type": "team",
                    "id": str(r.get("id")),
                    "name": r.get("name") or r.get("abbreviation") or "Unknown",
                    "sport": s,
                    "additional_info": {"source": "local"},
                }
                for r in rows
            ]
    return {"query": query, "entity_type": et, "sport": s, "results": results}
