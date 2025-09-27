from typing import Dict, Optional
from fastapi import Depends
from app.core.config import settings
import httpx

# Helper function to create API client
async def get_client():
    async with httpx.AsyncClient(timeout=30.0) as client:
        yield client

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

    async def get_player_by_id(self, player_id: str, client: httpx.AsyncClient = Depends(get_client), basic_only: bool = False):
        """Get NBA player information by ID"""
        headers = {"Authorization": f"Bearer {self.api_key}"}
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
    
    async def get_player_stats(self, player_id: str, season: Optional[str] = None, client: httpx.AsyncClient = Depends(get_client)):
        """Get NBA player statistics by ID and season"""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        params = {"player_ids[]": player_id}
        
        if season:
            params["seasons[]"] = season
        
        response = await client.get(f"{self.get_base_url('NBA')}/season_averages", params=params, headers=headers)
        response.raise_for_status()
        return response.json()["data"]
        
    async def get_player_shooting_stats(self, player_id: str, season: Optional[str] = None, season_type: str = "regular", stat_type: str = "5ft_range", client: httpx.AsyncClient = Depends(get_client)):
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
        
        response = await client.get(f"{self.get_base_url('NBA')}/season_averages/shooting", params=params, headers=headers)
        response.raise_for_status()
        return response.json()
    
    async def get_team_by_id(self, team_id: str, client: httpx.AsyncClient = Depends(get_client), basic_only: bool = False):
        """Get NBA team information by ID"""
        headers = {"Authorization": f"Bearer {self.api_key}"}
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
    
    async def get_team_stats(self, team_id: str, season: Optional[str] = None, client: httpx.AsyncClient = Depends(get_client)):
        """Get NBA team statistics by ID and season"""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        params = {"team_ids[]": team_id}
        
        if season:
            params["seasons[]"] = season
        
        # This endpoint may need adjustment based on actual API structure
        response = await client.get(f"{self.get_base_url('NBA')}/team_stats", params=params, headers=headers)
        response.raise_for_status()
        return response.json()["data"]
    
    async def search_players(self, query: str, client: httpx.AsyncClient = Depends(get_client)):
        """Search for NBA players by name"""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        params = {"search": query, "per_page": 10}
        response = await client.get(f"{self.get_base_url('NBA')}/players", params=params, headers=headers)
        response.raise_for_status()
        return response.json()["data"]
    
    async def search_teams(self, query: str, client: httpx.AsyncClient = Depends(get_client)):
        """Search for teams by name"""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        # Adjust according to the actual API capability
        response = await client.get(f"{self.get_base_url('NBA')}/teams", headers=headers)
        response.raise_for_status()
        teams = response.json()["data"]
        
        # Filter teams manually since the API might not support search directly
        filtered_teams = [
            team for team in teams 
            if query.lower() in team["full_name"].lower() or 
               query.lower() in team["abbreviation"].lower() or 
               query.lower() in team["city"].lower()
        ]
        
        return filtered_teams[:10]  # Limit to 10 results
        
    async def get_nfl_players(self, client: httpx.AsyncClient = Depends(get_client), params: Dict = None):
        """Get NFL players data"""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        url = f"{self.get_base_url('NFL')}/players"
        
        response = await client.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    
    async def get_nfl_player_by_id(self, player_id: str, client: httpx.AsyncClient = Depends(get_client), basic_only: bool = False):
        """Get NFL player information by ID"""
        headers = {"Authorization": f"Bearer {self.api_key}"}
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
        
    async def get_nfl_teams(self, client: httpx.AsyncClient = Depends(get_client), params: Dict = None):
        """Get NFL teams data"""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        url = f"{self.get_base_url('NFL')}/teams"
        
        response = await client.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    
    async def get_nfl_team_by_id(self, team_id: str, client: httpx.AsyncClient = Depends(get_client), basic_only: bool = False):
        """Get NFL team information by ID"""
        headers = {"Authorization": f"Bearer {self.api_key}"}
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
        
    async def get_nfl_season_stats(self, player_id: Optional[str] = None, season: Optional[int] = None, client: httpx.AsyncClient = Depends(get_client)):
        """Get NFL season statistics, optionally filtered by player ID and season"""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        params = {}
        
        if player_id:
            params["player_ids[]"] = player_id
        
        if season:
            params["seasons[]"] = season
            
        url = f"{self.get_base_url('NFL')}/season_stats"
        response = await client.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
        
    async def get_nfl_standings(self, season: Optional[int] = None, client: httpx.AsyncClient = Depends(get_client)):
        """Get NFL team standings, optionally filtered by season"""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        params = {}
        
        if season:
            params["seasons[]"] = season
            
        url = f"{self.get_base_url('NFL')}/standings"
        response = await client.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
        
    async def get_nba_standings(self, season: Optional[int] = None, client: httpx.AsyncClient = Depends(get_client)):
        """Get NBA team standings, optionally filtered by season"""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        params = {}
        
        if season:
            params["seasons[]"] = season
            
        url = f"{self.get_base_url('NBA')}/standings"
        response = await client.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
        
    async def get_epl_players(self, client: httpx.AsyncClient = Depends(get_client), params: Dict = None):
        """Get EPL players data"""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        url = f"{self.get_base_url('EPL')}/players"
        
        response = await client.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    
    async def get_epl_player_by_id(self, player_id: str, client: httpx.AsyncClient = Depends(get_client), basic_only: bool = False):
        """Get EPL player information by ID"""
        headers = {"Authorization": f"Bearer {self.api_key}"}
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
        
    async def get_epl_teams(self, client: httpx.AsyncClient = Depends(get_client), params: Dict = None):
        """Get EPL teams data"""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        url = f"{self.get_base_url('EPL')}/teams"
        
        response = await client.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    
    async def get_epl_team_by_id(self, team_id: str, client: httpx.AsyncClient = Depends(get_client), basic_only: bool = False):
        """Get EPL team information by ID"""
        headers = {"Authorization": f"Bearer {self.api_key}"}
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

