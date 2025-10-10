from typing import Dict, Optional
from app.core.config import settings
import httpx
from fastapi import HTTPException
import logging
logger = logging.getLogger(__name__)
"""Service layer for interacting with the balldontlie API.

Refactor notes (2025-10-01):
The previous iteration attempted to pass an httpx.AsyncClient into every
method via FastAPI dependency injection. That produced signature drift
and helper wrapper breakage (helpers called methods without the added
`client` parameter). It also led to repeated startup crashes and empty
search results because the server never fully reloaded.

Simplification: each service method now manages its own short‑lived
AsyncClient context. Given the very small request volume for this app,
connection pooling is not critical. If higher throughput is required
later, we can introduce an application lifespan that stores a single
client in `app.state`.

Only NBA endpoints are guaranteed supported for search right now. NFL
and EPL methods are left in place but remain best‑effort.
"""

class BallDontLieService:
    def __init__(self):
        # Base URLs for different sports
        self.base_urls = {
            "NBA": "https://api.balldontlie.io/v1",
            "NFL": "https://api.balldontlie.io/nfl/v1",
            "EPL": "https://api.balldontlie.io/epl/v1"
        }
        self.api_key = settings.BALLDONTLIE_API_KEY
        
    def get_base_url(self, sport: str) -> str:
        """Get the appropriate base URL for the given sport"""
        sport_upper = sport.upper()
        if sport_upper not in self.base_urls:
            raise ValueError(f"Unsupported sport: {sport}")
        return self.base_urls[sport_upper]

    async def get_player_by_id(self, player_id: str, basic_only: bool = False):
        """Get NBA player information by ID"""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        # Prefer shared client if available on app state (set by lifespan)
        raw_text = None
        try:
            async with httpx.AsyncClient(timeout=30.0) as fallback_client:
                client = fallback_client
                response = await client.get(f"{self.get_base_url('NBA')}/players/{player_id}", headers=headers)
                response.raise_for_status()
                raw_text = response.text
                try:
                    data = response.json()
                except ValueError:
                    logger.error("Upstream player payload not JSON", extra={"player_id": player_id, "snippet": (raw_text or "")[:300]})
                    raise HTTPException(status_code=502, detail="Malformed upstream player payload (non-json)")
        except httpx.HTTPStatusError as e:
            logger.warning("Upstream player fetch failed", extra={"player_id": player_id, "status": e.response.status_code})
            raise HTTPException(status_code=502, detail=f"Upstream player service error ({e.response.status_code})")
        except httpx.HTTPError as e:
            logger.error("Upstream player fetch network error", extra={"player_id": player_id, "error": str(e)})
            raise HTTPException(status_code=502, detail="Upstream player service unreachable")
        # Some upstream anomalies (rate-limit or temporary wrappers) may wrap the object
        # in a root key like {"data": {...}} or return a list. Normalize here.
        if isinstance(data, dict) and "data" in data and not isinstance(data.get("data"), list):
            # Single object nested under data
            data = data["data"]
        elif isinstance(data, dict) and "data" in data and isinstance(data.get("data"), list):
            # If a list was returned unexpectedly, attempt to locate by id
            for item in data["data"]:
                if item.get("id") == int(player_id):
                    data = item
                    break
        # Defensive: if still not an object with id, propagate structured error
        # Defensive validation – upstream occasionally can return a rate‑limit or error payload
        # that passes raise_for_status() (e.g. 200 with an alternate schema). Guard against
        # KeyErrors propagating into generic logs in the mentions route.
        if basic_only:
            if data.get("id") is None:
                # Only emit raw snippet if debug flag enabled
                from app.core.config import settings
                log_extra = {"player_id": player_id, "keys": list(data.keys())[:15]}
                if settings.BALLDONTLIE_DEBUG and raw_text:
                    log_extra["raw_snippet"] = raw_text[:400]
                logger.error("Malformed upstream player payload: missing id", extra=log_extra)
                # Surface a structured upstream error so caller can mark missing_entity
                raise HTTPException(status_code=502, detail="Malformed upstream player payload (missing id)")
            team_obj = data.get("team", {}) or {}
            return {
                "id": data.get("id"),
                "first_name": data.get("first_name"),
                "last_name": data.get("last_name"),
                "position": data.get("position"),
                # Additional fields exposed for player card
                "height": data.get("height"),
                "weight": data.get("weight"),
                "jersey_number": data.get("jersey_number"),
                "college": data.get("college"),
                "country": data.get("country"),
                "draft_year": data.get("draft_year"),
                "draft_round": data.get("draft_round"),
                "draft_number": data.get("draft_number"),
                "team": {
                    "id": team_obj.get("id"),
                    "name": team_obj.get("full_name") or team_obj.get("name"),
                    "abbreviation": team_obj.get("abbreviation"),
                }
            }
        
        return data
    
    async def get_player_stats(self, player_id: str, season: Optional[str] = None):
        """Get NBA player statistics by ID and season"""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        params = {"player_ids[]": player_id}
        if season:
            params["seasons[]"] = season
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{self.get_base_url('NBA')}/season_averages", params=params, headers=headers)
            response.raise_for_status()
            return response.json().get("data", [])
        
    async def get_player_shooting_stats(self, player_id: str, season: Optional[str] = None, season_type: str = "regular", stat_type: str = "5ft_range"):
        """Get NBA player shooting statistics by ID, season, and type"""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        params = {
            "player_ids[]": player_id,
            "type": stat_type
        }
        
        if season:
            params["season"] = season
            
        if season_type:
            params["season_type"] = season_type
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{self.get_base_url('NBA')}/season_averages/shooting", params=params, headers=headers)
            response.raise_for_status()
            return response.json()
    
    async def get_team_by_id(self, team_id: str, basic_only: bool = False):
        """Get NBA team information by ID"""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{self.get_base_url('NBA')}/teams/{team_id}", headers=headers)
            response.raise_for_status()
            data = response.json()
        
        if basic_only:
            # Return only basic information
            return {
                "id": data["id"],
                "name": data["full_name"],
                "abbreviation": data["abbreviation"],
                "city": data["city"],
                "conference": data["conference"],
                "division": data["division"],
            }
        
        return data
    
    async def get_team_stats(self, team_id: str, season: Optional[str] = None):
        """Get NBA team statistics by ID and season"""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        params = {"team_ids[]": team_id}
        
        if season:
            params["seasons[]"] = season
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{self.get_base_url('NBA')}/team_stats", params=params, headers=headers)
            response.raise_for_status()
            return response.json().get("data", [])
    
    async def search_players(self, query: str, sport: str = "NBA"):
        """Search for players by name"""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        params = {"search": query, "per_page": 10}
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{self.get_base_url(sport)}/players", params=params, headers=headers)
            response.raise_for_status()
            data = response.json().get("data", [])

        # Fallback: if multi-word query returns nothing, try token-based aggregation
        if not data and " " in query.strip():
            tokens = [t for t in query.lower().split() if t]
            if tokens:
                aggregated = {}
                async with httpx.AsyncClient(timeout=30.0) as client:
                    for token in tokens:
                        params_token = {"search": token, "per_page": 25}
                        try:
                            r = await client.get(f"{self.get_base_url(sport)}/players", params=params_token, headers=headers)
                            r.raise_for_status()
                            for player in r.json().get("data", []):
                                pid = player.get("id")
                                # Initialize score container
                                if pid not in aggregated:
                                    aggregated[pid] = {"player": player, "score": 0}
                                # Simple scoring: +1 per token match in first or last name
                                first = (player.get("first_name") or "").lower()
                                last = (player.get("last_name") or "").lower()
                                full = f"{first} {last}".strip()
                                if token in first or token in last or token in full:
                                    aggregated[pid]["score"] += 1
                        except httpx.HTTPError:
                            # Skip this token if request fails; continue with others
                            continue
                    # Rank by score (descending) then by last name
                    ranked = sorted(aggregated.values(), key=lambda x: (-x["score"], x["player"].get("last_name", "")))
                    # Keep only players that matched all tokens if possible; else fallback to ranked top 10
                    full_matches = [p["player"] for p in ranked if p["score"] >= len(tokens)]
                    if full_matches:
                        return full_matches[:10]
                    return [p["player"] for p in ranked[:10]]

        return data
    
    async def search_teams(self, query: str, sport: str = "NBA"):
        """Search for teams by name"""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        # Adjust according to the actual API capability
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{self.get_base_url(sport)}/teams", headers=headers)
            response.raise_for_status()
            teams = response.json().get("data", [])
        
        # Filter teams manually since the API might not support search directly
        filtered_teams = [
            team for team in teams 
            if query.lower() in team.get("full_name", "").lower() or 
               query.lower() in team.get("name", "").lower() or 
               query.lower() in team.get("abbreviation", "").lower() or 
               query.lower() in team.get("city", "").lower()
        ]
        
        return filtered_teams[:10]  # Limit to 10 results
        
    async def get_nfl_players(self, params: Dict = None):
        """Get NFL players data"""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        url = f"{self.get_base_url('NFL')}/players"
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
    
    async def get_nfl_player_by_id(self, player_id: str, basic_only: bool = False):
        """Get NFL player information by ID"""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{self.get_base_url('NFL')}/players/{player_id}", headers=headers)
            response.raise_for_status()
            data = response.json()
        
        if basic_only:
            # Return only basic information
            return {
                "id": data["id"],
                "first_name": data["first_name"],
                "last_name": data["last_name"],
                "position": data["position"],
                "position_abbreviation": data["position_abbreviation"],
                "height": data["height"],
                "weight": data["weight"],
                "jersey_number": data["jersey_number"],
                "college": data["college"],
                "experience": data["experience"],
                "age": data["age"],
                "team": {
                    "id": data["team"]["id"],
                    "name": data["team"]["name"],
                    "full_name": data["team"]["full_name"],
                    "abbreviation": data["team"]["abbreviation"],
                }
            }
        
        return data
        
    async def get_nfl_teams(self, params: Dict = None):
        """Get NFL teams data"""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        url = f"{self.get_base_url('NFL')}/teams"
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
    
    async def get_nfl_team_by_id(self, team_id: str, basic_only: bool = False):
        """Get NFL team information by ID"""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{self.get_base_url('NFL')}/teams/{team_id}", headers=headers)
            response.raise_for_status()
            data = response.json()
        
        if basic_only:
            # Return only basic information
            return {
                "id": data["id"],
                "conference": data["conference"],
                "division": data["division"],
                "location": data["location"],
                "name": data["name"],
                "full_name": data["full_name"],
                "abbreviation": data["abbreviation"],
            }
        
        return data
        
    async def get_nfl_season_stats(self, player_id: Optional[str] = None, season: Optional[int] = None):
        """Get NFL season statistics, optionally filtered by player ID and season"""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        params = {}
        
        if player_id:
            params["player_ids[]"] = player_id
        
        if season:
            params["seasons[]"] = season
            
        url = f"{self.get_base_url('NFL')}/season_stats"
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        
    async def get_nfl_standings(self, season: Optional[int] = None):
        """Get NFL team standings, optionally filtered by season"""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        params = {}
        
        if season:
            params["seasons[]"] = season
            
        url = f"{self.get_base_url('NFL')}/standings"
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        
    async def get_nba_standings(self, season: Optional[int] = None):
        """Get NBA team standings, optionally filtered by season"""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        params = {}
        
        if season:
            params["seasons[]"] = season
            
        url = f"{self.get_base_url('NBA')}/standings"
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        
    async def get_epl_players(self, params: Dict = None):
        """Get EPL players data"""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        url = f"{self.get_base_url('EPL')}/players"
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
    
    async def get_epl_player_by_id(self, player_id: str, basic_only: bool = False):
        """Get EPL player information by ID"""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{self.get_base_url('EPL')}/players/{player_id}", headers=headers)
            response.raise_for_status()
            data = response.json()
        
        if basic_only:
            # Return only basic information
            return {
                "id": data["id"],
                "position": data["position"],
                "national_team": data["national_team"],
                "height": data["height"],
                "weight": data["weight"],
                "birth_date": data["birth_date"],
                "age": data["age"],
                "name": data["name"],
                "first_name": data["first_name"],
                "last_name": data["last_name"],
                "team_ids": data["team_ids"]
            }
        
        return data
        
    async def get_epl_teams(self, params: Dict = None):
        """Get EPL teams data"""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        url = f"{self.get_base_url('EPL')}/teams"
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
    
    async def get_epl_team_by_id(self, team_id: str, basic_only: bool = False):
        """Get EPL team information by ID"""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{self.get_base_url('EPL')}/teams/{team_id}", headers=headers)
            response.raise_for_status()
            data = response.json()
        
        if basic_only:
            # Return only basic information
            return {
                "id": data["id"],
                "name": data["name"],
                "short_name": data["short_name"],
                "abbr": data["abbr"],
                "city": data["city"],
                "stadium": data["stadium"]
            }
        
        return data

