from fastapi import APIRouter, Depends, HTTPException, Path, Query
from typing import Optional, Dict, Any, List
from app.services.balldontlie_api import get_team_info, get_team_stats, get_standings
from app.services.sports_context import get_sports_context
from app.services.stats_percentile import stats_percentile_service
from app.services.google_rss import get_entity_mentions
from app.services.cache import basic_cache, stats_cache, percentile_cache
from pydantic import BaseModel
from app.models.schemas import TeamFullResponse
from app.services.metrics_utils import build_metrics_group

router = APIRouter()

@router.get("/{team_id}")
async def get_team_details(
    team_id: str = Path(..., description="ID of the team to fetch"),
    season: Optional[str] = Query(None, description="Season to fetch stats for"),
    sport: Optional[str] = Query(None, description="Override sport type (NBA, NFL, EPL)"),
    sports_context = Depends(get_sports_context)
):
    """
    Get detailed team information and statistics.
    """
    # Get active sport from context
    sport = (sport or sports_context.get_active_sport() or "NBA").upper()
    
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

@router.get("/{team_id}/full", response_model=TeamFullResponse)
async def get_team_full(
    team_id: str = Path(..., description="ID of the team"),
    season: Optional[str] = Query(None, description="Season to fetch stats for"),
    include_mentions: bool = Query(True, description="Include recent mentions"),
    sport: Optional[str] = Query(None, description="Override sport type (NBA, NFL, EPL)"),
    sports_context = Depends(get_sports_context)
):
    """Aggregate endpoint returning summary + stats + percentiles (+ mentions)."""
    resolved_sport = (sport or sports_context.get_active_sport() or "NBA").upper()
    season_key = season or "current"
    cache_key_summary = f"team:summary:{resolved_sport}:{team_id}"
    cache_key_profile = f"team:profile:{resolved_sport}:{team_id}"
    cache_key_stats = f"team:stats:base:{resolved_sport}:{team_id}:{season_key}"
    cache_key_pct = f"team:percentiles:base:{resolved_sport}:{team_id}:{season_key}"
    cache_key_standings = f"team:stats:standings:{resolved_sport}:{team_id}:{season_key}"
    cache_key_standings_pct = f"team:percentiles:standings:{resolved_sport}:{team_id}:{season_key}"

    summary = basic_cache.get(cache_key_summary)
    if summary is None:
        info = await get_team_info(team_id, resolved_sport, basic_only=True)
        summary = {
            "id": str(info.get("id")),
            "sport": resolved_sport,
            "name": info.get("name"),
            "abbreviation": info.get("abbreviation"),
            "city": info.get("city"),
            "conference": info.get("conference"),
            "division": info.get("division"),
        }
        basic_cache.set(cache_key_summary, summary, ttl=300)

    # Full profile (richer fields)
    profile = basic_cache.get(cache_key_profile)
    if profile is None:
        try:
            full_info = await get_team_info(team_id, resolved_sport, basic_only=False)
            if isinstance(full_info, dict):
                profile = {
                    "city": full_info.get("city"),
                    "full_name": full_info.get("full_name") or full_info.get("name"),
                    "conference": full_info.get("conference"),
                    "division": full_info.get("division"),
                }
            else:
                profile = None
        except Exception:
            profile = None
        basic_cache.set(cache_key_profile, profile, ttl=600)

    stats = stats_cache.get(cache_key_stats)
    if stats is None:
        try:
            raw_stats = await get_team_stats(team_id, resolved_sport, season=season)
            stats = (raw_stats[0] if isinstance(raw_stats, list) and raw_stats else raw_stats) or None
        except Exception:
            stats = None
        stats_cache.set(cache_key_stats, stats, ttl=300)

    percentiles = percentile_cache.get(cache_key_pct)
    if percentiles is None and stats:
        try:
            percentiles = await stats_percentile_service.calculate_percentiles(stats, resolved_sport, season)
        except Exception:
            percentiles = None
        percentile_cache.set(cache_key_pct, percentiles, ttl=1800)

    # Standings group
    standings_entry = stats_cache.get(cache_key_standings)
    if standings_entry is None:
        try:
            standings_payload = await get_standings(resolved_sport, season=season)
            # standings payload shape: {"data": [ ... ]}
            data_list = standings_payload.get('data') if isinstance(standings_payload, dict) else None
            found = None
            if isinstance(data_list, list):
                for d in data_list:
                    team_obj = (d.get('team') or {}) if isinstance(d, dict) else {}
                    if str(team_obj.get('id')) == str(team_id):
                        found = d
                        break
            standings_entry = found
        except Exception:
            standings_entry = None
        stats_cache.set(cache_key_standings, standings_entry, ttl=600)

    standings_percentiles = percentile_cache.get(cache_key_standings_pct)
    if standings_percentiles is None and standings_entry:
        try:
            # Extract numeric subset
            numeric_subset = {k: v for k, v in standings_entry.items() if isinstance(v, (int, float))}
            standings_percentiles = await stats_percentile_service.calculate_percentiles(numeric_subset, resolved_sport, season)
        except Exception:
            standings_percentiles = None
        percentile_cache.set(cache_key_standings_pct, standings_percentiles, ttl=1800)

    mentions = None
    if include_mentions:
        try:
            rss = await get_entity_mentions("team", team_id, resolved_sport)
            mentions = rss or []
        except Exception:
            mentions = []

    metrics_groups = {}
    if stats:
        metrics_groups['base'] = build_metrics_group('base', stats, percentiles)
    if standings_entry:
        metrics_groups['standings'] = build_metrics_group('standings', standings_entry, standings_percentiles)

    return {
        "summary": summary,
        "season": season_key,
        "stats": stats,
        "percentiles": percentiles,
        "mentions": mentions,
        "profile": profile,
        "metrics": {"groups": metrics_groups}
    }

@router.get("/{team_id}/roster")
async def get_team_roster(
    team_id: str = Path(..., description="ID of the team to fetch roster for"),
    season: Optional[str] = Query(None, description="Season to fetch roster for"),
    sport: Optional[str] = Query(None, description="Override sport type (NBA, NFL, EPL)"),
    sports_context = Depends(get_sports_context)
):
    """
    Get roster of players for a team in a specific season.
    """
    sport = (sport or sports_context.get_active_sport() or "NBA").upper()
    
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
    sport: Optional[str] = Query(None, description="Override sport type (NBA, NFL, EPL)"),
    sports_context = Depends(get_sports_context)
):
    """
    Get team statistics with percentile rankings compared to other teams.
    """
    # Get active sport from context
    sport = (sport or sports_context.get_active_sport() or "NBA").upper()
    
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