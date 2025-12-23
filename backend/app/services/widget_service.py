"""
Widget Service - API-Sports data fetching and normalization.

Fetches data from sport-specific API-Sports endpoints and transforms
them into a unified format for the frontend.

Architecture:
1. Fetch raw data from API-Sports
2. Transform using sport-specific transformers
3. Cache normalized result
4. Return to frontend in consistent format
"""
import logging
from typing import Any, Dict, Optional

import httpx
from fastapi import HTTPException

from app.config import settings
from app.services.cache import widget_cache
from app.services.singleflight import singleflight
from app.services.widget_transformers import normalize_team_response, normalize_player_response

logger = logging.getLogger(__name__)

# Cache TTL: 30 days (profile data rarely changes)
WIDGET_CACHE_TTL = 30 * 24 * 60 * 60


def _get_headers() -> Dict[str, str]:
    """Get API-Sports authentication headers."""
    if not settings.API_SPORTS_KEY:
        raise HTTPException(status_code=502, detail="API-Sports key not configured on server")
    return {"x-apisports-key": settings.API_SPORTS_KEY}


def _get_base_url(sport: str) -> str:
    """Get base URL for sport-specific API-Sports endpoint."""
    sport_upper = sport.upper()
    if sport_upper == "FOOTBALL":
        return "https://v3.football.api-sports.io"
    elif sport_upper == "NBA":
        return "https://v2.nba.api-sports.io"
    elif sport_upper == "NFL":
        return "https://v1.american-football.api-sports.io"
    raise HTTPException(status_code=400, detail=f"Unknown sport: {sport}")


def _get_team_params(team_id: str, sport: str) -> Dict[str, Any]:
    """Build query parameters for team endpoint."""
    # All sports use simple id parameter for teams
    return {"id": team_id}


def _get_player_params(player_id: str, sport: str) -> Dict[str, Any]:
    """Build query parameters for player endpoint."""
    sport_upper = sport.upper()
    params = {"id": player_id}

    # FOOTBALL requires season parameter for player lookups
    if sport_upper == "FOOTBALL":
        params["season"] = settings.API_SPORTS_DEFAULTS.get("FOOTBALL", {}).get("season", "2025")

    return params


async def get_team(team_id: str, sport: str, *, client: httpx.AsyncClient | None = None) -> Optional[Dict[str, Any]]:
    """
    Fetch team data from API-Sports and normalize to unified format.

    Args:
        team_id: Team ID
        sport: Sport code (FOOTBALL, NBA, NFL)
        client: Optional HTTP client for connection reuse

    Returns:
        Normalized team data in format:
        {
            "team": { id, name, logo, country, code, ... },
            "venue": { name, city, capacity, ... }
        }
        Returns None if team not found.
    """
    sport_upper = sport.upper()
    cache_key = f"team:{sport_upper}:{team_id}"

    cached = widget_cache.get(cache_key)
    if cached is not None:
        logger.debug(f"Cache HIT: {cache_key}")
        return cached

    async def _work() -> Optional[Dict[str, Any]]:
        # Double-check cache after singleflight wait
        cached2 = widget_cache.get(cache_key)
        if cached2 is not None:
            return cached2

        # Fetch from API-Sports
        base = _get_base_url(sport_upper)
        headers = _get_headers()
        params = _get_team_params(team_id, sport_upper)

        if client is None:
            async with httpx.AsyncClient(timeout=15.0) as tmp:
                resp = await tmp.get(f"{base}/teams", headers=headers, params=params)
                resp.raise_for_status()
                data = resp.json()
        else:
            resp = await client.get(f"{base}/teams", headers=headers, params=params)
            resp.raise_for_status()
            data = resp.json()

        # Extract response
        response_list = data.get("response", [])
        if not response_list:
            logger.warning(f"Team not found: {team_id} ({sport_upper})")
            return None

        raw = response_list[0]

        # Normalize using sport-specific transformer
        normalized = normalize_team_response(sport_upper, raw)

        # Cache and return
        widget_cache.set(cache_key, normalized, ttl=WIDGET_CACHE_TTL)
        logger.info(f"Cache SET: {cache_key}")
        return normalized

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
    Fetch player data from API-Sports and normalize to unified format.

    Args:
        player_id: Player ID
        sport: Sport code (FOOTBALL, NBA, NFL)
        client: Optional HTTP client for connection reuse

    Returns:
        Normalized player data in format:
        {
            "player": { id, name, photo, position, age, ... },
            "statistics": [...]
        }
        Returns None if player not found.
    """
    sport_upper = sport.upper()
    cache_key = f"player:{sport_upper}:{player_id}"

    cached = widget_cache.get(cache_key)
    if cached is not None:
        logger.debug(f"Cache HIT: {cache_key}")
        return cached

    async def _work() -> Optional[Dict[str, Any]]:
        # Double-check cache after singleflight wait
        cached2 = widget_cache.get(cache_key)
        if cached2 is not None:
            return cached2

        # Fetch from API-Sports
        base = _get_base_url(sport_upper)
        headers = _get_headers()
        params = _get_player_params(player_id, sport_upper)

        if client is None:
            async with httpx.AsyncClient(timeout=15.0) as tmp:
                resp = await tmp.get(f"{base}/players", headers=headers, params=params)
                resp.raise_for_status()
                data = resp.json()
        else:
            resp = await client.get(f"{base}/players", headers=headers, params=params)
            resp.raise_for_status()
            data = resp.json()

        # Extract response
        response_list = data.get("response", [])
        if not response_list:
            logger.warning(f"Player not found: {player_id} ({sport_upper})")
            return None

        raw = response_list[0]

        # Normalize using sport-specific transformer
        normalized = normalize_player_response(sport_upper, raw)

        # Cache and return
        widget_cache.set(cache_key, normalized, ttl=WIDGET_CACHE_TTL)
        logger.info(f"Cache SET: {cache_key}")
        return normalized

    try:
        return await singleflight.do(cache_key, _work)

    except httpx.HTTPStatusError as e:
        status = e.response.status_code if e.response is not None else None
        logger.error(f"Failed to fetch player {player_id} ({sport_upper}) status={status}")
        raise HTTPException(status_code=502, detail="API-Sports upstream error")
    except httpx.HTTPError as e:
        logger.error(f"Failed to fetch player {player_id} ({sport_upper}) network error: {e}")
        raise HTTPException(status_code=502, detail="API-Sports network error")
