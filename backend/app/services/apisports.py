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

    def _aggregate_nba_player_stats(self, games: List[Dict[str, Any]], target_season: Optional[int] = None) -> Dict[str, Any]:
        """Aggregate NBA game-by-game stats into season totals.

        The NBA API returns individual game records. This method sums them
        into season totals for storage in the stats database.

        Args:
            games: List of game records from the API
            target_season: If provided, only aggregate games from this season
        """
        if not games:
            return {}

        # Filter games by season if target_season specified
        if target_season:
            filtered_games = []
            for game in games:
                # Game records have game.season or team.season
                game_data = game.get("game", {}) or {}
                game_season = game_data.get("season")

                # Also check team structure for season
                if not game_season:
                    team_data = game.get("team", {}) or {}
                    game_season = team_data.get("season")

                # If we can extract a season, filter by it
                if game_season:
                    try:
                        if int(game_season) == target_season:
                            filtered_games.append(game)
                    except (ValueError, TypeError):
                        # Can't parse season, include the game
                        filtered_games.append(game)
                else:
                    # No season info, include the game
                    filtered_games.append(game)

            games = filtered_games if filtered_games else games

        # Use first game as template for player/team info
        first_game = games[0]

        # Initialize aggregates
        games_played = len(games)
        games_started = 0
        total_minutes = 0
        points = 0
        fgm = 0
        fga = 0
        tpm = 0  # 3-pointers made
        tpa = 0  # 3-pointers attempted
        ftm = 0
        fta = 0
        off_reb = 0
        def_reb = 0
        tot_reb = 0
        assists = 0
        turnovers = 0
        steals = 0
        blocks = 0
        fouls = 0
        plus_minus = 0

        for game in games:
            # Check if started
            if game.get("pos") or game.get("game", {}).get("start"):
                games_started += 1

            # Parse minutes (can be "MM:SS" or just minutes)
            mins = game.get("min") or game.get("minutes") or "0"
            if isinstance(mins, str) and ":" in mins:
                parts = mins.split(":")
                total_minutes += int(parts[0]) + (int(parts[1]) / 60 if len(parts) > 1 else 0)
            else:
                try:
                    total_minutes += float(mins) if mins else 0
                except (ValueError, TypeError):
                    pass

            # Sum counting stats
            points += game.get("points") or 0
            fgm += game.get("fgm") or 0
            fga += game.get("fga") or 0
            tpm += game.get("tpm") or 0
            tpa += game.get("tpa") or 0
            ftm += game.get("ftm") or 0
            fta += game.get("fta") or 0
            off_reb += game.get("offReb") or 0
            def_reb += game.get("defReb") or 0
            tot_reb += game.get("totReb") or 0
            assists += game.get("assists") or 0
            turnovers += game.get("turnovers") or 0
            steals += game.get("steals") or 0
            blocks += game.get("blocks") or 0
            fouls += game.get("pFouls") or 0

            # Plus/minus can be string like "+5" or "-3"
            pm = game.get("plusMinus") or 0
            if isinstance(pm, str):
                try:
                    plus_minus += int(pm)
                except ValueError:
                    pass
            else:
                plus_minus += pm or 0

        # Build aggregated result matching the structure expected by transform_player_stats
        # The transform expects specific key names and nested structures
        return {
            "player": first_game.get("player"),
            "team": first_game.get("team"),
            # Transform expects "games" with "played" and "started" keys
            "games": {"played": games_played, "started": games_started},
            # Transform checks for points dict with "total" or "points_total" key
            "points_total": points,
            # Minutes as integer
            "min": int(total_minutes),
            # Shooting stats as simple integers (transform handles this)
            "fgm": fgm,
            "fga": fga,
            "fgp": round((fgm / fga * 100), 1) if fga > 0 else 0,
            "tpm": tpm,
            "tpa": tpa,
            "tpp": round((tpm / tpa * 100), 1) if tpa > 0 else 0,
            "ftm": ftm,
            "fta": fta,
            "ftp": round((ftm / fta * 100), 1) if fta > 0 else 0,
            # Rebounds - transform looks for offReb, defReb, totReb
            "offReb": off_reb,
            "defReb": def_reb,
            "totReb": tot_reb,
            # Other counting stats
            "assists": assists,
            "turnovers": turnovers,
            "steals": steals,
            "blocks": blocks,
            "pFouls": fouls,
            "plusMinus": plus_minus,
            # Mark as aggregated season totals
            "_aggregated": True,
            "_games_count": games_played,
        }

    def _normalize_player(self, p: Dict[str, Any], sport_key: str) -> Dict[str, Any]:
        """Map API field names to consistent database column names.

        Minimal transformation - just field name mapping.
        Heavy transformation/cleaning happens at output (widgets).
        """
        sport_key_up = sport_key.upper()

        if sport_key_up == "FOOTBALL":
            # Football nests player data under "player" key
            player = p.get("player", p)
            stats_list = p.get("statistics", [])
            team = stats_list[0].get("team", {}) if stats_list else {}
            return {
                "id": player.get("id"),
                "first_name": player.get("firstname"),
                "last_name": player.get("lastname"),
                "position": player.get("position"),
                "nationality": player.get("nationality"),
                "photo_url": player.get("photo"),
                "team_id": team.get("id"),
            }

        elif sport_key_up == "NBA":
            # NBA: firstname/lastName, position in leagues.standard.pos
            teams = p.get("teams") or []
            team = teams[-1].get("team", {}) if teams else {}
            leagues = p.get("leagues") or {}
            standard = leagues.get("standard", {}) if isinstance(leagues, dict) else {}
            return {
                "id": p.get("id"),
                "first_name": p.get("firstname") or p.get("firstName"),
                "last_name": p.get("lastname") or p.get("lastName"),
                "position": standard.get("pos") if isinstance(standard, dict) else None,
                "nationality": p.get("country"),
                "photo_url": None,
                "team_id": team.get("id"),
            }

        else:  # NFL
            # NFL: name is full name, position at top level
            team = p.get("team") or {}
            return {
                "id": p.get("id"),
                "first_name": p.get("firstname"),
                "last_name": p.get("lastname"),
                "name": p.get("name"),  # Full name - split at output if needed
                "position": p.get("position"),
                "nationality": None,
                "photo_url": p.get("image"),
                "team_id": team.get("id"),
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
            result = self._aggregate_nba_player_stats(rows, target_season=target_season)
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
