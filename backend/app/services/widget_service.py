"""
Widget Service - Direct API-Sports proxy with caching.

Returns EXACTLY what API-Sports returns. No transformation.
Cache for 30 days (profile data rarely changes).
"""
import logging
from typing import Any, Dict, Optional

import httpx
from fastapi import HTTPException

from app.config import settings
from app.services.cache import widget_cache
from app.services.singleflight import singleflight

logger = logging.getLogger(__name__)

# Cache TTL: 30 days
WIDGET_CACHE_TTL = 30 * 24 * 60 * 60


def _get_headers() -> Dict[str, str]:
    """Get API-Sports headers."""
    if not settings.API_SPORTS_KEY:
        raise HTTPException(status_code=502, detail="API-Sports key not configured on server")
    return {"x-apisports-key": settings.API_SPORTS_KEY}


def _get_base_url(sport: str) -> str:
    """Get base URL for sport."""
    sport_upper = sport.upper()
    if sport_upper == "FOOTBALL":
        return "https://v3.football.api-sports.io"
    elif sport_upper == "NBA":
        return "https://v2.nba.api-sports.io"
    elif sport_upper == "NFL":
        return "https://v1.american-football.api-sports.io"
    raise HTTPException(status_code=400, detail=f"Unknown sport: {sport}")


async def get_team(team_id: str, sport: str, *, client: httpx.AsyncClient | None = None) -> Optional[Dict[str, Any]]:
    """
    GET /teams?id={team_id}
    
    Returns the FIRST item from response[] exactly as API-Sports returns it.
    Returns None if not found.
    """
    sport_upper = sport.upper()
    cache_key = f"team:{sport_upper}:{team_id}"
    
    cached = widget_cache.get(cache_key)
    if cached is not None:
        logger.debug(f"Cache HIT: {cache_key}")
        return cached

    async def _work() -> Optional[Dict[str, Any]]:
        cached2 = widget_cache.get(cache_key)
        if cached2 is not None:
            return cached2

        base = _get_base_url(sport_upper)
        headers = _get_headers()
        if client is None:
            async with httpx.AsyncClient(timeout=15.0) as tmp:
                resp = await tmp.get(f"{base}/teams", headers=headers, params={"id": team_id})
                resp.raise_for_status()
                data = resp.json()
        else:
            resp = await client.get(f"{base}/teams", headers=headers, params={"id": team_id})
            resp.raise_for_status()
            data = resp.json()

        response_list = data.get("response", [])
        if not response_list:
            logger.warning(f"Team not found: {team_id} ({sport_upper})")
            return None

        # Return exactly what API returns
        result = response_list[0]
        widget_cache.set(cache_key, result, ttl=WIDGET_CACHE_TTL)
        logger.info(f"Cache SET: {cache_key}")
        return result

    try:
        return await singleflight.do(cache_key, _work)

    except httpx.HTTPStatusError as e:
        status = e.response.status_code if e.response is not None else None
        logger.error(f"Failed to fetch team {team_id} ({sport_upper}) status={status}")
        raise HTTPException(status_code=502, detail="API-Sports upstream error")
    except httpx.HTTPError as e:
        logger.error(f"Failed to fetch team {team_id} ({sport_upper}) network error: {e}")
        raise HTTPException(status_code=502, detail="API-Sports network error")


async def get_player(player_id: str, sport: str, *, client: httpx.AsyncClient | None = None) -> Optional[Dict[str, Any]]:
    """
    GET /players?id={player_id}
    
    Returns the FIRST item from response[] exactly as API-Sports returns it.
    Returns None if not found.
    """
    sport_upper = sport.upper()
    cache_key = f"player:{sport_upper}:{player_id}"
    
    cached = widget_cache.get(cache_key)
    if cached is not None:
        logger.debug(f"Cache HIT: {cache_key}")
        return cached

    async def _work() -> Optional[Dict[str, Any]]:
        cached2 = widget_cache.get(cache_key)
        if cached2 is not None:
            return cached2

        base = _get_base_url(sport_upper)
        headers = _get_headers()
        params = {"id": player_id}
        # Football requires season
        if sport_upper == "FOOTBALL":
            params["season"] = settings.API_SPORTS_DEFAULTS.get("FOOTBALL", {}).get("season", "2024")

        if client is None:
            async with httpx.AsyncClient(timeout=15.0) as tmp:
                resp = await tmp.get(f"{base}/players", headers=headers, params=params)
                resp.raise_for_status()
                data = resp.json()
        else:
            resp = await client.get(f"{base}/players", headers=headers, params=params)
            resp.raise_for_status()
            data = resp.json()

        response_list = data.get("response", [])
        if not response_list:
            logger.warning(f"Player not found: {player_id} ({sport_upper})")
            return None

        # Return exactly what API returns
        result = response_list[0]
        widget_cache.set(cache_key, result, ttl=WIDGET_CACHE_TTL)
        logger.info(f"Cache SET: {cache_key}")
        return result

    try:
        return await singleflight.do(cache_key, _work)

    except httpx.HTTPStatusError as e:
        status = e.response.status_code if e.response is not None else None
        logger.error(f"Failed to fetch player {player_id} ({sport_upper}) status={status}")
        raise HTTPException(status_code=502, detail="API-Sports upstream error")
    except httpx.HTTPError as e:
        logger.error(f"Failed to fetch player {player_id} ({sport_upper}) network error: {e}")
        raise HTTPException(status_code=502, detail="API-Sports network error")

