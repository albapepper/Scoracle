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
        self.base_url = "https://api.balldontlie.io/v1"
        self.api_key = settings.BALLDONTLIE_API_KEY

    async def get_player_by_id(self, player_id: str, client: httpx.AsyncClient = Depends(get_client), basic_only: bool = False):
        """Get player information by ID"""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        response = await client.get(f"{self.base_url}/players/{player_id}", headers=headers)
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
        """Get player statistics by ID and season"""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        params = {"player_ids[]": player_id}
        
        if season:
            params["seasons[]"] = season
        
        response = await client.get(f"{self.base_url}/season_averages", params=params, headers=headers)
        response.raise_for_status()
        return response.json()["data"]
    
    async def get_team_by_id(self, team_id: str, client: httpx.AsyncClient = Depends(get_client), basic_only: bool = False):
        """Get team information by ID"""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        response = await client.get(f"{self.base_url}/teams/{team_id}", headers=headers)
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
        """Get team statistics by ID and season"""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        params = {"team_ids[]": team_id}
        
        if season:
            params["seasons[]"] = season
        
        # This endpoint may need adjustment based on actual API structure
        response = await client.get(f"{self.base_url}/team_stats", params=params, headers=headers)
        response.raise_for_status()
        return response.json()["data"]
    
    async def search_players(self, query: str, client: httpx.AsyncClient = Depends(get_client)):
        """Search for players by name"""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        params = {"search": query, "per_page": 10}
        response = await client.get(f"{self.base_url}/players", params=params, headers=headers)
        response.raise_for_status()
        return response.json()["data"]
    
    async def search_teams(self, query: str, client: httpx.AsyncClient = Depends(get_client)):
        """Search for teams by name"""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        # Adjust according to the actual API capability
        response = await client.get(f"{self.base_url}/teams", headers=headers)
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

# Create a singleton instance
balldontlie_service = BallDontLieService()

# Helper functions for easier access
async def get_player_info(player_id: str, sport: str, basic_only: bool = False):
    """Get player information, respecting the sport context"""
    if sport.upper() == "NBA":
        return await balldontlie_service.get_player_by_id(player_id, basic_only=basic_only)
    else:
        # For other sports, this would use different APIs
        raise NotImplementedError(f"Player info for {sport} not yet implemented")

async def get_player_stats(player_id: str, sport: str, season: Optional[str] = None):
    """Get player statistics, respecting the sport context"""
    if sport.upper() == "NBA":
        return await balldontlie_service.get_player_stats(player_id, season)
    else:
        # For other sports, this would use different APIs
        raise NotImplementedError(f"Player statistics for {sport} not yet implemented")

async def get_team_info(team_id: str, sport: str, basic_only: bool = False):
    """Get team information, respecting the sport context"""
    if sport.upper() == "NBA":
        return await balldontlie_service.get_team_by_id(team_id, basic_only=basic_only)
    else:
        # For other sports, this would use different APIs
        raise NotImplementedError(f"Team info for {sport} not yet implemented")

async def get_team_stats(team_id: str, sport: str, season: Optional[str] = None):
    """Get team statistics, respecting the sport context"""
    if sport.upper() == "NBA":
        return await balldontlie_service.get_team_stats(team_id, season)
    else:
        # For other sports, this would use different APIs
        raise NotImplementedError(f"Team statistics for {sport} not yet implemented")