async def get_epl_player_season_stats(self, player_id: str, season: Optional[int] = None, client: httpx.AsyncClient = Depends(get_client)):
        """Get EPL player season statistics"""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        params = {}
        
        if season:
            params["season"] = season
        
        url = f"{self.get_base_url('EPL')}/players/{player_id}/season_stats"
        response = await client.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()

async def get_player_stats(player_id: str, sport: str, season: Optional[str] = None):
    """Get player statistics, respecting the sport context"""
    sport_upper = sport.upper()
    if sport_upper == "NBA":
        return await balldontlie_service.get_player_stats(player_id, season)
    elif sport_upper == "NFL":
        # Convert season to int if it's a string
        season_int = int(season) if season and season.isdigit() else None
        result = await balldontlie_service.get_nfl_season_stats(player_id, season_int)
        return result.get("data", [])
    elif sport_upper == "EPL":
        # Convert season to int if it's a string
        season_int = int(season) if season and season.isdigit() else None
        result = await balldontlie_service.get_epl_player_season_stats(player_id, season_int)
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

async def get_epl_team_season_stats(self, team_id: str, season: Optional[int] = None, client: httpx.AsyncClient = Depends(get_client)):
        """Get EPL team season statistics"""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        params = {}
        
        if season:
            params["season"] = season
        
        url = f"{self.get_base_url('EPL')}/teams/{team_id}/season_stats"
        response = await client.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
        
async def get_team_stats(team_id: str, sport: str, season: Optional[str] = None):
    """Get team statistics, respecting the sport context"""
    sport_upper = sport.upper()
    if sport_upper == "NBA":
        return await balldontlie_service.get_team_stats(team_id, season)
    elif sport_upper == "NFL":
        # NFL might not have a direct stats endpoint or need a different approach
        # Return empty array for now, can be implemented later
        return []
    elif sport_upper == "EPL":
        # Convert season to int if it's a string
        season_int = int(season) if season and season.isdigit() else None
        result = await balldontlie_service.get_epl_team_season_stats(team_id, season_int)
        return result.get("data", [])
    else:
        raise ValueError(f"Unsupported sport: {sport}")

async def get_players(sport: str, params: Dict = None):
    """Get all players for a specific sport"""
    sport_upper = sport.upper()
    if sport_upper == "NBA":
        # The NBA endpoint is search-based, so we'd need to modify this approach
        # Returns first page of players
        search_params = params or {"per_page": 25}
        # Create a client using the Depends function
        async for client in get_client():
            response = await balldontlie_service.search_players("", client=client)
            return {"data": response}
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
        # NBA endpoint requires special handling to transform the response
        async for client in get_client():
            response = await balldontlie_service.search_teams("", client=client)
            return {"data": response}
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
        # For other sports, this would use different APIs or could be not applicable
        raise ValueError(f"Shooting statistics for {sport} not yet implemented")
        
async def get_epl_standings(self, season: Optional[int] = None, client: httpx.AsyncClient = Depends(get_client)):
        """Get EPL team standings, optionally filtered by season"""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        params = {}
        
        if season:
            params["seasons[]"] = season
            
        url = f"{self.get_base_url('EPL')}/standings"
        response = await client.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()

# Helper functions for easier access
async def get_standings(sport: str, season: Optional[str] = None):
    """Get team standings for a specific sport"""
    sport_upper = sport.upper()
    if sport_upper == "NFL":
        # Convert season to int if it's a string
        season_int = int(season) if season and season.isdigit() else None
        return await balldontlie_service.get_nfl_standings(season_int)
    elif sport_upper == "NBA":
        # Convert season to int if it's a string
        season_int = int(season) if season and season.isdigit() else None
        return await balldontlie_service.get_nba_standings(season_int)
    elif sport_upper == "EPL":
        # Convert season to int if it's a string
        season_int = int(season) if season and season.isdigit() else None
        return await balldontlie_service.get_epl_standings(season_int)
    else:
        # For other sports, this would use different APIs
        raise ValueError(f"Standings for {sport} not yet implemented")