# Create a singleton instance
balldontlie_service = BallDontLieService()

# Helper functions for easier access
async def get_player_info(player_id: str, sport: str, basic_only: bool = False):
    """Get player information, respecting the sport context"""
    sport_upper = sport.upper()
    if sport_upper == "NBA":
        try:
            data = await balldontlie_service.get_player_by_id(player_id, basic_only=basic_only)
            # Write-through upsert (best-effort)
            try:
                from app.db.registry import entity_registry
                await entity_registry.connect()
                full_name = f"{data.get('first_name','')} {data.get('last_name','')}".strip()
                team = data.get('team') or {}
                row = {
                    'sport': 'NBA',
                    'entity_type': 'player',
                    'id': data.get('id'),
                    'first_name': data.get('first_name'),
                    'last_name': data.get('last_name'),
                    'full_name': full_name,
                    'team_id': team.get('id'),
                    'team_abbr': team.get('abbreviation'),
                    'position': data.get('position'),
                    'search_blob': (full_name + ' ' + (team.get('abbreviation') or '')).lower().strip()
                }
                await entity_registry.upsert_entity(row)
                await entity_registry._conn.commit()
            except Exception as reg_ex:
                logger.debug("Registry write-through failed for player %s: %s", player_id, reg_ex)
            return data
        except HTTPException as e:
            if basic_only:
                # Attempt registry fallback only if single-object fetch failed
                try:
                    from app.db.registry import entity_registry
                    await entity_registry.connect()
                    row = await entity_registry.get_basic('NBA', 'player', int(player_id))
                    if row:
                        return {
                            "id": row.get("id"),
                            "first_name": row.get("first_name"),
                            "last_name": row.get("last_name"),
                            "position": row.get("position"),
                            "team": {
                                "id": row.get("team_id"),
                                "name": row.get("team_abbr"),
                                "abbreviation": row.get("team_abbr"),
                            },
                            "fallback_source": "registry"
                        }
                except Exception as reg_ex:
                    logger.debug("Player registry fallback failed %s: %s", player_id, reg_ex)
            raise e
    elif sport_upper == "NFL":
        return await balldontlie_service.get_nfl_player_by_id(player_id, basic_only=basic_only)
    elif sport_upper == "EPL":
        return await balldontlie_service.get_epl_player_by_id(player_id, basic_only=basic_only)
    else:
        raise ValueError(f"Unsupported sport: {sport}")

