from fastapi import APIRouter, Depends, HTTPException, Path, Query
from typing import Optional, Dict, Any, List
from app.services.balldontlie_api import get_player_info, get_player_stats
from app.services.sports_context import get_sports_context
from app.services.stats_percentile import stats_percentile_service
from app.services.google_rss import get_entity_mentions
from app.services.cache import basic_cache, stats_cache, percentile_cache
from pydantic import BaseModel
from app.models.schemas import PlayerFullResponse

from app.core.config import settings
import httpx
router = APIRouter()

@router.get("/{player_id}")
async def get_player_details(
    player_id: str = Path(..., description="ID of the player to fetch"),
    season: Optional[str] = Query(None, description="Season to fetch stats for"),
    sport: Optional[str] = Query(None, description="Override sport type (NBA, NFL, EPL)"),
    sports_context = Depends(get_sports_context)
):
    """
    Get detailed player information and statistics.
    """
    # Get active sport from context
    # Determine sport precedence: explicit query param > context default
    sport = (sport or sports_context.get_active_sport() or "NBA").upper()
    
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

@router.get("/{player_id}/full", response_model=PlayerFullResponse)
async def get_player_full(
    player_id: str = Path(..., description="ID of the player"),
    season: Optional[str] = Query(None, description="Season to fetch stats for"),
    include_mentions: bool = Query(True, description="Include recent mentions"),
    sport: Optional[str] = Query(None, description="Override sport type (NBA, NFL, EPL)"),
    sports_context = Depends(get_sports_context)
):
    """Aggregate endpoint returning summary + stats + percentiles (+ mentions)."""
    resolved_sport = (sport or sports_context.get_active_sport() or "NBA").upper()
    season_key = season or "current"
    cache_key_summary = f"player:summary:{resolved_sport}:{player_id}"
    cache_key_stats = f"player:stats:{resolved_sport}:{player_id}:{season_key}"
    cache_key_pct = f"player:percentiles:{resolved_sport}:{player_id}:{season_key}"

    # Summary (basic info)
    summary = basic_cache.get(cache_key_summary)
    if summary is None:
        info = await get_player_info(player_id, resolved_sport, basic_only=True)
        summary = {
            "id": str(info.get("id")),
            "sport": resolved_sport,
            "first_name": info.get("first_name"),
            "last_name": info.get("last_name"),
            "full_name": f"{info.get('first_name','')} {info.get('last_name','')}".strip(),
            "position": info.get("position"),
            "team_id": (info.get("team") or {}).get("id"),
            "team_name": (info.get("team") or {}).get("name"),
            "team_abbreviation": (info.get("team") or {}).get("abbreviation"),
        }
        basic_cache.set(cache_key_summary, summary, ttl=180)

    # Stats
    stats = stats_cache.get(cache_key_stats)
    if stats is None:
        try:
            raw_stats = await get_player_stats(player_id, resolved_sport, season=season)
            stats = (raw_stats[0] if isinstance(raw_stats, list) and raw_stats else raw_stats) or None
        except Exception:
            stats = None
        stats_cache.set(cache_key_stats, stats, ttl=300)

    # Percentiles (requires stats)
    percentiles = percentile_cache.get(cache_key_pct)
    if percentiles is None and stats:
        try:
            percentiles = await stats_percentile_service.calculate_percentiles(stats, resolved_sport, season)
        except Exception:
            percentiles = None
        percentile_cache.set(cache_key_pct, percentiles, ttl=1800)

    # Mentions (optional, no caching for now—RSS ttl would be separate if added)
    mentions = None
    if include_mentions:
        try:
            rss = await get_entity_mentions("player", player_id, resolved_sport)
            mentions = rss or []
        except Exception:
            mentions = []

    return {
        "summary": summary,
        "season": season_key,
        "stats": stats,
        "percentiles": percentiles,
        "mentions": mentions
    }

@router.get("/raw/{player_id}")
async def get_player_raw(
    player_id: str = Path(..., description="Player ID"),
    sport: str = Query("NBA"),
):
    """Diagnostic: fetch raw upstream payload (debug mode only)."""
    if not settings.BALLDONTLIE_DEBUG:
        raise HTTPException(status_code=404, detail="Not found")
    sport_upper = sport.upper()
    if sport_upper != "NBA":
        raise HTTPException(status_code=400, detail="Raw diagnostic limited to NBA")
    headers = {"Authorization": f"Bearer {settings.BALLDONTLIE_API_KEY}"}
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.get(f"https://api.balldontlie.io/v1/players/{player_id}", headers=headers)
        text = r.text[:4000]
        status = r.status_code
        try:
            parsed = r.json()
        except Exception:
            parsed = None
    return {"status": status, "raw_snippet": text, "json_keys": list(parsed.keys()) if isinstance(parsed, dict) else None}

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
    sport: Optional[str] = Query(None, description="Override sport type (NBA, NFL, EPL)"),
    sports_context = Depends(get_sports_context)
):
    """
    Get player statistics with percentile rankings compared to other players.
    """
    # Get active sport from context
    sport = (sport or sports_context.get_active_sport() or "NBA").upper()
    
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
    sport: Optional[str] = Query(None, description="Override sport type (NBA, NFL, EPL)"),
    sports_context = Depends(get_sports_context)
):
    """
    Get list of seasons for which a player has statistics.
    """
    sport = (sport or sports_context.get_active_sport() or "NBA").upper()
    
    # This would call a service to get available seasons
    # For now, return a placeholder
    return {
        "player_id": player_id,
        "sport": sport,
        "seasons": ["2022-2023", "2021-2022", "2020-2021"]  # Will be populated by the actual service
    }