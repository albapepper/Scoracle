from fastapi import APIRouter, Depends, HTTPException, Path, Query
from typing import Optional
from app.services.balldontlie_api import get_team_info, get_team_stats
from app.services.sports_context import get_sports_context

router = APIRouter()

@router.get("/{team_id}")
async def get_team_details(
    team_id: str = Path(..., description="ID of the team to fetch"),
    season: Optional[str] = Query(None, description="Season to fetch stats for"),
    sports_context = Depends(get_sports_context)
):
    """
    Get detailed team information and statistics.
    """
    # Get active sport from context
    sport = sports_context.get_active_sport()
    
    # Fetch team details
    team_info = await get_team_info(team_id, sport)
    
    # Fetch team statistics (defaults to current/most recent season if not specified)
    stats = await get_team_stats(team_id, sport, season=season)
    
    return {
        "team_id": team_id,
        "sport": sport,
        "season": season or "current",
        "info": team_info,
        "statistics": stats
    }

@router.get("/{team_id}/roster")
async def get_team_roster(
    team_id: str = Path(..., description="ID of the team to fetch roster for"),
    season: Optional[str] = Query(None, description="Season to fetch roster for"),
    sports_context = Depends(get_sports_context)
):
    """
    Get roster of players for a team in a specific season.
    """
    sport = sports_context.get_active_sport()
    
    # This would call a service to get the team roster
    # For now, return a placeholder
    return {
        "team_id": team_id,
        "sport": sport,
        "season": season or "current",
        "roster": []  # Will be populated by the actual service
    }