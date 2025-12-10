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
        players_raw = list_all_players(s)
        items = []
        for pid, name in players_raw:
            cleaned_name = _strip_specials_preserve_case(name or "")
            cleaned_name = _first_last_only(cleaned_name)
            parts = cleaned_name.split()
            first_name = parts[0] if parts else ""
            last_name = " ".join(parts[1:]) if len(parts) > 1 else ""
            player_record = local_get_player_by_id(s, int(pid))
            current_team = player_record.get("current_team") if player_record else None
            if current_team:
                current_team = _strip_specials_preserve_case(current_team)
            items.append(
                {
                    "id": int(pid),
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
        teams_raw = list_all_teams(s)
        items = []
        for tid, name in teams_raw:
            cleaned_name = _strip_specials_preserve_case(name or "")
            team_data = {"id": int(tid), "name": cleaned_name}
            try:
                team_row = local_get_team_by_id(s, int(tid))
                if team_row and team_row.get("current_league"):
                    team_data["league"] = team_row.get("current_league")
            except Exception:
                pass
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
        players_raw = list_all_players(s)
        teams_raw = list_all_teams(s)
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
    for pid, name in players_raw:
        cleaned_name = _strip_specials_preserve_case(name or "")
        cleaned_name = _first_last_only(cleaned_name)
        parts = cleaned_name.split()
        first_name = parts[0] if parts else ""
        last_name = " ".join(parts[1:]) if len(parts) > 1 else ""
        try:
            row = local_get_player_by_id(s, int(pid))
            current_team = row.get("current_team") if row else None
            if current_team:
                current_team = _strip_specials_preserve_case(current_team)
        except Exception:
            current_team = None
        players_items.append(
            {
                "id": int(pid),
                "firstName": first_name,
                "lastName": last_name,
                "currentTeam": current_team,
            }
        )

    teams_items = []
    for tid, name in teams_raw:
        cleaned_name = _strip_specials_preserve_case(name or "")
        team_data = {"id": int(tid), "name": cleaned_name}
        try:
            team_row = local_get_team_by_id(s, int(tid))
            if team_row and team_row.get("current_league"):
                team_data["league"] = team_row.get("current_league")
        except Exception:
            pass
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
