"""
Co-mentions Router - API endpoint for finding co-mentioned entities.

GET /api/v1/co-mentions/{entity_type}/{entity_id}?sport=FOOTBALL&hours=48

Returns entities from the same sport's database that appear alongside
the searched entity in recent news articles, sorted by mention frequency.
"""
import logging
from typing import Any, Dict

from fastapi import APIRouter, Query, Response, Request, HTTPException

from app.services import co_mentions_service
from app.utils.http_cache import build_cache_control, compute_etag, if_none_match_matches

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/co-mentions", tags=["co-mentions"])

# Cache policy (same as news - snappy updates)
CO_MENTIONS_CACHE_CONTROL = build_cache_control(
    max_age=60,
    s_maxage=10 * 60,  # 10 minutes
    stale_while_revalidate=60 * 60,
    stale_if_error=60 * 60,
)


@router.get("/{entity_type}/{entity_id}")
async def get_co_mentions(
    request: Request,
    response: Response,
    entity_type: str,
    entity_id: int,
    sport: str = Query(..., description="Sport code: FOOTBALL, NBA, or NFL"),
    hours: int = Query(48, description="Hours to look back for news"),
) -> Dict[str, Any]:
    """
    Get entities co-mentioned with the given entity in recent news articles.

    - Fetches news articles for the entity
    - Cross-references with all entities in the sport's database
    - Returns matches sorted by mention frequency

    Args:
        entity_type: "player" or "team"
        entity_id: The entity's database ID
        sport: Sport code (FOOTBALL, NBA, NFL)
        hours: Hours to look back for news (default 48)

    Returns:
        List of co-mentioned entities with frequency counts
    """
    # Validate entity_type
    if entity_type not in ("player", "team"):
        raise HTTPException(status_code=400, detail="entity_type must be 'player' or 'team'")

    # Validate sport
    sport_upper = sport.upper()
    if sport_upper not in ("FOOTBALL", "NBA", "NFL"):
        raise HTTPException(status_code=400, detail="sport must be FOOTBALL, NBA, or NFL")

    # Get HTTP client from app state
    client = getattr(request.app.state, "http_client", None)
    if client is None:
        raise HTTPException(status_code=500, detail="HTTP client not initialized")

    # Fetch co-mentions
    co_mentions = await co_mentions_service.get_co_mentions(
        client=client,
        entity_type=entity_type,
        entity_id=entity_id,
        sport=sport_upper,
        hours=hours,
    )

    payload = {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "sport": sport_upper,
        "hours": hours,
        "count": len(co_mentions),
        "co_mentions": co_mentions,
    }

    # ETag for conditional requests
    etag = compute_etag(payload)
    if if_none_match_matches(request.headers.get("if-none-match"), etag):
        return Response(status_code=304, headers={"ETag": etag, "Cache-Control": CO_MENTIONS_CACHE_CONTROL})

    response.headers["ETag"] = etag
    response.headers["Cache-Control"] = CO_MENTIONS_CACHE_CONTROL
    return payload
