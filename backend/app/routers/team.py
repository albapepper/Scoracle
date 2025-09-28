from fastapi import APIRouter, Depends, HTTPException, Path, Query
from typing import Optional, Dict, Any, List
from app.services.balldontlie_api import get_team_info, get_team_stats, get_standings
from app.services.sports_context import get_sports_context
from app.services.stats_percentile import stats_percentile_service
from pydantic import BaseModel

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

@router.get("/nfl/{team_id}")
async def get_nfl_team(
    team_id: str = Path(..., description="ID of the NFL team to fetch")
):
    """
    Get detailed NFL team information with the specified JSON structure.
    """
    try:
        team_info = await get_team_info(team_id, "NFL")
        
        # Return the data in the required format
        return {
            "data": [team_info]
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching NFL team: {str(e)}")
        
@router.get("/nba/{team_id}")
async def get_nba_team(
    team_id: str = Path(..., description="ID of the NBA team to fetch")
):
    """
    Get detailed NBA team information with the specified JSON structure.
    """
    try:
        team_info = await get_team_info(team_id, "NBA")
        
        # Return the data in the required format
        return {
            "data": [team_info]
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching NBA team: {str(e)}")
        
@router.get("/epl/{team_id}")
async def get_epl_team(
    team_id: str = Path(..., description="ID of the EPL team to fetch")
):
    """
    Get detailed EPL team information with the specified JSON structure.
    """
    try:
        team_info = await get_team_info(team_id, "EPL")
        
        # Return the data in the required format
        return {
            "data": [team_info]
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching EPL team: {str(e)}")
        
@router.get("/epl/{team_id}/season_stats")
async def get_epl_team_season_stats(
    team_id: str = Path(..., description="ID of the EPL team to fetch stats for"),
    season: Optional[int] = Query(None, description="Season to fetch stats for (year)")
):
    """
    Get EPL team season statistics with the specified JSON structure.
    """
    try:
        # Use the helper function to get EPL team stats
        stats = await get_team_stats(team_id, "EPL", season=str(season) if season else None)
        
        # Return the data in the required format
        return {
            "data": stats
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching EPL team season stats: {str(e)}")

@router.get("/nfl/standings")
async def get_nfl_standings(
    season: Optional[int] = Query(None, description="Season to fetch standings for (year)")
):
    """
    Get NFL team standings with the specified JSON structure.
    """
    try:
        # Use the helper function to get NFL standings
        standings = await get_standings("NFL", season=str(season) if season else None)
        
        # The standings are already in the expected format
        return standings
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching NFL standings: {str(e)}")
        
@router.get("/nba/standings")
async def get_nba_standings(
    season: Optional[int] = Query(None, description="Season to fetch standings for (year)")
):
    """
    Get NBA team standings with the specified JSON structure.
    """
    try:
        # Use the helper function to get NBA standings
        standings = await get_standings("NBA", season=str(season) if season else None)
        
        # The standings are already in the expected format
        return standings
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching NBA standings: {str(e)}")
        
@router.get("/epl/standings")
async def get_epl_standings(
    season: Optional[int] = Query(None, description="Season to fetch standings for (year)")
):
    """
    Get EPL team standings with the specified JSON structure.
    """
    try:
        # Use the helper function to get EPL standings
        standings = await get_standings("EPL", season=str(season) if season else None)
        
        # The standings are already in the expected format
        return standings
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching EPL standings: {str(e)}")


@router.get("/{team_id}/percentiles")
async def get_team_stats_percentiles(
    team_id: str = Path(..., description="ID of the team to fetch stats for"),
    season: Optional[str] = Query(None, description="Season to fetch stats for"),
    sports_context = Depends(get_sports_context)
):
    """
    Get team statistics with percentile rankings compared to other teams.
    """
    # Get active sport from context
    sport = sports_context.get_active_sport()
    
    try:
        # First get the team's stats
        stats = await get_team_stats(team_id, sport, season=season)
        
        # Then calculate percentiles based on all teams in that season
        percentiles = await stats_percentile_service.calculate_percentiles(stats, sport, season)
        
        return {
            "team_id": team_id,
            "sport": sport,
            "season": season or "current",
            "statistics": stats,
            "percentiles": percentiles
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating team percentiles: {str(e)}")