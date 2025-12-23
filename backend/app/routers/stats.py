"""
Stats Router - Statistics endpoints for entity pages.

GET /api/v1/stats/{entity_type}/{entity_id}?sport=FOOTBALL|NBA|NFL[&season=2024]

Returns formatted statistics for StatsCard component.
Season defaults to most recent if not specified.
"""
import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Query, Response, Request, HTTPException

from app.services.stats_service import get_team_stats, get_player_stats
from app.utils.http_cache import build_cache_control, compute_etag, if_none_match_matches

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/stats", tags=["stats"])

# Cache policy for stats (shorter than profile widgets)
# - Browser: 30 min
# - CDN: 6 hours
# - SWR: 1 day (serve stale, refresh in background)
CACHE_CONTROL = build_cache_control(
    max_age=30 * 60,
    s_maxage=6 * 60 * 60,
    stale_while_revalidate=24 * 60 * 60,
    stale_if_error=24 * 60 * 60,
)


@router.get("/{entity_type}/{entity_id}")
async def get_stats(
    request: Request,
    response: Response,
    entity_type: str,
    entity_id: str,
    sport: str = Query(..., description="Sport: FOOTBALL, NBA, or NFL"),
    season: Optional[str] = Query(None, description="Season year (e.g., 2024). Defaults to most recent."),
    league_id: Optional[int] = Query(None, description="League ID (required for Football teams if not in DB)"),
) -> Optional[Dict[str, Any]]:
    """
    Fetch entity statistics from API-Sports.
    
    Returns formatted data for StatsCard table display:
    {
        "season": "2024",
        "stats": [
            {"label": "Goals Scored", "value": "45"},
            {"label": "Goals per Game", "value": "2.1"},
            ...
        ]
    }
    """
    entity_type_lower = entity_type.lower()
    sport_upper = sport.upper()

    if sport_upper not in ("FOOTBALL", "NBA", "NFL"):
        raise HTTPException(status_code=400, detail="sport must be FOOTBALL, NBA, or NFL")

    client = getattr(request.app.state, "http_client", None)
    
    if entity_type_lower == "team":
        data = await get_team_stats(
            entity_id, 
            sport_upper, 
            season=season, 
            league_id=league_id,
            client=client
        )
    elif entity_type_lower == "player":
        data = await get_player_stats(
            entity_id, 
            sport_upper, 
            season=season, 
            client=client
        )
    else:
        raise HTTPException(status_code=400, detail="entity_type must be 'team' or 'player'")
    
    if data is None:
        raise HTTPException(status_code=404, detail="Statistics not found")

    # ETag + conditional requests
    etag = compute_etag(data)
    if if_none_match_matches(request.headers.get("if-none-match"), etag):
        return Response(status_code=304, headers={"ETag": etag, "Cache-Control": CACHE_CONTROL})

    response.headers["ETag"] = etag
    response.headers["Cache-Control"] = CACHE_CONTROL
    return data
