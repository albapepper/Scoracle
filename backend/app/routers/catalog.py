"""Local dataset and bootstrap endpoints."""
from __future__ import annotations

import hashlib
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import JSONResponse, Response

from app.database.local_dbs import (
    _db_path_for_sport,
    _first_last_only,
    _strip_specials_preserve_case,
    get_player_by_id as local_get_player_by_id,
    get_team_by_id as local_get_team_by_id,
    list_all_players,
    list_all_teams,
    get_all_players_with_details,
    get_all_teams_with_details,
    local_search_players,
    local_search_teams,
)


def hash_bootstrap_payload(data: Dict[str, Any]) -> str:
    """Compute ETag hash for bootstrap payload."""
    try:
        content = json.dumps(data, sort_keys=True, separators=(",", ":"), default=str)
        return hashlib.md5(content.encode()).hexdigest()[:16]
    except Exception:
        return ""

router = APIRouter(prefix="/{sport}", tags=["catalog"])
logger = logging.getLogger(__name__)


@router.get("/entities")
async def entities_dump(sport: str, entity_type: str = Query("player")):
    s = sport.upper()
    et = (entity_type or "player").lower()
    if et == "player":
        try:
            items = [{"id": str(pid), "name": name} for (pid, name) in list_all_players(s)]
        except Exception:
            items = local_search_players(s, " ", limit=1_000_000)
    elif et == "team":
        try:
            items = [{"id": str(tid), "name": name} for (tid, name) in list_all_teams(s)]
        except Exception:
            items = local_search_teams(s, " ", limit=1_000_000)
    else:
        raise HTTPException(status_code=400, detail="entity_type must be 'player' or 'team'")
    return {"sport": s, "entity_type": et, "count": len(items), "items": items}


@router.get("/sync/players")
async def sync_players(sport: str):
    s = sport.upper()
    try:
        # Use batch query to get all player details at once (avoids N+1 queries)
        players_with_details = get_all_players_with_details(s)
        items = []
        for player in players_with_details:
            name = player.get("name") or ""
            cleaned_name = _strip_specials_preserve_case(name)
            cleaned_name = _first_last_only(cleaned_name)
            parts = cleaned_name.split()
            first_name = parts[0] if parts else ""
            last_name = " ".join(parts[1:]) if len(parts) > 1 else ""
            current_team = player.get("current_team")
            if current_team:
                current_team = _strip_specials_preserve_case(current_team)
            items.append(
                {
                    "id": int(player.get("id")),
                    "firstName": first_name,
                    "lastName": last_name,
                    "currentTeam": current_team,
                }
            )
        return {
            "sport": s,
            "items": items,
            "count": len(items),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to sync players: {str(e)}")


@router.get("/sync/teams")
async def sync_teams(sport: str):
    s = sport.upper()
    try:
        # Use batch query to get all team details at once (avoids N+1 queries)
        teams_with_details = get_all_teams_with_details(s)
        items = []
        for team in teams_with_details:
            name = team.get("name") or ""
            cleaned_name = _strip_specials_preserve_case(name)
            team_data = {"id": int(team.get("id")), "name": cleaned_name}
            if team.get("current_league"):
                team_data["league"] = team.get("current_league")
            items.append(team_data)
        return {
            "sport": s,
            "items": items,
            "count": len(items),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to sync teams: {str(e)}")


@router.get("/bootstrap")
async def bootstrap(sport: str, request: Request, since: str | None = Query(None)):
    s = sport.upper()
    db_path = _db_path_for_sport(s)
    db_exists = os.path.exists(db_path)
    logger.info("[bootstrap] sport=%s db_path=%s exists=%s", s, db_path, db_exists)
    try:
        # Use batch queries to get all data at once (avoids N+1 queries)
        players_with_details = get_all_players_with_details(s)
        teams_with_details = get_all_teams_with_details(s)
    except Exception as e:
        logger.exception("[bootstrap] Failed to read local DB for sport=%s db_path=%s", s, db_path)
        return JSONResponse(
            status_code=500,
            content={
                "error": "Failed to read local DB",
                "sport": s,
                "db_path": db_path,
                "exists": db_exists,
                "detail": str(e),
            },
        )

    players_items = []
    for player in players_with_details:
        name = player.get("name") or ""
        cleaned_name = _strip_specials_preserve_case(name)
        cleaned_name = _first_last_only(cleaned_name)
        parts = cleaned_name.split()
        first_name = parts[0] if parts else ""
        last_name = " ".join(parts[1:]) if len(parts) > 1 else ""
        current_team = player.get("current_team")
        if current_team:
            current_team = _strip_specials_preserve_case(current_team)
        players_items.append(
            {
                "id": int(player.get("id")),
                "firstName": first_name,
                "lastName": last_name,
                "currentTeam": current_team,
            }
        )

    teams_items = []
    for team in teams_with_details:
        name = team.get("name") or ""
        cleaned_name = _strip_specials_preserve_case(name)
        team_data = {"id": int(team.get("id")), "name": cleaned_name}
        if team.get("current_league"):
            team_data["league"] = team.get("current_league")
        teams_items.append(team_data)

    generated_at = datetime.now(timezone.utc).isoformat()
    dataset_version = f"{s.lower()}-{len(players_items)}p-{len(teams_items)}t-{generated_at[:10]}"
    payload = {
        "sport": s,
        "datasetVersion": dataset_version,
        "generatedAt": generated_at,
        "players": {"count": len(players_items), "items": players_items},
        "teams": {"count": len(teams_items), "items": teams_items},
    }
    etag = hash_bootstrap_payload({"v": 1, "sport": s, "pc": len(players_items), "tc": len(teams_items)})
    inm = request.headers.get("if-none-match")
    headers = {"ETag": etag, "Cache-Control": "public, max-age=300, stale-while-revalidate=600"}
    if (inm and inm == etag) or (since and since == dataset_version):
        return Response(status_code=304, headers=headers)
    return JSONResponse(payload, headers=headers)
