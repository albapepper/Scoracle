import logging
import os
from typing import List, Dict, Any, Optional
import httpx
from fastapi import HTTPException

from app.config import settings
from app.services.cache import basic_cache, stats_cache

logger = logging.getLogger(__name__)


class ApiSportsService:
    """Thin client for API-Sports provider.

    Notes:
    - API-Sports has separate subdomains per sport.
      football (soccer): https://v3.football.api-sports.io
      basketball:        https://v2.nba.api-sports.io/
      american-football: https://v1.american-football.api-sports.io
    - Requires header: 'x-apisports-key: <KEY>'
    - League/season selection is required for many endpoints; we rely on settings.API_SPORTS_DEFAULTS.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.API_SPORTS_KEY
        if not self.api_key:
            logger.warning("API_SPORTS_KEY not set – API-Sports calls will fail until configured")

    def _base_url_for(self, sport_key: str) -> str:
        defaults = settings.API_SPORTS_DEFAULTS.get(sport_key.upper()) or {}
        sport = defaults.get("sport")
        if sport == "football":
            return "https://v3.football.api-sports.io"
        if sport == "basketball":
            return "https://v2.nba.api-sports.io"
        if sport == "american-football":
            return "https://v1.american-football.api-sports.io"
        raise ValueError(f"Unsupported API-Sports sport key: {sport_key}")

    def _headers_for_base(self, base_url: str) -> Dict[str, str]:
        """Build headers for API-Sports or RapidAPI access based on env.

        Environment:
        - API_SPORTS_MODE: 'direct' (default) or 'rapidapi'
        - API_SPORTS_KEY: used as key for selected mode
        - RAPIDAPI_KEY: optional separate key when API_SPORTS_MODE='rapidapi'
        """
        from urllib.parse import urlparse
        env_mode = os.getenv("API_SPORTS_MODE")
        # Auto-switch to rapidapi if RAPIDAPI_KEY is present and mode not explicitly set
        mode = (env_mode or ("rapidapi" if os.getenv("RAPIDAPI_KEY") else "direct")).lower()
        host = urlparse(base_url).netloc
        if mode == "rapidapi":
            rapid_key = os.getenv("RAPIDAPI_KEY", self.api_key)
            return {"x-rapidapi-key": rapid_key, "x-rapidapi-host": host}
        # default: direct header
        return {"x-apisports-key": self.api_key}

    async def search_players(self, q: str, sport_key: str, *, league_override: Optional[int] = None, season_override: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search players across supported sports.

        Returns a list of normalized dicts with minimal fields needed by autocomplete mapping stage.
        """
        # Cache frequent searches briefly to reduce upstream load
        cache_key = f"apisports:search_players:{sport_key}:{(season_override or '')}:{(league_override or '')}:{q.strip().lower()}"
        cached = basic_cache.get(cache_key)
        if cached is not None:
            return cached
        if not self.api_key:
            # Provide a clearer failure when key is missing
            raise HTTPException(status_code=502, detail="API-Sports key not configured on server")
        sport_key_up = sport_key.upper()
        base = self._base_url_for(sport_key_up)
        headers = self._headers_for_base(base)
        defaults = settings.API_SPORTS_DEFAULTS.get(sport_key_up, {})
        league = league_override if league_override is not None else defaults.get("league")
        season = (season_override if season_override is not None else defaults.get("season")) or None

        try:
            tmo = httpx.Timeout(connect=3.0, read=5.0, write=5.0, pool=3.0)
            async with httpx.AsyncClient(timeout=tmo) as client:
                if sport_key_up in ('EPL', 'FOOTBALL'):
                    # Football search: /players?league=39&search=...&season=YYYY
                    params = {"league": league}
                    if (q or "").strip():
                        params["search"] = q
                    if season:
                        params["season"] = season
                    r = await client.get(f"{base}/players", headers=headers, params=params)
                    r.raise_for_status()
                    payload = r.json()
                    response_list = payload.get("response", []) if isinstance(payload, dict) else []
                    out = []
                    for item in response_list:
                        player = item.get("player", {})
                        statistics = item.get("statistics", [])
                        team_abbr = None
                        if statistics and isinstance(statistics, list):
                            first_stat = statistics[0]
                            team = first_stat.get("team") or {}
                            team_abbr = team.get("name")  # EPL typically uses full name
                        out.append({
                            "id": player.get("id"),
                            "first_name": player.get("firstname"),
                            "last_name": player.get("lastname"),
                            "team_abbr": team_abbr,
                        })
                    basic_cache.set(cache_key, out, ttl=90)
                    return out
                elif sport_key_up == 'NBA':
                    # Basketball: /players?search=...
                    # Avoid applying league filter by default as it can reduce hits for some accounts
                    params = {"search": q}
                    if season:
                        params["season"] = season
                    try:
                        r = await client.get(f"{base}/players", headers=headers, params=params)
                        r.raise_for_status()
                    except httpx.HTTPStatusError as e:
                        # Retry with explicit league if available when 400/404 occurs
                        if e.response is not None and e.response.status_code in (400, 404) and league:
                            params_with_league = dict(params)
                            params_with_league["league"] = league
                            r = await client.get(f"{base}/players", headers=headers, params=params_with_league)
                            r.raise_for_status()
                        else:
                            raise
                    payload = r.json()
                    response_list = payload.get("response", [])
                    out = []
                    for p in response_list:
                        team_abbr = None
                        teams = p.get("teams") or []
                        if teams:
                            last_team = teams[-1]
                            team_abbr = (last_team.get("team") or {}).get("code") or (last_team.get("team") or {}).get("name")
                        out.append({
                            "id": p.get("id"),
                            "first_name": p.get("firstname") or p.get("firstName"),
                            "last_name": p.get("lastname") or p.get("lastName"),
                            "team_abbr": team_abbr,
                        })
                    basic_cache.set(cache_key, out, ttl=90)
                    return out
                elif sport_key_up == 'NFL':
                    # American football: limited coverage; attempt /players?search=...
                    params = {"search": q}
                    if league:
                        params["league"] = league
                    if season:
                        params["season"] = season
                    r = await client.get(f"{base}/players", headers=headers, params=params)
                    r.raise_for_status()
                    payload = r.json()
                    response_list = payload.get("response", [])
                    out = []
                    for p in response_list:
                        team_abbr = None
                        team = (p.get("team") or {})
                        team_abbr = team.get("name") or team.get("code")
                        name = (p.get("name") or "").split(" ")
                        first = name[0] if name else None
                        last = " ".join(name[1:]) if len(name) > 1 else None
                        out.append({
                            "id": p.get("id"),
                            "first_name": first,
                            "last_name": last,
                            "team_abbr": team_abbr,
                        })
                    basic_cache.set(cache_key, out, ttl=90)
                    return out
                else:
                    basic_cache.set(cache_key, [], ttl=60)
                    return []
        except httpx.HTTPStatusError as e:
            status = e.response.status_code if e.response is not None else None
            logger.error("API-Sports player search failed", extra={"sport": sport_key_up, "status": status})
            # Surface auth errors distinctly
            if status in (401, 403):
                raise HTTPException(status_code=502, detail="API-Sports authentication failed; check API key")
            raise HTTPException(status_code=502, detail="API-Sports player search error")
        except httpx.HTTPError as e:
            logger.error("API-Sports player search network error", extra={"sport": sport_key_up, "error": str(e)})
            raise HTTPException(status_code=502, detail="API-Sports network error")

    async def search_teams(self, q: str, sport_key: str, *, league_override: Optional[int] = None, season_override: Optional[str] = None) -> List[Dict[str, Any]]:
        cache_key = f"apisports:search_teams:{sport_key}:{(season_override or '')}:{(league_override or '')}:{q.strip().lower()}"
        cached = basic_cache.get(cache_key)
        if cached is not None:
            return cached
        if not self.api_key:
            raise HTTPException(status_code=502, detail="API-Sports key not configured on server")
        sport_key_up = sport_key.upper()
        base = self._base_url_for(sport_key_up)
        headers = self._headers_for_base(base)
        defaults = settings.API_SPORTS_DEFAULTS.get(sport_key_up, {})
        league = league_override if league_override is not None else defaults.get("league")
        season = (season_override if season_override is not None else defaults.get("season")) or None

        try:
            tmo = httpx.Timeout(connect=3.0, read=5.0, write=5.0, pool=3.0)
            async with httpx.AsyncClient(timeout=tmo) as client:
                if sport_key_up in ('EPL', 'FOOTBALL'):
                    # football: /teams?league=39&search=...
                    params = {"league": league}
                    if (q or "").strip():
                        params["search"] = q
                    try:
                        r = await client.get(f"{base}/teams", headers=headers, params=params)
                        r.raise_for_status()
                        payload = r.json()
                        response_list = payload.get("response", [])
                    except httpx.HTTPStatusError as e:
                        # Some combinations may error for certain accounts; fallback to search-only
                        if e.response is not None and e.response.status_code in (400, 404):
                            r = await client.get(f"{base}/teams", headers=headers, params={"search": q})
                            r.raise_for_status()
                            payload = r.json()
                            response_list = payload.get("response", [])
                        else:
                            raise
                    out = []
                    for t in response_list:
                        team = t.get("team") or {}
                        out.append({
                            "id": team.get("id"),
                            "name": team.get("name"),
                            "abbreviation": team.get("code") or team.get("name"),
                        })
                    basic_cache.set(cache_key, out, ttl=120)
                    return out
                elif sport_key_up == 'NBA':
                    params = {"search": q}
                    # NBA v2: avoid strict league filters in search; include season if provided
                    if season:
                        params["season"] = season
                    try:
                        r = await client.get(f"{base}/teams", headers=headers, params=params)
                        r.raise_for_status()
                    except httpx.HTTPStatusError as e:
                        raise
                    payload = r.json()
                    response_list = payload.get("response", [])
                    out = []
                    for t in response_list:
                        team = t.get("team") or t
                        out.append({
                            "id": team.get("id"),
                            "name": team.get("name"),
                            "abbreviation": team.get("code") or team.get("nickname") or team.get("name"),
                        })
                    basic_cache.set(cache_key, out, ttl=120)
                    return out
                elif sport_key_up == 'NFL':
                    params = {"search": q}
                    if league:
                        params["league"] = league
                    r = await client.get(f"{base}/teams", headers=headers, params=params)
                    r.raise_for_status()
                    payload = r.json()
                    response_list = payload.get("response", [])
                    out = []
                    for t in response_list:
                        team = t.get("team") or t
                        out.append({
                            "id": team.get("id"),
                            "name": team.get("name"),
                            "abbreviation": team.get("code") or team.get("name"),
                        })
                    basic_cache.set(cache_key, out, ttl=120)
                    return out
                else:
                    basic_cache.set(cache_key, [], ttl=60)
                    return []
        except httpx.HTTPStatusError as e:
            status = e.response.status_code if e.response is not None else None
            logger.error("API-Sports team search failed", extra={"sport": sport_key_up, "status": status})
            if status in (401, 403):
                raise HTTPException(status_code=502, detail="API-Sports authentication failed; check API key")
            raise HTTPException(status_code=502, detail="API-Sports team search error")
        except httpx.HTTPError as e:
            logger.error("API-Sports team search network error", extra={"sport": sport_key_up, "error": str(e)})
            raise HTTPException(status_code=502, detail="API-Sports network error")

    # --- Listing helpers for seeding ---
    async def list_football_teams(self, league_id: int, season: Optional[str] = None) -> List[Dict[str, Any]]:
        base = self._base_url_for('FOOTBALL')
        headers = self._headers_for_base(base)
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                params = {"league": league_id}
                if season:
                    params["season"] = season
                r = await client.get(f"{base}/teams", headers=headers, params=params)
                r.raise_for_status()
                payload = r.json()
                response_list = payload.get("response", [])
                out = []
                for t in response_list:
                    team = t.get('team') or {}
                    out.append({
                        "id": team.get('id'),
                        "name": team.get('name'),
                        "abbreviation": team.get('code') or team.get('name'),
                    })
                return out
        except httpx.HTTPError as e:
            logger.error("API-Sports football team list error", extra={"error": str(e), "league": league_id})
            return []

    async def list_football_players(self, league_id: int, season: str, page: int = 1) -> List[Dict[str, Any]]:
        base = self._base_url_for('FOOTBALL')
        headers = self._headers_for_base(base)
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                r = await client.get(f"{base}/players", headers=headers, params={"league": league_id, "season": season, "page": page})
                r.raise_for_status()
                payload = r.json()
                response_list = payload.get("response", [])
                out = []
                for item in response_list:
                    player = item.get('player', {})
                    statistics = item.get('statistics', [])
                    team_abbr = None
                    if statistics and isinstance(statistics, list):
                        first_stat = statistics[0]
                        team = first_stat.get("team") or {}
                        team_abbr = team.get("name")
                    out.append({
                        "id": player.get('id'),
                        "first_name": player.get('firstname'),
                        "last_name": player.get('lastname'),
                        "team_abbr": team_abbr,
                    })
                return out
        except httpx.HTTPError as e:
            logger.error("API-Sports football player list error", extra={"error": str(e), "league": league_id, "season": season, "page": page})
            return []

    async def list_nfl_teams(self, league: Optional[int] = None) -> List[Dict[str, Any]]:
        base = self._base_url_for('NFL')
        headers = self._headers_for_base(base)
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                params = {"league": league} if league else None
                r = await client.get(f"{base}/teams", headers=headers, params=params)
                r.raise_for_status()
                payload = r.json()
                response_list = payload.get('response', [])
                out = []
                for t in response_list:
                    team = t.get('team') or t
                    out.append({
                        "id": team.get('id'),
                        "name": team.get('name'),
                        "abbreviation": team.get('code') or team.get('name'),
                    })
                return out
        except httpx.HTTPError as e:
            logger.error("API-Sports NFL team list error", extra={"error": str(e)})
            return []

    async def get_nfl_team_by_id(self, team_id: int) -> Optional[Dict[str, Any]]:
        base = self._base_url_for('NFL')
        headers = self._headers_for_base(base)
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.get(f"{base}/teams", headers=headers, params={"id": team_id})
                r.raise_for_status()
                payload = r.json()
                response_list = payload.get('response', [])
                if not response_list:
                    return None
                t = response_list[0]
                team = t.get('team') or t
                return {
                    "id": team.get('id'),
                    "name": team.get('name'),
                    "abbreviation": team.get('code') or team.get('name'),
                }
        except httpx.HTTPError as e:
            logger.error("API-Sports NFL team-by-id error", extra={"error": str(e), "team_id": team_id})
            return None

    async def list_nfl_players(self, season: str, page: int = 1, league: Optional[int] = None) -> List[Dict[str, Any]]:
        base = self._base_url_for('NFL')
        headers = self._headers_for_base(base)
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                params = {"season": season, "page": page}
                if league:
                    params["league"] = league
                r = await client.get(f"{base}/players", headers=headers, params=params)
                r.raise_for_status()
                payload = r.json()
                response_list = payload.get('response', [])
                out = []
                for p in response_list:
                    name = (p.get('name') or '')
                    parts = name.split(' ')
                    first = parts[0] if parts else None
                    last = ' '.join(parts[1:]) if len(parts) > 1 else None
                    team = p.get('team') or {}
                    out.append({
                        "id": p.get('id'),
                        "first_name": first,
                        "last_name": last,
                        "team_abbr": team.get('name') or team.get('code'),
                    })
                return out
        except httpx.HTTPError as e:
            logger.error("API-Sports NFL player list error", extra={"error": str(e), "season": season, "page": page})
            return []

    async def list_nfl_team_players(self, team_id: int, season: Optional[str], page: int = 1) -> List[Dict[str, Any]]:
        """Roster fallback for NFL: list players for a specific team and season via /players.

        Returns minimal identity fields similar to list_nfl_players.
        """
        base = self._base_url_for('NFL')
        headers = self._headers_for_base(base)
        params: Dict[str, Any] = {"team": team_id, "page": page}
        if season:
            params["season"] = season
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                r = await client.get(f"{base}/players", headers=headers, params=params)
                r.raise_for_status()
                payload = r.json()
                response_list = payload.get('response', [])
                out: List[Dict[str, Any]] = []
                for p in response_list:
                    name = (p.get('name') or '')
                    parts = name.split(' ')
                    first = parts[0] if parts else None
                    last = ' '.join(parts[1:]) if len(parts) > 1 else None
                    team = p.get('team') or {}
                    out.append({
                        "id": p.get('id'),
                        "first_name": first,
                        "last_name": last,
                        "team_abbr": team.get('name') or team.get('code'),
                    })
                return out
        except httpx.HTTPError as e:
            logger.error("API-Sports NFL team roster error", extra={"error": str(e), "team": team_id, "season": season, "page": page})
            return []

    async def list_nfl_team_statistics_players(self, team_id: int, season: Optional[str]) -> List[Dict[str, Any]]:
        """Statistics fallback for NFL using /players/statistics?team=ID&season=YYYY.

        Some accounts may not have access to broad player listings; this derives roster identities from stat rows.
        """
        base = self._base_url_for('NFL')
        headers = self._headers_for_base(base)
        params: Dict[str, Any] = {"team": team_id}
        if season:
            params["season"] = season
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                r = await client.get(f"{base}/players/statistics", headers=headers, params=params)
                r.raise_for_status()
                payload = r.json()
                response_list = payload.get('response', [])
                out: List[Dict[str, Any]] = []
                for row in response_list:
                    player = row.get('player') or {}
                    team = row.get('team') or {}
                    # American football payloads often have player.name; split into first/last
                    fullname = player.get('name') or ''
                    parts = fullname.split(' ')
                    first = parts[0] if parts else None
                    last = ' '.join(parts[1:]) if len(parts) > 1 else None
                    out.append({
                        "id": player.get('id'),
                        "first_name": first,
                        "last_name": last,
                        "team_abbr": team.get('code') or team.get('name'),
                    })
                return out
        except httpx.HTTPError as e:
            logger.error("API-Sports NFL team stats list error", extra={"error": str(e), "team": team_id, "season": season})
            return []

    async def list_nfl_statistics_players(self, season: Optional[str], league: Optional[int] = None, page: int = 1) -> List[Dict[str, Any]]:
        """League-level fallback for NFL using /players/statistics with optional league and season.

        Extracts unique player identities from stat rows.
        """
        base = self._base_url_for('NFL')
        headers = self._headers_for_base(base)
        params: Dict[str, Any] = {"page": page}
        if season:
            params["season"] = season
        if league:
            params["league"] = league
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                r = await client.get(f"{base}/players/statistics", headers=headers, params=params)
                r.raise_for_status()
                payload = r.json()
                response_list = payload.get('response', [])
                out: List[Dict[str, Any]] = []
                for row in response_list:
                    player = row.get('player') or {}
                    team = row.get('team') or {}
                    fullname = player.get('name') or ''
                    parts = fullname.split(' ')
                    first = parts[0] if parts else None
                    last = ' '.join(parts[1:]) if len(parts) > 1 else None
                    out.append({
                        "id": player.get('id'),
                        "first_name": first,
                        "last_name": last,
                        "team_abbr": team.get('code') or team.get('name'),
                    })
                return out
        except httpx.HTTPError as e:
            logger.error("API-Sports NFL league stats list error", extra={"error": str(e), "season": season, "page": page})
            return []

    async def list_nba_teams(self, league: Optional[str] = 'standard') -> List[Dict[str, Any]]:
        base = self._base_url_for('NBA')
        headers = self._headers_for_base(base)
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                params = {"league": league} if league else None
                r = await client.get(f"{base}/teams", headers=headers, params=params)
                r.raise_for_status()
                payload = r.json()
                response_list = payload.get('response', [])
                out = []
                for t in response_list:
                    raw = t.get('team') or t
                    # Prefer true NBA franchises only
                    nba_flag = (raw.get('nbaFranchise') if isinstance(raw, dict) else None)
                    leagues = raw.get('leagues') if isinstance(raw, dict) else None
                    has_standard = False
                    if isinstance(leagues, dict):
                        std = leagues.get('standard')
                        if isinstance(std, dict):
                            # Teams with a 'standard' league entry are NBA-related
                            has_standard = True
                    if nba_flag is False:
                        continue
                    if nba_flag is None and not has_standard:
                        # If we can't confirm NBA linkage, skip to avoid foreign teams
                        continue
                    out.append({
                        "id": raw.get('id'),
                        "name": raw.get('name'),
                        "abbreviation": raw.get('code') or raw.get('nickname') or raw.get('name'),
                    })
                return out
        except httpx.HTTPError as e:
            logger.error("API-Sports NBA team list error", extra={"error": str(e)})
            return []

    async def list_nba_players(self, season: Optional[str], page: int = 1, league: Optional[str] = 'standard') -> List[Dict[str, Any]]:
        base = self._base_url_for('NBA')
        headers = self._headers_for_base(base)
        params = {"page": page}
        if season:
            params['season'] = season
        if league:
            params['league'] = league
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                r = await client.get(f"{base}/players", headers=headers, params=params or None)
                r.raise_for_status()
                payload = r.json()
                response_list = payload.get('response', [])
                out = []
                for p in response_list:
                    team_abbr = None
                    teams = p.get('teams') or []
                    if teams:
                        last_team = teams[-1]
                        team_abbr = (last_team.get('team') or {}).get('code') or (last_team.get('team') or {}).get('name')
                    out.append({
                        "id": p.get('id'),
                        "first_name": p.get('firstname') or p.get('firstName'),
                        "last_name": p.get('lastname') or p.get('lastName'),
                        "team_abbr": team_abbr,
                    })
                return out
        except httpx.HTTPError as e:
            logger.error("API-Sports NBA player list error", extra={"error": str(e), "season": season})
            return []

    async def list_nba_team_players(self, team_id: int, season: Optional[str], league: Optional[str] = 'standard', page: int = 1) -> List[Dict[str, Any]]:
        """Roster fallback: list players for a specific NBA team and season."""
        base = self._base_url_for('NBA')
        headers = self._headers_for_base(base)
        params = {"team": team_id, "page": page}
        if season:
            params['season'] = season
        if league:
            params['league'] = league
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                r = await client.get(f"{base}/players", headers=headers, params=params)
                r.raise_for_status()
                payload = r.json()
                response_list = payload.get('response', [])
                out = []
                for p in response_list:
                    team_abbr = None
                    teams = p.get('teams') or []
                    if teams:
                        last_team = teams[-1]
                        team_abbr = (last_team.get('team') or {}).get('code') or (last_team.get('team') or {}).get('name')
                    out.append({
                        "id": p.get('id'),
                        "first_name": p.get('firstname') or p.get('firstName'),
                        "last_name": p.get('lastname') or p.get('lastName'),
                        "team_abbr": team_abbr,
                    })
                return out
        except httpx.HTTPError as e:
            logger.error("API-Sports NBA team roster error", extra={"error": str(e), "team": team_id, "season": season})
            return []

    async def list_nba_team_statistics_players(self, team_id: int, season: Optional[str]) -> List[Dict[str, Any]]:
        """Fallback using /players/statistics?team=ID&season=YYYY to derive player identities.

        Note: This endpoint returns per-game or per-season stat rows; we only extract identity fields.
        """
        base = self._base_url_for('NBA')
        headers = self._headers_for_base(base)
        params: Dict[str, Any] = {"team": team_id}
        if season:
            params["season"] = season
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                r = await client.get(f"{base}/players/statistics", headers=headers, params=params)
                r.raise_for_status()
                payload = r.json()
                response_list = payload.get('response', [])
                out = []
                for row in response_list:
                    player = row.get('player') or {}
                    team = row.get('team') or {}
                    out.append({
                        "id": player.get('id'),
                        "first_name": player.get('firstname') or player.get('firstName'),
                        "last_name": player.get('lastname') or player.get('lastName'),
                        "team_abbr": team.get('code') or team.get('name'),
                    })
                return out
        except httpx.HTTPError as e:
            logger.error("API-Sports NBA team stats list error", extra={"error": str(e), "team": team_id, "season": season})
            return []

    # --- Basketball (NBA) basics ---
    async def get_basketball_player_basic(self, player_id: str, season: Optional[str] = None) -> Dict[str, Any]:
        """Fetch minimal NBA player info by id via API-Sports.

        Returns normalized dict with id, first_name, last_name, team {...} keys.
        """
        cache_key = f"apisports:nba:player_basic:{player_id}:{season or ''}"
        cached = basic_cache.get(cache_key)
        if cached is not None:
            return cached
        base = self._base_url_for('NBA')
        headers = self._headers_for_base(base)
        defaults = settings.API_SPORTS_DEFAULTS.get('NBA', {})
        params = {"id": player_id}
        # season not required for identity; omit to avoid 400s
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                r = await client.get(f"{base}/players", headers=headers, params=params)
                r.raise_for_status()
                payload = r.json()
                resp = payload.get('response') if isinstance(payload, dict) else None
                if not resp:
                    raise HTTPException(status_code=404, detail="NBA player not found")
                p = resp[0]
                # Teams history list; pick the most recent if present
                team_abbr = None
                team_id = None
                team_name = None
                teams = p.get('teams') or []
                if teams and isinstance(teams, list):
                    last_team = teams[-1]
                    t = last_team.get('team') or {}
                    team_id = t.get('id')
                    team_name = t.get('name')
                    team_abbr = t.get('code') or t.get('name')
                result = {
                    "id": p.get('id'),
                    "first_name": p.get('firstname') or p.get('firstName'),
                    "last_name": p.get('lastname') or p.get('lastName'),
                    "position": p.get('position'),
                    "team": {"id": team_id, "name": team_name, "abbreviation": team_abbr},
                }
                basic_cache.set(cache_key, result, ttl=300)
                return result
        except httpx.HTTPStatusError as e:
            status = e.response.status_code if e.response is not None else None
            logger.error("API-Sports NBA player fetch failed", extra={"status": status, "player_id": player_id})
            if status in (401, 403):
                raise HTTPException(status_code=502, detail="API-Sports authentication failed; check API key")
            raise HTTPException(status_code=502, detail="API-Sports NBA player error")
        except httpx.HTTPError as e:
            logger.error("API-Sports NBA player network error", extra={"error": str(e), "player_id": player_id})
            raise HTTPException(status_code=502, detail="API-Sports network error")

    async def get_basketball_team_basic(self, team_id: str) -> Dict[str, Any]:
        """Fetch minimal NBA team info by id via API-Sports.

        Returns normalized dict with id, name, abbreviation, and common fields.
        """
        cache_key = f"apisports:nba:team_basic:{team_id}"
        cached = basic_cache.get(cache_key)
        if cached is not None:
            return cached
        base = self._base_url_for('NBA')
        headers = self._headers_for_base(base)
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                r = await client.get(f"{base}/teams", headers=headers, params={"id": team_id})
                r.raise_for_status()
                payload = r.json()
                resp = payload.get('response') if isinstance(payload, dict) else None
                if not resp:
                    raise HTTPException(status_code=404, detail="NBA team not found")
                t = resp[0]
                team = t.get('team') or t
                name = team.get('name')
                code = team.get('code') or team.get('nickname') or name
                # Extract logo from top level (API returns it directly in response)
                logo = t.get('logo') or team.get('logo')
                # Extract conference/division from leagues.standard structure
                leagues = t.get('leagues', {})
                standard = leagues.get('standard', {}) if isinstance(leagues, dict) else {}
                conference = standard.get('conference') or team.get('conference')
                division = standard.get('division') or team.get('division')
                result = {
                    "id": team.get('id'),
                    "name": name,
                    "abbreviation": code,
                    "city": team.get('city'),
                    "conference": conference,
                    "division": division,
                    "logo_url": logo,
                }
                basic_cache.set(cache_key, result, ttl=600)
                return result
        except httpx.HTTPStatusError as e:
            status = e.response.status_code if e.response is not None else None
            logger.error("API-Sports NBA team fetch failed", extra={"status": status, "team_id": team_id})
            if status in (401, 403):
                raise HTTPException(status_code=502, detail="API-Sports authentication failed; check API key")
            raise HTTPException(status_code=502, detail="API-Sports NBA team error")
        except httpx.HTTPError as e:
            logger.error("API-Sports NBA team network error", extra={"error": str(e), "team_id": team_id})
            raise HTTPException(status_code=502, detail="API-Sports network error")

    async def get_basketball_player_statistics(self, player_id: str, season: Optional[str] = None) -> Dict[str, Any]:
        """Fetch NBA player statistics from API-Sports. Returns first statistics row for the given season.

        API endpoint: GET /players/statistics?player=ID&season=YYYY
        """
        cache_key = f"apisports:nba:player_stats:{player_id}:{season or ''}"
        cached = stats_cache.get(cache_key)
        if cached is not None:
            return cached
        base = self._base_url_for('NBA')
        headers = self._headers_for_base(base)
        params = {"player": player_id}
        if season:
            # API-Sports expects single year
            params["season"] = int(season) if str(season).isdigit() else season
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                r = await client.get(f"{base}/players/statistics", headers=headers, params=params)
                r.raise_for_status()
                payload = r.json()
                rows = payload.get('response') if isinstance(payload, dict) else None
                if not rows:
                    stats_cache.set(cache_key, {}, ttl=120)
                    return {}
                # Return the first row; client may request specific team/league if needed later
                result = rows[0]
                stats_cache.set(cache_key, result, ttl=300)
                return result
        except httpx.HTTPStatusError as e:
            status = e.response.status_code if e.response is not None else None
            logger.error("API-Sports NBA player statistics failed", extra={"status": status, "player_id": player_id})
            if status in (401, 403):
                raise HTTPException(status_code=502, detail="API-Sports authentication failed; check API key")
            raise HTTPException(status_code=502, detail="API-Sports NBA player statistics error")
        except httpx.HTTPError as e:
            logger.error("API-Sports NBA player statistics network error", extra={"error": str(e), "player_id": player_id})
            raise HTTPException(status_code=502, detail="API-Sports network error")

    async def get_basketball_team_statistics(self, team_id: str, season: Optional[str] = None) -> Dict[str, Any]:
        """Fetch NBA team statistics from API-Sports.

        API endpoint: GET /teams/statistics?team=ID&season=YYYY
        """
        cache_key = f"apisports:nba:team_stats:{team_id}:{season or ''}"
        cached = stats_cache.get(cache_key)
        if cached is not None:
            return cached
        base = self._base_url_for('NBA')
        headers = self._headers_for_base(base)
        params = {"team": team_id}
        if season:
            params["season"] = int(season) if str(season).isdigit() else season
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                r = await client.get(f"{base}/teams/statistics", headers=headers, params=params)
                r.raise_for_status()
                payload = r.json()
                resp = payload.get('response') if isinstance(payload, dict) else None
                result = resp or {}
                stats_cache.set(cache_key, result, ttl=300)
                return result
        except httpx.HTTPStatusError as e:
            status = e.response.status_code if e.response is not None else None
            logger.error("API-Sports NBA team statistics failed", extra={"status": status, "team_id": team_id})
            if status in (401, 403):
                raise HTTPException(status_code=502, detail="API-Sports authentication failed; check API key")
            raise HTTPException(status_code=502, detail="API-Sports NBA team statistics error")
        except httpx.HTTPError as e:
            logger.error("API-Sports NBA team statistics network error", extra={"error": str(e), "team_id": team_id})
            raise HTTPException(status_code=502, detail="API-Sports network error")

    async def get_basketball_standings(self, season: Optional[str] = None) -> Dict[str, Any]:
        """Fetch NBA standings from API-Sports.

        API endpoint: GET /standings?season=YYYY
        """
        base = self._base_url_for('NBA')
        headers = self._headers_for_base(base)
        params = {}
        if season:
            params["season"] = int(season) if str(season).isdigit() else season
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                r = await client.get(f"{base}/standings", headers=headers, params=params)
                r.raise_for_status()
                payload = r.json()
                return payload
        except httpx.HTTPStatusError as e:
            status = e.response.status_code if e.response is not None else None
            logger.error("API-Sports NBA standings failed", extra={"status": status})
            if status in (401, 403):
                raise HTTPException(status_code=502, detail="API-Sports authentication failed; check API key")
            raise HTTPException(status_code=502, detail="API-Sports NBA standings error")
        except httpx.HTTPError as e:
            logger.error("API-Sports NBA standings network error", extra={"error": str(e)})
            raise HTTPException(status_code=502, detail="API-Sports network error")

    # --- Football basics ---
    async def get_football_player_basic(self, player_id: str, season: Optional[str] = None) -> Dict[str, Any]:
        cache_key = f"apisports:football:player_basic:{player_id}:{season or ''}"
        cached = basic_cache.get(cache_key)
        if cached is not None:
            return cached
        base = self._base_url_for('FOOTBALL')
        headers = self._headers_for_base(base)
        defaults = settings.API_SPORTS_DEFAULTS.get('FOOTBALL', {})
        season_param = season or defaults.get('season')
        params = {"id": player_id}
        if season_param:
            params["season"] = season_param
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                r = await client.get(f"{base}/players", headers=headers, params=params)
                r.raise_for_status()
                payload = r.json()
                resp = payload.get('response') if isinstance(payload, dict) else None
                if not resp:
                    raise HTTPException(status_code=404, detail="EPL player not found")
                item = resp[0]
                player = item.get('player', {})
                stats_list = item.get('statistics') or []
                team_id = None
                team_name = None
                if stats_list:
                    team = (stats_list[0].get('team') or {})
                    team_id = team.get('id')
                    team_name = team.get('name')
                # Normalize first/last split
                first = player.get('firstname') or player.get('firstName')
                last = player.get('lastname') or player.get('lastName')
                result = {
                    "id": player.get('id'),
                    "first_name": first,
                    "last_name": last,
                    "position": None,
                    "team": {"id": team_id, "name": team_name, "abbreviation": team_name},
                }
                basic_cache.set(cache_key, result, ttl=300)
                return result
        except httpx.HTTPStatusError as e:
            logger.error("API-Sports EPL player fetch failed", extra={"status": e.response.status_code, "player_id": player_id})
            raise HTTPException(status_code=502, detail="API-Sports EPL player error")
        except httpx.HTTPError as e:
            logger.error("API-Sports EPL player network error", extra={"error": str(e), "player_id": player_id})
            raise HTTPException(status_code=502, detail="API-Sports network error")

    async def get_football_team_basic(self, team_id: str) -> Dict[str, Any]:
        cache_key = f"apisports:football:team_basic:{team_id}"
        cached = basic_cache.get(cache_key)
        if cached is not None:
            return cached
        base = self._base_url_for('FOOTBALL')
        headers = self._headers_for_base(base)
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                r = await client.get(f"{base}/teams", headers=headers, params={"id": team_id})
                r.raise_for_status()
                payload = r.json()
                resp = payload.get('response') if isinstance(payload, dict) else None
                if not resp:
                    raise HTTPException(status_code=404, detail="EPL team not found")
                t = resp[0]
                team = t.get('team') or t
                name = team.get('name')
                code = team.get('code') or name
                # Extract logo from team object or top level
                logo = team.get('logo') or t.get('logo')
                result = {
                    "id": team.get('id'),
                    "name": name,
                    "abbreviation": code,
                    "city": team.get('city'),
                    "conference": None,
                    "division": None,
                    "logo_url": logo,
                }
                basic_cache.set(cache_key, result, ttl=600)
                return result
        except httpx.HTTPStatusError as e:
            logger.error("API-Sports EPL team fetch failed", extra={"status": e.response.status_code, "team_id": team_id})
            raise HTTPException(status_code=502, detail="API-Sports EPL team error")
        except httpx.HTTPError as e:
            logger.error("API-Sports EPL team network error", extra={"error": str(e), "team_id": team_id})
            raise HTTPException(status_code=502, detail="API-Sports network error")

    # --- American Football (NFL) basics ---
    async def get_nfl_player_basic(self, player_id: str, season: Optional[str] = None) -> Dict[str, Any]:
        """Fetch minimal NFL player info by id via API-Sports.

        API endpoint: GET /players?id=ID [,&season=YYYY]
        Returns normalized dict with id, first_name, last_name, team {...}.
        """
        cache_key = f"apisports:nfl:player_basic:{player_id}:{season or ''}"
        cached = basic_cache.get(cache_key)
        if cached is not None:
            return cached
        base = self._base_url_for('NFL')
        headers = self._headers_for_base(base)
        params: Dict[str, Any] = {"id": player_id}
        if season:
            params["season"] = season
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                r = await client.get(f"{base}/players", headers=headers, params=params)
                r.raise_for_status()
                payload = r.json()
                resp = payload.get("response") if isinstance(payload, dict) else None
                if not resp:
                    raise HTTPException(status_code=404, detail="NFL player not found")
                p = resp[0]
                # NFL payloads often have 'name' and 'team'
                fullname = p.get("name") or ""
                parts = fullname.split()
                first = parts[0] if parts else None
                last = " ".join(parts[1:]) if len(parts) > 1 else None
                team = p.get("team") or {}
                result = {
                    "id": p.get("id"),
                    "first_name": first,
                    "last_name": last,
                    "position": p.get("position"),
                    "team": {
                        "id": team.get("id"),
                        "name": team.get("name"),
                        "abbreviation": team.get("code") or team.get("name"),
                    },
                }
                basic_cache.set(cache_key, result, ttl=300)
                return result
        except httpx.HTTPStatusError as e:
            status = e.response.status_code if e.response is not None else None
            logger.error("API-Sports NFL player fetch failed", extra={"status": status, "player_id": player_id})
            if status in (401, 403):
                raise HTTPException(status_code=502, detail="API-Sports authentication failed; check API key")
            raise HTTPException(status_code=502, detail="API-Sports NFL player error")
        except httpx.HTTPError as e:
            logger.error("API-Sports NFL player network error", extra={"error": str(e), "player_id": player_id})
            raise HTTPException(status_code=502, detail="API-Sports network error")

    async def get_nfl_team_basic(self, team_id: str) -> Dict[str, Any]:
        """Fetch minimal NFL team info by id via API-Sports.

        API endpoint: GET /teams?id=ID
        Returns normalized dict with id, name, abbreviation.
        """
        cache_key = f"apisports:nfl:team_basic:{team_id}"
        cached = basic_cache.get(cache_key)
        if cached is not None:
            return cached
        base = self._base_url_for('NFL')
        headers = self._headers_for_base(base)
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                r = await client.get(f"{base}/teams", headers=headers, params={"id": team_id})
                r.raise_for_status()
                payload = r.json()
                resp = payload.get("response") if isinstance(payload, dict) else None
                if not resp:
                    raise HTTPException(status_code=404, detail="NFL team not found")
                t = resp[0]
                team = t.get("team") or t
                name = team.get("name")
                code = team.get("code") or name
                # Extract logo from top level or team object
                logo = t.get("logo") or team.get("logo")
                # Check if API provides division/conference info
                division = team.get("division")
                conference = team.get("conference")
                result = {
                    "id": team.get("id"),
                    "name": name,
                    "abbreviation": code,
                    "city": team.get("city"),
                    "conference": conference,
                    "division": division,
                    "logo_url": logo,
                }
                basic_cache.set(cache_key, result, ttl=600)
                return result
        except httpx.HTTPStatusError as e:
            status = e.response.status_code if e.response is not None else None
            logger.error("API-Sports NFL team fetch failed", extra={"status": status, "team_id": team_id})
            if status in (401, 403):
                raise HTTPException(status_code=502, detail="API-Sports authentication failed; check API key")
            raise HTTPException(status_code=502, detail="API-Sports NFL team error")
        except httpx.HTTPError as e:
            logger.error("API-Sports NFL team network error", extra={"error": str(e), "team_id": team_id})
            raise HTTPException(status_code=502, detail="API-Sports network error")


    # --- Profile endpoints for basic widgets ---
    
    async def get_nba_player_profile(self, player_id: str) -> Dict[str, Any]:
        """Fetch NBA player profile from /players endpoint.
        
        Endpoint: GET /players?id={player_id}
        Returns full profile response.
        """
        cache_key = f"apisports:nba:player_profile:{player_id}"
        cached = basic_cache.get(cache_key)
        if cached is not None:
            return cached
        base = self._base_url_for('NBA')
        headers = self._headers_for_base(base)
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                r = await client.get(f"{base}/players", headers=headers, params={"id": player_id})
                r.raise_for_status()
                payload = r.json()
                resp = payload.get('response') if isinstance(payload, dict) else None
                if not resp or len(resp) == 0:
                    raise HTTPException(status_code=404, detail="NBA player not found")
                # Return the full first response object
                profile = resp[0]
                basic_cache.set(cache_key, profile, ttl=600)
                return profile
        except httpx.HTTPStatusError as e:
            status = e.response.status_code if e.response is not None else None
            logger.error("API-Sports NBA player profile fetch failed", extra={"status": status, "player_id": player_id})
            if status in (401, 403):
                raise HTTPException(status_code=502, detail="API-Sports authentication failed; check API key")
            raise HTTPException(status_code=502, detail="API-Sports NBA player profile error")
        except httpx.HTTPError as e:
            logger.error("API-Sports NBA player profile network error", extra={"error": str(e), "player_id": player_id})
            raise HTTPException(status_code=502, detail="API-Sports network error")
    
    async def get_nba_team_profile(self, team_id: str) -> Dict[str, Any]:
        """Fetch NBA team profile from /teams endpoint.
        
        Endpoint: GET /teams?id={team_id}
        Returns full profile response.
        """
        cache_key = f"apisports:nba:team_profile:{team_id}"
        cached = basic_cache.get(cache_key)
        if cached is not None:
            return cached
        base = self._base_url_for('NBA')
        headers = self._headers_for_base(base)
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                r = await client.get(f"{base}/teams", headers=headers, params={"id": team_id})
                r.raise_for_status()
                payload = r.json()
                resp = payload.get('response') if isinstance(payload, dict) else None
                if not resp or len(resp) == 0:
                    raise HTTPException(status_code=404, detail="NBA team not found")
                # Return the full first response object
                profile = resp[0]
                basic_cache.set(cache_key, profile, ttl=600)
                return profile
        except httpx.HTTPStatusError as e:
            status = e.response.status_code if e.response is not None else None
            logger.error("API-Sports NBA team profile fetch failed", extra={"status": status, "team_id": team_id})
            if status in (401, 403):
                raise HTTPException(status_code=502, detail="API-Sports authentication failed; check API key")
            raise HTTPException(status_code=502, detail="API-Sports NBA team profile error")
        except httpx.HTTPError as e:
            logger.error("API-Sports NBA team profile network error", extra={"error": str(e), "team_id": team_id})
            raise HTTPException(status_code=502, detail="API-Sports network error")
    
    async def get_football_player_profile(self, player_id: str) -> Dict[str, Any]:
        """Fetch Football player profile from /players/profiles endpoint.
        
        Endpoint: GET /players/profiles?player={player_id}
        Returns full profile response.
        """
        cache_key = f"apisports:football:player_profile:{player_id}"
        cached = basic_cache.get(cache_key)
        if cached is not None:
            return cached
        base = self._base_url_for('FOOTBALL')
        headers = self._headers_for_base(base)
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                r = await client.get(f"{base}/players/profiles", headers=headers, params={"player": player_id})
                r.raise_for_status()
                payload = r.json()
                resp = payload.get('response') if isinstance(payload, dict) else None
                if not resp or len(resp) == 0:
                    raise HTTPException(status_code=404, detail="Football player not found")
                # Return the full first response object
                profile = resp[0]
                basic_cache.set(cache_key, profile, ttl=600)
                return profile
        except httpx.HTTPStatusError as e:
            status = e.response.status_code if e.response is not None else None
            logger.error("API-Sports Football player profile fetch failed", extra={"status": status, "player_id": player_id})
            if status in (401, 403):
                raise HTTPException(status_code=502, detail="API-Sports authentication failed; check API key")
            raise HTTPException(status_code=502, detail="API-Sports Football player profile error")
        except httpx.HTTPError as e:
            logger.error("API-Sports Football player profile network error", extra={"error": str(e), "player_id": player_id})
            raise HTTPException(status_code=502, detail="API-Sports network error")
    
    async def get_football_team_profile(self, team_id: str) -> Dict[str, Any]:
        """Fetch Football team profile from /teams endpoint.
        
        Endpoint: GET /teams?id={team_id}
        Returns full profile response.
        """
        cache_key = f"apisports:football:team_profile:{team_id}"
        cached = basic_cache.get(cache_key)
        if cached is not None:
            return cached
        base = self._base_url_for('FOOTBALL')
        headers = self._headers_for_base(base)
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                r = await client.get(f"{base}/teams", headers=headers, params={"id": team_id})
                r.raise_for_status()
                payload = r.json()
                resp = payload.get('response') if isinstance(payload, dict) else None
                if not resp or len(resp) == 0:
                    raise HTTPException(status_code=404, detail="Football team not found")
                # Return the full first response object
                profile = resp[0]
                basic_cache.set(cache_key, profile, ttl=600)
                return profile
        except httpx.HTTPStatusError as e:
            status = e.response.status_code if e.response is not None else None
            logger.error("API-Sports Football team profile fetch failed", extra={"status": status, "team_id": team_id})
            if status in (401, 403):
                raise HTTPException(status_code=502, detail="API-Sports authentication failed; check API key")
            raise HTTPException(status_code=502, detail="API-Sports Football team profile error")
        except httpx.HTTPError as e:
            logger.error("API-Sports Football team profile network error", extra={"error": str(e), "team_id": team_id})
            raise HTTPException(status_code=502, detail="API-Sports network error")
    
    async def get_nfl_player_profile(self, player_id: str) -> Dict[str, Any]:
        """Fetch NFL player profile from /players endpoint.
        
        Endpoint: GET /players?id={player_id}
        Returns full profile response.
        """
        cache_key = f"apisports:nfl:player_profile:{player_id}"
        cached = basic_cache.get(cache_key)
        if cached is not None:
            return cached
        base = self._base_url_for('NFL')
        headers = self._headers_for_base(base)
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                r = await client.get(f"{base}/players", headers=headers, params={"id": player_id})
                r.raise_for_status()
                payload = r.json()
                resp = payload.get('response') if isinstance(payload, dict) else None
                if not resp or len(resp) == 0:
                    raise HTTPException(status_code=404, detail="NFL player not found")
                # Return the full first response object
                profile = resp[0]
                basic_cache.set(cache_key, profile, ttl=600)
                return profile
        except httpx.HTTPStatusError as e:
            status = e.response.status_code if e.response is not None else None
            logger.error("API-Sports NFL player profile fetch failed", extra={"status": status, "player_id": player_id})
            if status in (401, 403):
                raise HTTPException(status_code=502, detail="API-Sports authentication failed; check API key")
            raise HTTPException(status_code=502, detail="API-Sports NFL player profile error")
        except httpx.HTTPError as e:
            logger.error("API-Sports NFL player profile network error", extra={"error": str(e), "player_id": player_id})
            raise HTTPException(status_code=502, detail="API-Sports network error")
    
    async def get_nfl_team_profile(self, team_id: str) -> Dict[str, Any]:
        """Fetch NFL team profile from /teams endpoint.
        
        Endpoint: GET /teams?id={team_id}
        Returns full profile response.
        """
        cache_key = f"apisports:nfl:team_profile:{team_id}"
        cached = basic_cache.get(cache_key)
        if cached is not None:
            return cached
        base = self._base_url_for('NFL')
        headers = self._headers_for_base(base)
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                r = await client.get(f"{base}/teams", headers=headers, params={"id": team_id})
                r.raise_for_status()
                payload = r.json()
                resp = payload.get('response') if isinstance(payload, dict) else None
                if not resp or len(resp) == 0:
                    raise HTTPException(status_code=404, detail="NFL team not found")
                # Return the full first response object
                profile = resp[0]
                basic_cache.set(cache_key, profile, ttl=600)
                return profile
        except httpx.HTTPStatusError as e:
            status = e.response.status_code if e.response is not None else None
            logger.error("API-Sports NFL team profile fetch failed", extra={"status": status, "team_id": team_id})
            if status in (401, 403):
                raise HTTPException(status_code=502, detail="API-Sports authentication failed; check API key")
            raise HTTPException(status_code=502, detail="API-Sports NFL team profile error")
        except httpx.HTTPError as e:
            logger.error("API-Sports NFL team profile network error", extra={"error": str(e), "team_id": team_id})
            raise HTTPException(status_code=502, detail="API-Sports network error")


apisports_service = ApiSportsService()
