"""
Widget Router - Direct proxy to API-Sports.

GET /api/v1/widget/{type}/{id}?sport=FOOTBALL|NBA|NFL

Returns EXACTLY what API-Sports returns. No wrapping, no transformation.
"""
import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Query, Response, Request, HTTPException

from app.services.widget_service import get_team, get_player
from app.utils.http_cache import build_cache_control, compute_etag, if_none_match_matches

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/widget", tags=["widgets"])

# Cache policy (snappy widgets)
# - Browser: 1h
# - CDN: 30d
# - SWR: 7d (serve instantly, refresh in background)
CACHE_CONTROL = build_cache_control(
    max_age=60 * 60,
    s_maxage=30 * 24 * 60 * 60,
    stale_while_revalidate=7 * 24 * 60 * 60,
    stale_if_error=7 * 24 * 60 * 60,
)


@router.get("/{entity_type}/{entity_id}")
async def get_widget(
    request: Request,
    response: Response,
    entity_type: str,
    entity_id: str,
    sport: str = Query(..., description="Sport: FOOTBALL, NBA, or NFL"),
) -> Optional[Dict[str, Any]]:
    """
    Fetch entity data from API-Sports.
    
    Returns the raw API response - no transformation.
    """
    entity_type_lower = entity_type.lower()
    sport_upper = sport.upper()

    if sport_upper not in ("FOOTBALL", "NBA", "NFL"):
        raise HTTPException(status_code=400, detail="sport must be FOOTBALL, NBA, or NFL")

    client = getattr(request.app.state, "http_client", None)
    
    if entity_type_lower == "team":
        data = await get_team(entity_id, sport_upper, client=client)
    elif entity_type_lower == "player":
        data = await get_player(entity_id, sport_upper, client=client)
    else:
        raise HTTPException(status_code=400, detail="entity_type must be 'team' or 'player'")
    
    if data is None:
        raise HTTPException(status_code=404, detail="Entity not found")

    # ETag + conditional requests
    etag = compute_etag(data)
    if if_none_match_matches(request.headers.get("if-none-match"), etag):
        return Response(status_code=304, headers={"ETag": etag, "Cache-Control": CACHE_CONTROL})

    response.headers["ETag"] = etag
    response.headers["Cache-Control"] = CACHE_CONTROL
    return data