async def get_epl_player_season_stats(player_id: str, season: Optional[int] = None):
    """Get EPL player season statistics"""
    headers = {"Authorization": f"Bearer {balldontlie_service.api_key}"}
    params = {}
    if season:
        params["season"] = season
    async with httpx.AsyncClient(timeout=30.0) as client:
        url = f"{balldontlie_service.get_base_url('EPL')}/players/{player_id}/season_stats"
        response = await client.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()

async def get_player_stats(player_id: str, sport: str, season: Optional[str] = None):
    """Get player statistics, respecting the sport context"""
    sport_upper = sport.upper()
    if sport_upper == "NBA":
        return await balldontlie_service.get_player_stats(player_id, season)
    elif sport_upper == "NFL":
        season_int = int(season) if season and season.isdigit() else None
        result = await balldontlie_service.get_nfl_season_stats(player_id, season_int)
        return result.get("data", [])
    elif sport_upper == "EPL":
        season_int = int(season) if season and season.isdigit() else None
        result = await get_epl_player_season_stats(player_id, season_int)
        return result.get("data", [])
    else:
        raise ValueError(f"Unsupported sport: {sport}")

async def get_team_info(team_id: str, sport: str, basic_only: bool = False):
    """Get team information, respecting the sport context"""
    sport_upper = sport.upper()
    if sport_upper == "NBA":
        try:
            data = await balldontlie_service.get_team_by_id(team_id, basic_only=basic_only)
            # Write-through upsert for team basic row
            try:
                from app.db.registry import entity_registry
                await entity_registry.connect()
                full_name = data.get('full_name') or data.get('name') or ''
                row = {
                    'sport': 'NBA',
                    'entity_type': 'team',
                    'id': data.get('id'),
                    'first_name': None,
                    'last_name': None,
                    'full_name': full_name,
                    'team_id': None,
                    'team_abbr': data.get('abbreviation'),
                    'position': None,
                    'search_blob': (full_name + ' ' + (data.get('abbreviation') or '')).lower().strip()
                }
                await entity_registry.upsert_entity(row)
                await entity_registry._conn.commit()
            except Exception as reg_ex:
                logger.debug("Registry write-through failed for team %s: %s", team_id, reg_ex)
            return data
        except HTTPException:
            raise
    elif sport_upper == "NFL":
        return await balldontlie_service.get_nfl_team_by_id(team_id, basic_only=basic_only)
    elif sport_upper == "EPL":
        return await balldontlie_service.get_epl_team_by_id(team_id, basic_only=basic_only)
    else:
        raise ValueError(f"Unsupported sport: {sport}")

