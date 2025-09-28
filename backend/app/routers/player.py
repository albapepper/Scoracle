from fastapi import APIRouter, Depends, HTTPException, Path, Query
from typing import Optional, Dict, Any, List
from app.services.balldontlie_api import get_player_info, get_player_stats
from app.services.sports_context import get_sports_context
from app.services.stats_percentile import stats_percentile_service
from pydantic import BaseModel

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
    
    try:
        if sport.upper() == "NFL":
            # For NFL, format the response according to the specified structure
            player_info = await get_player_info(player_id, sport)
            
            # Format the response to match the required structure
            return {
                "data": player_info
            }
        else:
            # For other sports, use the existing format
            player_info = await get_player_info(player_id, sport)
            stats = await get_player_stats(player_id, sport, season=season)
            
            return {
                "player_id": player_id,
                "sport": sport,
                "season": season or "current",
                "info": player_info,
                "statistics": stats
            }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching player details: {str(e)}")

@router.get("/nfl/{player_id}")
async def get_nfl_player(
    player_id: str = Path(..., description="ID of the NFL player to fetch")
):
    """
    Get detailed NFL player information with the specified JSON structure.
    """
    try:
        player_info = await get_player_info(player_id, "NFL")
        
        # Return the data in the required format
        return {
            "data": player_info
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching NFL player: {str(e)}")
        
@router.get("/nba/{player_id}")
async def get_nba_player(
    player_id: str = Path(..., description="ID of the NBA player to fetch")
):
    """
    Get detailed NBA player information with the specified JSON structure.
    """
    try:
        player_info = await get_player_info(player_id, "NBA")
        
        # Return the data in the required format
        return {
            "data": player_info
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching NBA player: {str(e)}")
        
@router.get("/epl/{player_id}")
async def get_epl_player(
    player_id: str = Path(..., description="ID of the EPL player to fetch")
):
    """
    Get detailed EPL player information with the specified JSON structure.
    """
    try:
        player_info = await get_player_info(player_id, "EPL")
        
        # Return the data in the required format
        return {
            "data": player_info
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching EPL player: {str(e)}")
        
@router.get("/epl/{player_id}/season_stats")
async def get_epl_player_season_stats(
    player_id: str = Path(..., description="ID of the EPL player to fetch stats for"),
    season: Optional[int] = Query(None, description="Season to fetch stats for (year)")
):
    """
    Get EPL player season statistics with the specified JSON structure.
    """
    try:
        # Use the helper function to get EPL player stats
        stats = await get_player_stats(player_id, "EPL", season=str(season) if season else None)
        
        # Return the data in the required format
        return {
            "data": stats
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching EPL player season stats: {str(e)}")
        
@router.get("/nba/stats/shooting")
async def get_nba_shooting_stats(
    player_id: str = Query(..., description="ID of the NBA player to fetch shooting stats for"),
    season: Optional[int] = Query(None, description="Season to fetch stats for (year)"),
    season_type: str = Query("regular", description="Type of season (regular, playoffs)"),
    type: str = Query("5ft_range", description="Type of shooting stats")
):
    """
    Get NBA player shooting statistics with the specified JSON structure.
    """
    try:
        from app.services.balldontlie_api import get_player_shooting_stats
        
        # Use the helper function to get NBA shooting stats
        stats = await get_player_shooting_stats(
            player_id, 
            "NBA", 
            season=str(season) if season else None,
            season_type=season_type,
            stat_type=type
        )
        
        # The stats are already in the expected format
        return stats
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching NBA shooting stats: {str(e)}")


@router.get("/{player_id}/percentiles")
async def get_player_stats_percentiles(
    player_id: str = Path(..., description="ID of the player to fetch stats for"),
    season: Optional[str] = Query(None, description="Season to fetch stats for"),
    sports_context = Depends(get_sports_context)
):
    """
    Get player statistics with percentile rankings compared to other players.
    """
    # Get active sport from context
    sport = sports_context.get_active_sport()
    
    try:
        # First get the player's stats
        stats = await get_player_stats(player_id, sport, season=season)
        
        # Then calculate percentiles based on all players in that season
        percentiles = await stats_percentile_service.calculate_percentiles(stats, sport, season)
        
        return {
            "player_id": player_id,
            "sport": sport,
            "season": season or "current",
            "statistics": stats,
            "percentiles": percentiles
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating player percentiles: {str(e)}")

@router.get("/nfl/stats/season")
async def get_nfl_season_stats(
    player_id: Optional[str] = Query(None, description="ID of the NFL player to fetch stats for"),
    season: Optional[int] = Query(None, description="Season to fetch stats for (year)")
):
    """
    Get NFL season statistics with the specified JSON structure.
    If player_id is provided, returns stats for that specific player.
    Otherwise, returns stats for all players (paginated).
    """
    try:
        # Use the helper function to get NFL season stats
        stats = await get_player_stats(player_id, "NFL", season=str(season) if season else None)
        
        # The get_player_stats function now returns the data directly
        # so we need to wrap it in the expected format
        return {
            "data": stats
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching NFL season stats: {str(e)}")



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