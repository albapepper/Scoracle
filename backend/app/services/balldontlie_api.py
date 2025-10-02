from typing import Dict, Optional
from app.core.config import settings
import httpx
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
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{self.get_base_url('NBA')}/players/{player_id}", headers=headers)
            response.raise_for_status()
            data = response.json()
        
        if basic_only:
            # Return only basic information
            return {
                "id": data["id"],
                "first_name": data["first_name"],
                "last_name": data["last_name"],
                "position": data["position"],
                "team": {
                    "id": data["team"]["id"],
                    "name": data["team"]["full_name"],
                    "abbreviation": data["team"]["abbreviation"],
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
        return await balldontlie_service.get_player_by_id(player_id, basic_only=basic_only)
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
        return await balldontlie_service.get_team_by_id(team_id, basic_only=basic_only)
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