async def get_epl_team_season_stats(team_id: str, season: Optional[int] = None):
    """Get EPL team season statistics"""
    headers = {"Authorization": f"Bearer {balldontlie_service.api_key}"}
    params = {}
    if season:
        params["season"] = season
    async with httpx.AsyncClient(timeout=30.0) as client:
        url = f"{balldontlie_service.get_base_url('EPL')}/teams/{team_id}/season_stats"
        response = await client.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()

async def get_team_stats(team_id: str, sport: str, season: Optional[str] = None):
    """Get team statistics, respecting the sport context"""
    sport_upper = sport.upper()
    if sport_upper == "NBA":
        return await balldontlie_service.get_team_stats(team_id, season)
    elif sport_upper == "NFL":
        return []  # Placeholder
    elif sport_upper == "EPL":
        season_int = int(season) if season and season.isdigit() else None
        result = await get_epl_team_season_stats(team_id, season_int)
        return result.get("data", [])
    else:
        raise ValueError(f"Unsupported sport: {sport}")

async def get_players(sport: str, params: Dict = None):
    """Get all players for a specific sport (limited support)"""
    sport_upper = sport.upper()
    if sport_upper == "NBA":
        return {"data": await balldontlie_service.search_players("")}
    elif sport_upper == "NFL":
        return await balldontlie_service.get_nfl_players(params=params)
    elif sport_upper == "EPL":
        return await balldontlie_service.get_epl_players(params=params)
    else:
        raise ValueError(f"Unsupported sport: {sport}")

