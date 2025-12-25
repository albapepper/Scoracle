"""API-Sports service client.

Thin async client for API-Sports provider supporting Football, NBA, and NFL.
"""
import logging
import os
from typing import List, Dict, Any, Optional
import httpx
from fastapi import HTTPException

from app.config import settings
from app.services.cache import basic_cache, stats_cache

logger = logging.getLogger(__name__)

# Timeout configuration
DEFAULT_TIMEOUT = httpx.Timeout(connect=3.0, read=10.0, write=10.0, pool=3.0)
LONG_TIMEOUT = httpx.Timeout(connect=3.0, read=30.0, write=10.0, pool=3.0)


class ApiSportsService:
    """Thin client for API-Sports provider.

    API-Sports has separate subdomains per sport configured in settings.API_SPORTS_DEFAULTS.
    Requires header: 'x-apisports-key: <KEY>'
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.API_SPORTS_KEY
        if not self.api_key:
            logger.warning("API_SPORTS_KEY not set – API-Sports calls will fail until configured")

    def _get_sport_config(self, sport_key: str) -> dict:
        """Get sport configuration from settings."""
        config = settings.API_SPORTS_DEFAULTS.get(sport_key.upper())
        if not config:
            raise ValueError(f"Unsupported sport: {sport_key}")
        return config

    def _base_url_for(self, sport_key: str) -> str:
        """Get base URL for a sport from centralized config."""
        return self._get_sport_config(sport_key)["base_url"]

    def _headers(self, base_url: str) -> Dict[str, str]:
        """Build headers for API-Sports or RapidAPI based on env."""
        from urllib.parse import urlparse
        env_mode = os.getenv("API_SPORTS_MODE")
        mode = (env_mode or ("rapidapi" if os.getenv("RAPIDAPI_KEY") else "direct")).lower()
        host = urlparse(base_url).netloc
        if mode == "rapidapi":
            rapid_key = os.getenv("RAPIDAPI_KEY", self.api_key)
            return {"x-rapidapi-key": rapid_key, "x-rapidapi-host": host}
        return {"x-apisports-key": self.api_key}

    async def _request(
        self,
        sport_key: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        timeout: httpx.Timeout = DEFAULT_TIMEOUT,
    ) -> Dict[str, Any]:
        """Make an API request with standard error handling."""
        if not self.api_key:
            raise HTTPException(status_code=502, detail="API-Sports key not configured")

        base = self._base_url_for(sport_key)
        headers = self._headers(base)

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                r = await client.get(f"{base}/{endpoint}", headers=headers, params=params)
                r.raise_for_status()
                return r.json()
        except httpx.HTTPStatusError as e:
            status = e.response.status_code if e.response is not None else None
            logger.error(f"API-Sports {sport_key} request failed", extra={"endpoint": endpoint, "status": status})
            if status in (401, 403):
                raise HTTPException(status_code=502, detail="API-Sports authentication failed; check API key")
            raise HTTPException(status_code=502, detail=f"API-Sports {sport_key} error")
        except httpx.HTTPError as e:
            logger.error(f"API-Sports {sport_key} network error", extra={"endpoint": endpoint, "error": str(e)})
            raise HTTPException(status_code=502, detail="API-Sports network error")

    def _parse_name(self, name: str) -> tuple:
        """Split a full name into first and last name."""
        parts = (name or "").split()
        first = parts[0] if parts else None
        last = " ".join(parts[1:]) if len(parts) > 1 else None
        return first, last

    def _normalize_player(self, p: Dict[str, Any], sport_key: str) -> Dict[str, Any]:
        """Normalize player data across sports to a common format."""
        sport_key_up = sport_key.upper()

        if sport_key_up == "FOOTBALL":
            player = p.get("player", p)
            stats_list = p.get("statistics", [])
            team_abbr = None
            if stats_list:
                team = (stats_list[0].get("team") or {})
                team_abbr = team.get("name")
            return {
                "id": player.get("id"),
                "name": player.get("name"),
                "first_name": player.get("firstname"),
                "last_name": player.get("lastname"),
                "team_abbr": team_abbr,
            }
        elif sport_key_up == "NBA":
            team_abbr = None
            teams = p.get("teams") or []
            if teams:
                last_team = teams[-1]
                team_abbr = (last_team.get("team") or {}).get("code") or (last_team.get("team") or {}).get("name")
            first_name = p.get("firstname") or p.get("firstName")
            last_name = p.get("lastname") or p.get("lastName")
            full_name = f"{first_name or ''} {last_name or ''}".strip() or None
            return {
                "id": p.get("id"),
                "name": full_name,
                "first_name": first_name,
                "last_name": last_name,
                "team_abbr": team_abbr,
            }
        else:  # NFL
            full_name = p.get("name") or ""
            first, last = self._parse_name(full_name)
            team = p.get("team") or {}
            return {
                "id": p.get("id"),
                "name": full_name,
                "first_name": first,
                "last_name": last,
                "team_abbr": team.get("name") or team.get("code"),
            }

    def _normalize_team(self, t: Dict[str, Any], sport_key: str) -> Dict[str, Any]:
        """Normalize team data across sports to a common format."""
        team = t.get("team") or t
        name = team.get("name")
        code = team.get("code") or team.get("nickname") or name
        logo = t.get("logo") or team.get("logo")

        # Extract conference/division (varies by sport)
        conference = team.get("conference")
        division = team.get("division")
        if sport_key.upper() == "NBA":
            leagues = t.get("leagues", {})
            standard = leagues.get("standard", {}) if isinstance(leagues, dict) else {}
            conference = standard.get("conference") or conference
            division = standard.get("division") or division

        return {
            "id": team.get("id"),
            "name": name,
            "abbreviation": code,
            "city": team.get("city"),
            "conference": conference,
            "division": division,
            "logo_url": logo,
        }

    # --- Generic profile endpoints ---

    async def get_player_profile(self, player_id: str, sport_key: str) -> Dict[str, Any]:
        """Fetch player profile for any sport."""
        sport_key_up = sport_key.upper()
        cache_key = f"apisports:{sport_key_up.lower()}:player_profile:{player_id}"
        cached = basic_cache.get(cache_key)
        if cached is not None:
            return cached

        # Football uses a different endpoint
        if sport_key_up == "FOOTBALL":
            endpoint = "players/profiles"
            params = {"player": player_id}
        else:
            endpoint = "players"
            params = {"id": player_id}

        payload = await self._request(sport_key_up, endpoint, params)
        resp = payload.get("response") if isinstance(payload, dict) else None
        if not resp:
            raise HTTPException(status_code=404, detail=f"{sport_key_up} player not found")

        profile = resp[0]
        basic_cache.set(cache_key, profile, ttl=600)
        return profile

    async def get_team_profile(self, team_id: str, sport_key: str) -> Dict[str, Any]:
        """Fetch team profile for any sport."""
        sport_key_up = sport_key.upper()
        cache_key = f"apisports:{sport_key_up.lower()}:team_profile:{team_id}"
        cached = basic_cache.get(cache_key)
        if cached is not None:
            return cached

        payload = await self._request(sport_key_up, "teams", {"id": team_id})
        resp = payload.get("response") if isinstance(payload, dict) else None
        if not resp:
            raise HTTPException(status_code=404, detail=f"{sport_key_up} team not found")

        profile = resp[0]
        basic_cache.set(cache_key, profile, ttl=600)
        return profile

    # --- Generic basic info endpoints ---

    async def get_player_basic(self, player_id: str, sport_key: str, season: Optional[str] = None) -> Dict[str, Any]:
        """Fetch minimal player info by id for any sport."""
        sport_key_up = sport_key.upper()
        cache_key = f"apisports:{sport_key_up.lower()}:player_basic:{player_id}:{season or ''}"
        cached = basic_cache.get(cache_key)
        if cached is not None:
            return cached

        config = self._get_sport_config(sport_key_up)
        params = {"id": player_id}
        if season or config.get("season"):
            params["season"] = season or config["season"]

        payload = await self._request(sport_key_up, "players", params)
        resp = payload.get("response")
        if not resp:
            raise HTTPException(status_code=404, detail=f"{sport_key_up} player not found")

        p = resp[0]
        normalized = self._normalize_player(p, sport_key_up)

        # Build result with team info
        if sport_key_up == "FOOTBALL":
            player = p.get("player", p)
            stats_list = p.get("statistics", [])
            team_id = team_name = None
            if stats_list:
                team = stats_list[0].get("team") or {}
                team_id = team.get("id")
                team_name = team.get("name")
            result = {
                "id": player.get("id"),
                "first_name": normalized["first_name"],
                "last_name": normalized["last_name"],
                "position": None,
                "team": {"id": team_id, "name": team_name, "abbreviation": team_name},
            }
        elif sport_key_up == "NBA":
            teams = p.get("teams") or []
            team_id = team_name = team_abbr = None
            if teams:
                last_team = teams[-1]
                t = last_team.get("team") or {}
                team_id = t.get("id")
                team_name = t.get("name")
                team_abbr = t.get("code") or team_name
            result = {
                "id": p.get("id"),
                "first_name": normalized["first_name"],
                "last_name": normalized["last_name"],
                "position": p.get("position"),
                "team": {"id": team_id, "name": team_name, "abbreviation": team_abbr},
            }
        else:  # NFL
            team = p.get("team") or {}
            result = {
                "id": p.get("id"),
                "first_name": normalized["first_name"],
                "last_name": normalized["last_name"],
                "position": p.get("position"),
                "team": {
                    "id": team.get("id"),
                    "name": team.get("name"),
                    "abbreviation": team.get("code") or team.get("name"),
                },
            }

        basic_cache.set(cache_key, result, ttl=300)
        return result

    async def get_team_basic(self, team_id: str, sport_key: str) -> Dict[str, Any]:
        """Fetch minimal team info by id for any sport."""
        sport_key_up = sport_key.upper()
        cache_key = f"apisports:{sport_key_up.lower()}:team_basic:{team_id}"
        cached = basic_cache.get(cache_key)
        if cached is not None:
            return cached

        payload = await self._request(sport_key_up, "teams", {"id": team_id})
        resp = payload.get("response")
        if not resp:
            raise HTTPException(status_code=404, detail=f"{sport_key_up} team not found")

        result = self._normalize_team(resp[0], sport_key_up)
        basic_cache.set(cache_key, result, ttl=600)
        return result

    # --- Search endpoints ---

    async def search_players(
        self,
        q: str,
        sport_key: str,
        *,
        league_override: Optional[int] = None,
        season_override: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search players across supported sports."""
        sport_key_up = sport_key.upper()
        cache_key = f"apisports:search_players:{sport_key}:{season_override or ''}:{league_override or ''}:{q.strip().lower()}"
        cached = basic_cache.get(cache_key)
        if cached is not None:
            return cached

        config = self._get_sport_config(sport_key_up)
        league = league_override if league_override is not None else config.get("league")
        season = season_override if season_override is not None else config.get("season")

        params: Dict[str, Any] = {}
        if q and q.strip():
            params["search"] = q
        if sport_key_up in ("FOOTBALL", "EPL"):
            params["league"] = league
        if season:
            params["season"] = season
        if sport_key_up == "NFL" and league:
            params["league"] = league

        try:
            payload = await self._request(sport_key_up, "players", params)
        except HTTPException:
            # Retry without league filter for NBA
            if sport_key_up == "NBA" and league:
                params.pop("league", None)
                payload = await self._request(sport_key_up, "players", params)
            else:
                raise

        response_list = payload.get("response", [])
        out = [self._normalize_player(p, sport_key_up) for p in response_list]
        basic_cache.set(cache_key, out, ttl=90)
        return out

    async def search_teams(
        self,
        q: str,
        sport_key: str,
        *,
        league_override: Optional[int] = None,
        season_override: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search teams across supported sports."""
        sport_key_up = sport_key.upper()
        cache_key = f"apisports:search_teams:{sport_key}:{season_override or ''}:{league_override or ''}:{q.strip().lower()}"
        cached = basic_cache.get(cache_key)
        if cached is not None:
            return cached

        config = self._get_sport_config(sport_key_up)
        league = league_override if league_override is not None else config.get("league")
        season = season_override if season_override is not None else config.get("season")

        params: Dict[str, Any] = {}
        if q and q.strip():
            params["search"] = q
        if sport_key_up in ("FOOTBALL", "EPL"):
            params["league"] = league
        if season and sport_key_up == "NBA":
            params["season"] = season
        if sport_key_up == "NFL" and league:
            params["league"] = league

        try:
            payload = await self._request(sport_key_up, "teams", params)
        except HTTPException:
            # Fallback to search-only for football
            if sport_key_up in ("FOOTBALL", "EPL"):
                payload = await self._request(sport_key_up, "teams", {"search": q})
            else:
                raise

        response_list = payload.get("response", [])
        out = []
        for t in response_list:
            team = t.get("team") or t
            # Filter NBA teams to only include franchises
            if sport_key_up == "NBA":
                nba_flag = team.get("nbaFranchise")
                leagues = team.get("leagues") or {}
                has_standard = isinstance(leagues.get("standard"), dict)
                if nba_flag is False or (nba_flag is None and not has_standard):
                    continue
            out.append({
                "id": team.get("id"),
                "name": team.get("name"),
                "abbreviation": team.get("code") or team.get("nickname") or team.get("name"),
            })

        basic_cache.set(cache_key, out, ttl=120)
        return out

    # --- List endpoints for seeding ---

    async def list_teams(self, sport_key: str, league: Optional[Any] = None, season: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all teams for a sport."""
        sport_key_up = sport_key.upper()
        config = self._get_sport_config(sport_key_up)

        params: Dict[str, Any] = {}
        if league is not None:
            params["league"] = league
        elif sport_key_up == "NBA":
            params["league"] = config.get("league", "standard")
        elif sport_key_up == "NFL":
            params["league"] = config.get("league", 1)
        if season:
            params["season"] = season

        try:
            payload = await self._request(sport_key_up, "teams", params or None, timeout=LONG_TIMEOUT)
        except HTTPException:
            return []

        response_list = payload.get("response", [])
        out = []
        for t in response_list:
            team = t.get("team") or t
            # Filter NBA teams
            if sport_key_up == "NBA":
                nba_flag = team.get("nbaFranchise")
                leagues = team.get("leagues") or {}
                has_standard = isinstance(leagues.get("standard"), dict)
                if nba_flag is False or (nba_flag is None and not has_standard):
                    continue
            out.append({
                "id": team.get("id"),
                "name": team.get("name"),
                "abbreviation": team.get("code") or team.get("nickname") or team.get("name"),
            })
        return out

    async def list_players(
        self,
        sport_key: str,
        season: Optional[str] = None,
        page: int = 1,
        league: Optional[Any] = None,
        team_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """List players for a sport with pagination."""
        sport_key_up = sport_key.upper()
        config = self._get_sport_config(sport_key_up)

        params: Dict[str, Any] = {}
        if season:
            params["season"] = season
        if team_id:
            params["team"] = team_id
        # Note: NBA and NFL players endpoints don't support 'league' or 'page' parameters
        # Only FOOTBALL (soccer) uses league and page for players
        if sport_key_up == "FOOTBALL":
            params["page"] = page
            if league is not None:
                params["league"] = league
            else:
                params["league"] = config.get("league")

        try:
            payload = await self._request(sport_key_up, "players", params, timeout=LONG_TIMEOUT)
        except HTTPException:
            return []

        response_list = payload.get("response", [])
        return [self._normalize_player(p, sport_key_up) for p in response_list]

    async def list_players_from_statistics(
        self,
        sport_key: str,
        team_id: Optional[int] = None,
        season: Optional[str] = None,
        league: Optional[int] = None,
        page: int = 1
    ) -> List[Dict[str, Any]]:
        """Fallback: derive player identities from statistics endpoint."""
        sport_key_up = sport_key.upper()

        params: Dict[str, Any] = {"page": page}
        if team_id:
            params["team"] = team_id
        if season:
            params["season"] = season
        if league:
            params["league"] = league

        try:
            payload = await self._request(sport_key_up, "players/statistics", params, timeout=LONG_TIMEOUT)
        except HTTPException:
            return []

        response_list = payload.get("response", [])
        out = []
        for row in response_list:
            player = row.get("player") or {}
            team = row.get("team") or {}

            if sport_key_up == "NBA":
                first_name = player.get("firstname") or player.get("firstName")
                last_name = player.get("lastname") or player.get("lastName")
                full_name = f"{first_name or ''} {last_name or ''}".strip() or None
            else:
                full_name = player.get("name") or ""
                first_name, last_name = self._parse_name(full_name)

            out.append({
                "id": player.get("id"),
                "name": full_name,
                "first_name": first_name,
                "last_name": last_name,
                "team_abbr": team.get("code") or team.get("name"),
            })
        return out

    # --- Statistics endpoints ---

    async def get_player_statistics(self, player_id: str, sport_key: str, season: Optional[str] = None) -> Dict[str, Any]:
        """Fetch player statistics for any sport."""
        sport_key_up = sport_key.upper()
        cache_key = f"apisports:{sport_key_up.lower()}:player_stats:{player_id}:{season or ''}"
        cached = stats_cache.get(cache_key)
        if cached is not None:
            return cached

        params: Dict[str, Any] = {"player": player_id}
        if season:
            params["season"] = int(season) if str(season).isdigit() else season

        payload = await self._request(sport_key_up, "players/statistics", params)
        rows = payload.get("response")
        if not rows:
            stats_cache.set(cache_key, {}, ttl=120)
            return {}

        result = rows[0]
        stats_cache.set(cache_key, result, ttl=300)
        return result

    async def get_team_statistics(self, team_id: str, sport_key: str, season: Optional[str] = None) -> Dict[str, Any]:
        """Fetch team statistics for any sport."""
        sport_key_up = sport_key.upper()
        cache_key = f"apisports:{sport_key_up.lower()}:team_stats:{team_id}:{season or ''}"
        cached = stats_cache.get(cache_key)
        if cached is not None:
            return cached

        params: Dict[str, Any] = {"team": team_id}
        if season:
            params["season"] = int(season) if str(season).isdigit() else season

        payload = await self._request(sport_key_up, "teams/statistics", params)
        result = payload.get("response") or {}
        stats_cache.set(cache_key, result, ttl=300)
        return result

    async def get_standings(self, sport_key: str, season: Optional[str] = None) -> Dict[str, Any]:
        """Fetch standings for any sport."""
        params = {}
        if season:
            params["season"] = int(season) if str(season).isdigit() else season
        return await self._request(sport_key, "standings", params)

    # --- Legacy compatibility methods (delegate to generic) ---

    async def get_basketball_player_basic(self, player_id: str, season: Optional[str] = None) -> Dict[str, Any]:
        return await self.get_player_basic(player_id, "NBA", season)

    async def get_basketball_team_basic(self, team_id: str) -> Dict[str, Any]:
        return await self.get_team_basic(team_id, "NBA")

    async def get_basketball_player_statistics(self, player_id: str, season: Optional[str] = None) -> Dict[str, Any]:
        return await self.get_player_statistics(player_id, "NBA", season)

    async def get_basketball_team_statistics(self, team_id: str, season: Optional[str] = None) -> Dict[str, Any]:
        return await self.get_team_statistics(team_id, "NBA", season)

    async def get_basketball_standings(self, season: Optional[str] = None) -> Dict[str, Any]:
        return await self.get_standings("NBA", season)

    async def get_football_player_basic(self, player_id: str, season: Optional[str] = None) -> Dict[str, Any]:
        return await self.get_player_basic(player_id, "FOOTBALL", season)

    async def get_football_team_basic(self, team_id: str) -> Dict[str, Any]:
        return await self.get_team_basic(team_id, "FOOTBALL")

    async def get_nfl_player_basic(self, player_id: str, season: Optional[str] = None) -> Dict[str, Any]:
        return await self.get_player_basic(player_id, "NFL", season)

    async def get_nfl_team_basic(self, team_id: str) -> Dict[str, Any]:
        return await self.get_team_basic(team_id, "NFL")

    async def get_nfl_team_by_id(self, team_id: int) -> Optional[Dict[str, Any]]:
        try:
            return await self.get_team_basic(str(team_id), "NFL")
        except HTTPException:
            return None

    # Legacy profile methods
    async def get_nba_player_profile(self, player_id: str) -> Dict[str, Any]:
        return await self.get_player_profile(player_id, "NBA")

    async def get_nba_team_profile(self, team_id: str) -> Dict[str, Any]:
        return await self.get_team_profile(team_id, "NBA")

    async def get_football_player_profile(self, player_id: str) -> Dict[str, Any]:
        return await self.get_player_profile(player_id, "FOOTBALL")

    async def get_football_team_profile(self, team_id: str) -> Dict[str, Any]:
        return await self.get_team_profile(team_id, "FOOTBALL")

    async def get_nfl_player_profile(self, player_id: str) -> Dict[str, Any]:
        return await self.get_player_profile(player_id, "NFL")

    async def get_nfl_team_profile(self, team_id: str) -> Dict[str, Any]:
        return await self.get_team_profile(team_id, "NFL")

    # Legacy list methods
    async def list_football_teams(self, league_id: int, season: Optional[str] = None) -> List[Dict[str, Any]]:
        return await self.list_teams("FOOTBALL", league=league_id, season=season)

    async def list_football_players(self, league_id: int, season: str, page: int = 1) -> List[Dict[str, Any]]:
        return await self.list_players("FOOTBALL", season=season, page=page, league=league_id)

    async def list_nfl_teams(self, league: Optional[int] = None, season: Optional[str] = None) -> List[Dict[str, Any]]:
        config = self._get_sport_config("NFL")
        return await self.list_teams("NFL", league=league, season=season or config.get("season"))

    async def list_nfl_players(self, season: str, page: int = 1, league: Optional[int] = None) -> List[Dict[str, Any]]:
        return await self.list_players("NFL", season=season, page=page, league=league)

    async def list_nfl_team_players(self, team_id: int, season: Optional[str], page: int = 1) -> List[Dict[str, Any]]:
        return await self.list_players("NFL", season=season, page=page, team_id=team_id)

    async def list_nfl_team_statistics_players(self, team_id: int, season: Optional[str]) -> List[Dict[str, Any]]:
        return await self.list_players_from_statistics("NFL", team_id=team_id, season=season)

    async def list_nfl_statistics_players(self, season: Optional[str], league: Optional[int] = None, page: int = 1) -> List[Dict[str, Any]]:
        return await self.list_players_from_statistics("NFL", season=season, league=league, page=page)

    async def list_nba_teams(self, league: Optional[str] = "standard") -> List[Dict[str, Any]]:
        return await self.list_teams("NBA", league=league)

    async def list_nba_players(self, season: Optional[str], page: int = 1, league: Optional[str] = "standard") -> List[Dict[str, Any]]:
        return await self.list_players("NBA", season=season, page=page, league=league)

    async def list_nba_team_players(self, team_id: int, season: Optional[str], page: int = 1) -> List[Dict[str, Any]]:
        # Note: NBA players endpoint doesn't support league parameter
        return await self.list_players("NBA", season=season, page=page, team_id=team_id)

    async def list_nba_team_statistics_players(self, team_id: int, season: Optional[str]) -> List[Dict[str, Any]]:
        return await self.list_players_from_statistics("NBA", team_id=team_id, season=season)


apisports_service = ApiSportsService()
