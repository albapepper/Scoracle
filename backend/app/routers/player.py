from fastapi import APIRouter, Depends, HTTPException, Path, Query
from typing import Optional
from app.services.balldontlie_api import get_player_info, get_player_stats
from app.services.sports_context import get_sports_context

router = APIRouter()

@router.get("/{player_id}")
async def get_player_details(
    player_id: str = Path(..., description="ID of the player to fetch"),
    season: Optional[str] = Query(None, description="Season to fetch stats for"),
    sports_context = Depends(get_sports_context)
):
    """
    Get detailed player information and statistics.
    """
    # Get active sport from context
    sport = sports_context.get_active_sport()
    
    # Fetch player details
    player_info = await get_player_info(player_id, sport)
    
    # Fetch player statistics (defaults to current/most recent season if not specified)
    stats = await get_player_stats(player_id, sport, season=season)
    
    return {
        "player_id": player_id,
        "sport": sport,
        "season": season or "current",
        "info": player_info,
        "statistics": stats
    }

@router.get("/{player_id}/seasons")
async def get_player_seasons(
    player_id: str = Path(..., description="ID of the player to fetch seasons for"),
    sports_context = Depends(get_sports_context)
):
    """
    Get list of seasons for which a player has statistics.
    """
    sport = sports_context.get_active_sport()
    
    # This would call a service to get available seasons
    # For now, return a placeholder
    return {
        "player_id": player_id,
        "sport": sport,
        "seasons": ["2022-2023", "2021-2022", "2020-2021"]  # Will be populated by the actual service
    }