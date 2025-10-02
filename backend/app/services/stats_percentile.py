from typing import Dict, List, Optional, Any
from fastapi import HTTPException
import numpy as np
import httpx
from app.core.config import settings

class StatsPercentileService:
    """Service for calculating player statistic percentiles"""
    
    def __init__(self):
        self.api_key = settings.BALLDONTLIE_API_KEY
        self.base_urls = {
            "NBA": "https://api.balldontlie.io/v1",
            "NFL": "https://api.balldontlie.io/nfl/v1",
            "EPL": "https://api.balldontlie.io/epl/v1"
        }
        # Cache for season stats to avoid multiple API calls
        self._season_stats_cache = {}
        
    def get_base_url(self, sport: str) -> str:
        """Get the appropriate base URL for the given sport"""
        sport_upper = sport.upper()
        if sport_upper not in self.base_urls:
            raise ValueError(f"Unsupported sport: {sport}")
        return self.base_urls[sport_upper]
        
    async def get_all_player_stats(self, sport: str, season: Optional[str] = None) -> List[Dict]:
        """
        Fetches stats for all players in a given season to use for percentile calculations
        Uses a cache to avoid unnecessary API calls
        """
        cache_key = f"{sport}_{season}"
        
        if cache_key in self._season_stats_cache:
            return self._season_stats_cache[cache_key]
            
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        # URL and parameters vary by sport
        if sport.upper() == "NBA":
            params = {}
            if season:
                params["seasons[]"] = season
                
            url = f"{self.get_base_url('NBA')}/season_averages"
            
        elif sport.upper() == "NFL":
            params = {}
            if season:
                params["season"] = season
                
            url = f"{self.get_base_url('NFL')}/season_stats"
            
        elif sport.upper() == "EPL":
            params = {}
            if season:
                params["season"] = season
                
            url = f"{self.get_base_url('EPL')}/season_stats"
        else:
            raise ValueError(f"Percentile calculation not supported for {sport}")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=headers, params=params)
                response.raise_for_status()
                stats = response.json().get("data", [])
            
            # Filter out players with minimal playing time
            if sport.upper() == "NBA":
                # Filter for players with significant minutes
                stats = [s for s in stats if s.get("games_played", 0) >= 10]
            
            # Cache the results
            self._season_stats_cache[cache_key] = stats
            return stats
            
        except Exception as e:
            raise HTTPException(status_code=500, 
                                detail=f"Error fetching season stats for percentile calculation: {str(e)}")
    
    async def calculate_percentiles(self, player_stats: Dict, sport: str, season: Optional[str] = None) -> Dict[str, float]:
        """
        Calculate percentile ranks for each statistical category
        Returns a dictionary with the same keys as player_stats, but values are percentiles (0-100)
        """
        if not player_stats:
            return {}
            
        # Get all players' stats for comparison (placeholder simple implementation)
        all_players_stats = await self.get_all_player_stats(sport, season)
        
        if not all_players_stats:
            # If we can't get comparison data, return empty percentiles
            return {}
            
        # Calculate percentiles for each stat
        percentiles = {}

        for key, value in player_stats.items():
            # Skip non-numeric or identifier fields
            if not isinstance(value, (int, float)) or key in ['id', 'player_id', 'team_id', 'season']:
                continue
                
            # Extract this stat from all players
            all_values = [p.get(key, 0) for p in all_players_stats if key in p]
            
            if not all_values:
                continue
                
            # Percentile: proportion of players with value <= player's value
            rank = sum(1 for v in all_values if v <= value)
            percentiles[key] = round((rank / len(all_values)) * 100, 1)

        return percentiles

# Create a singleton instance
stats_percentile_service = StatsPercentileService()