async def get_teams(sport: str, params: Dict = None):
    """Get all teams for a specific sport"""
    sport_upper = sport.upper()
    if sport_upper == "NBA":
        return {"data": await balldontlie_service.search_teams("")}
    elif sport_upper == "NFL":
        return await balldontlie_service.get_nfl_teams(params=params)
    elif sport_upper == "EPL":
        return await balldontlie_service.get_epl_teams(params=params)
    else:
        raise ValueError(f"Unsupported sport: {sport}")

async def get_player_shooting_stats(player_id: str, sport: str, season: Optional[str] = None, season_type: str = "regular", stat_type: str = "5ft_range"):
    """Get player shooting statistics, respecting the sport context"""
    sport_upper = sport.upper()
    if sport_upper == "NBA":
        return await balldontlie_service.get_player_shooting_stats(player_id, season, season_type, stat_type)
    else:
        raise ValueError(f"Shooting statistics for {sport} not yet implemented")

async def get_epl_standings(season: Optional[int] = None):
    """Get EPL team standings, optionally filtered by season"""
    headers = {"Authorization": f"Bearer {balldontlie_service.api_key}"}
    params = {}
    if season:
        params["seasons[]"] = season
    async with httpx.AsyncClient(timeout=30.0) as client:
        url = f"{balldontlie_service.get_base_url('EPL')}/standings"
        response = await client.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()

async def get_standings(sport: str, season: Optional[str] = None):
    """Get team standings for a specific sport"""
    sport_upper = sport.upper()
    if sport_upper == "NFL":
        season_int = int(season) if season and season.isdigit() else None
        return await balldontlie_service.get_nfl_standings(season_int)
    elif sport_upper == "NBA":
        season_int = int(season) if season and season.isdigit() else None
        return await balldontlie_service.get_nba_standings(season_int)
    elif sport_upper == "EPL":
        season_int = int(season) if season and season.isdigit() else None
        return await get_epl_standings(season_int)
    else:
        raise ValueError(f"Standings for {sport} not yet implemented")