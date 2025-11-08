from typing import Optional, Dict, Any
from fastapi import HTTPException

from app.services.apisports import apisports_service
from app.database.local_dbs import get_player_by_id as local_get_player_by_id
from app.config import settings


async def build_player_widget_payload(sport: str, player_id: str, season: Optional[str]) -> Dict[str, Any]:
    """Construct a normalized player widget payload for the requested sport.

    This function encapsulates sport-specific branching so routers remain sport-agnostic.
    """
    s = (sport or "").upper()
    season_norm = season if (season and str(season).lower() != "current") else None

    if settings.LEAN_BACKEND:
        # Minimal local DB-only path
        row = local_get_player_by_id(s, int(player_id))
        if not row:
            raise HTTPException(status_code=404, detail="Player not found")
        name = row.get("name") or ""
        parts = name.split(" ")
        payload = {
            "id": int(player_id),
            "name": name.strip(),
            "firstName": parts[0] if parts else None,
            "lastName": " ".join(parts[1:]) if len(parts) > 1 else None,
            "position": None,
            "team": {"id": None, "name": row.get("current_team"), "abbreviation": row.get("current_team")},
            "season": season_norm,
            "statistics": {},
        }
        return payload

    if s == 'NBA':
        basic = await apisports_service.get_basketball_player_basic(player_id, season=None)
        stats = await apisports_service.get_basketball_player_statistics(player_id, season_norm)
        payload = {
            "id": basic.get("id"),
            "name": f"{basic.get('first_name') or ''} {basic.get('last_name') or ''}".strip(),
            "firstName": basic.get("first_name"),
            "lastName": basic.get("last_name"),
            "position": basic.get("position"),
            "team": basic.get("team"),
            "season": season_norm,
            "statistics": stats or {},
        }
        return payload

    # Other sports to be implemented incrementally here
    raise HTTPException(status_code=501, detail=f"Player widget payload not implemented for sport {s}")
