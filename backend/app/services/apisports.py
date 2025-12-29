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
from app.statsdb.aggregators import NBAStatsAggregator

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


    def _normalize_player(self, p: Dict[str, Any], sport_key: str) -> Dict[str, Any]:
        """Map API field names to consistent database column names.

        Minimal transformation - just field name mapping.
        Heavy transformation/cleaning happens at output (widgets).
        """
        sport_key_up = sport_key.upper()

        if sport_key_up == "FOOTBALL":
            # Football nests player data under "player" key
            # Profile data: id, name, firstname, lastname, age, birth, nationality,
            # height, weight, number, position, photo
            player = p.get("player", p)
            stats_list = p.get("statistics", [])
            team = stats_list[0].get("team", {}) if stats_list else {}
            birth = player.get("birth", {}) or {}
            return {
                "id": player.get("id"),
                "first_name": player.get("firstname"),
                "last_name": player.get("lastname"),
                "name": player.get("name"),  # Full name like "C. Palmer"
                "position": player.get("position"),
                "nationality": player.get("nationality"),
                "photo_url": player.get("photo"),
                "team_id": team.get("id"),
                # Additional profile fields
                "age": player.get("age"),
                "birth_date": birth.get("date"),
                "birth_place": birth.get("place"),
                "birth_country": birth.get("country"),
                "height": player.get("height"),  # e.g., "189" (cm)
                "weight": player.get("weight"),  # e.g., "76" (kg)
                "number": player.get("number"),  # jersey number
                "injured": player.get("injured"),
            }

        elif sport_key_up == "NBA":
            # NBA player data structure:
            # - firstname, lastname, birth: {date, country}
            # - nba: {start, pro}, height: {feets, inches, meters}
            # - weight: {pounds, kilograms}, college, affiliation
            # - leagues: {standard: {jersey, active, pos}}
            teams = p.get("teams") or []
            team = teams[-1].get("team", {}) if teams else {}
            leagues = p.get("leagues") or {}
            standard = leagues.get("standard", {}) if isinstance(leagues, dict) else {}
            birth = p.get("birth", {}) or {}
            height = p.get("height", {}) or {}
            weight = p.get("weight", {}) or {}
            nba = p.get("nba", {}) or {}
            return {
                "id": p.get("id"),
                "first_name": p.get("firstname") or p.get("firstName"),
                "last_name": p.get("lastname") or p.get("lastName"),
                "position": standard.get("pos") if isinstance(standard, dict) else None,
                "nationality": p.get("country") or birth.get("country"),
                "photo_url": None,
                "team_id": team.get("id"),
                # Additional profile fields
                "birth_date": birth.get("date"),
                "birth_country": birth.get("country"),
                "height": height,  # dict with feets, inches, meters
                "weight": weight,  # dict with pounds, kilograms
                "college": p.get("college"),
                "affiliation": p.get("affiliation"),
                "nba_start": nba.get("start"),  # Year started in NBA
                "jersey": standard.get("jersey") if isinstance(standard, dict) else None,
                "active": standard.get("active") if isinstance(standard, dict) else None,
            }

        else:  # NFL
            # NFL /players endpoint returns rich profile data:
            # id, name, age, height, weight, college, group, position,
            # number, salary, experience, image
            team = p.get("team") or {}
            return {
                "id": p.get("id"),
                "first_name": p.get("firstname"),
                "last_name": p.get("lastname"),
                "name": p.get("name"),  # Full name
                "position": p.get("position"),
                "group": p.get("group"),  # Offense/Defense/Special Teams
                "nationality": None,
                "photo_url": p.get("image"),
                "team_id": team.get("id"),
                # Additional profile fields
                "age": p.get("age"),
                "height": p.get("height"),  # e.g., "6' 2\""
                "weight": p.get("weight"),  # e.g., "238 lbs"
                "college": p.get("college"),
                "experience": p.get("experience"),  # years
                "number": p.get("number"),  # jersey number
                "salary": p.get("salary"),
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

            # Minimal field mapping - no transformation
            out.append({
                "id": player.get("id"),
                "first_name": player.get("firstname") or player.get("firstName"),
                "last_name": player.get("lastname") or player.get("lastName"),
                "name": player.get("name"),  # Full name if available
                "position": player.get("pos") or player.get("position"),
                "photo_url": player.get("photo") or player.get("image"),
                "team_id": team.get("id"),
            })
        return out

    # --- Statistics endpoints ---

    async def get_player_statistics(
        self, player_id: str, sport_key: str, season: Optional[str] = None, league_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Fetch player statistics for any sport."""
        sport_key_up = sport_key.upper()
        cache_key = f"apisports:{sport_key_up.lower()}:player_stats:{player_id}:{season or ''}:{league_id or ''}"
        cached = stats_cache.get(cache_key)
        if cached is not None:
            return cached

        # Different sports use different endpoints and params:
        # - NBA: /players/statistics with id param, returns game-by-game stats
        # - NFL: /players/statistics with id param, returns season stats
        # - Football: /players with id+league+season params (no /players/statistics endpoint), stats embedded
        if sport_key_up == "FOOTBALL":
            params: Dict[str, Any] = {"id": player_id}
            if season:
                params["season"] = int(season) if str(season).isdigit() else season
            if league_id:
                params["league"] = league_id
            payload = await self._request(sport_key_up, "players", params)
        else:
            # NBA and NFL use 'id' param for /players/statistics
            params: Dict[str, Any] = {"id": player_id}
            if season:
                params["season"] = int(season) if str(season).isdigit() else season
            payload = await self._request(sport_key_up, "players/statistics", params)

        rows = payload.get("response")
        if not rows:
            stats_cache.set(cache_key, {}, ttl=120)
            return {}

        # NBA returns game-by-game stats - aggregate them into season totals
        if sport_key_up == "NBA" and isinstance(rows, list) and len(rows) > 1:
            # Parse season to int for filtering
            target_season = None
            if season:
                try:
                    target_season = int(season)
                except (ValueError, TypeError):
                    pass
            result = NBAStatsAggregator.aggregate_player_stats(rows, target_season=target_season)
        else:
            result = rows[0] if isinstance(rows, list) else rows
        stats_cache.set(cache_key, result, ttl=300)
        return result

    async def get_team_statistics(
        self, team_id: str, sport_key: str, season: Optional[str] = None, league_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Fetch team statistics for any sport."""
        sport_key_up = sport_key.upper()
        cache_key = f"apisports:{sport_key_up.lower()}:team_stats:{team_id}:{season or ''}:{league_id or ''}"
        cached = stats_cache.get(cache_key)
        if cached is not None:
            return cached

        # NFL uses standings endpoint (no teams/statistics endpoint available)
        # Format: /standings?league=1&season=2025&team={id}
        if sport_key_up == "NFL":
            config = self._get_sport_config(sport_key_up)
            params: Dict[str, Any] = {
                "team": team_id,
                "league": league_id if league_id else config.get("league", 1),
            }
            if season:
                params["season"] = int(season) if str(season).isdigit() else season
            payload = await self._request(sport_key_up, "standings", params)
            rows = payload.get("response", [])
            # Standings returns a list, take first match
            result = rows[0] if rows else {}
            stats_cache.set(cache_key, result, ttl=300)
            return result

        # NBA uses 'id' param, Football uses 'team' param
        # Football also requires 'league' param
        if sport_key_up == "NBA":
            params: Dict[str, Any] = {"id": team_id}
        else:
            params: Dict[str, Any] = {"team": team_id}
        if season:
            params["season"] = int(season) if str(season).isdigit() else season
        if sport_key_up == "FOOTBALL" and league_id:
            params["league"] = league_id

        payload = await self._request(sport_key_up, "teams/statistics", params)
        resp = payload.get("response")
        # NBA returns a list, others return a dict
        if isinstance(resp, list):
            result = resp[0] if resp else {}
        else:
            result = resp or {}
        stats_cache.set(cache_key, result, ttl=300)
        return result

    async def get_standings(self, sport_key: str, season: Optional[str] = None) -> Dict[str, Any]:
        """Fetch standings for any sport."""
        params = {}
        if season:
            params["season"] = int(season) if str(season).isdigit() else season
        return await self._request(sport_key, "standings", params)

apisports_service = ApiSportsService()
