from fastapi import APIRouter, Depends, HTTPException, Path, Query
from typing import Optional, Dict, Any, List
import logging
from app.services.balldontlie_api import get_player_info, get_player_stats
from app.services.sports_context import get_sports_context
from app.services.stats_percentile import stats_percentile_service
from app.services.google_rss import get_entity_mentions
from app.services.cache import basic_cache, stats_cache, percentile_cache
from pydantic import BaseModel
from app.models.schemas import PlayerFullResponse
from app.services.metrics_utils import normalize_season_average, remap_percentile_keys, build_metrics_group
from pydantic import ValidationError

from app.core.config import settings
import httpx
router = APIRouter()
logger = logging.getLogger(__name__)

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

def _normalize_season_for_upstream(sport: str, season: Optional[str]) -> Optional[str]:
    """Normalize season formats coming from the UI.

    Accepted inputs examples:
    - "2022" (already fine)
    - "2022-2023" (take the first year for upstream NBA season_averages)
    - "current" or None -> None (let upstream treat as current season when supported)
    """
    if not season or season.lower() == "current":
        return None
    # Only implement normalization for NBA for now; other sports keep raw (they may expect single year anyway)
    if sport.upper() == "NBA" and "-" in season:
        first = season.split("-")[0]
        if first.isdigit():
            return first
    return season

@router.get("/{player_id}/full", response_model=PlayerFullResponse)
async def get_player_full(
    player_id: str = Path(..., description="ID of the player"),
    season: Optional[str] = Query(None, description="Season to fetch stats for (can be 'YYYY' or 'YYYY-YYYY')"),
    include_mentions: bool = Query(True, description="Include recent mentions"),
    sport: Optional[str] = Query(None, description="Override sport type (NBA, NFL, EPL)"),
    sports_context = Depends(get_sports_context)
):
    """Aggregate endpoint returning summary + stats + percentiles (+ mentions).

    Adds defensive logging + season normalization to diagnose 500 errors when clients
    pass range seasons like 2022-2023.
    """
    resolved_sport = (sport or sports_context.get_active_sport() or "NBA").upper()
    season_key = season or "current"
    normalized_season = _normalize_season_for_upstream(resolved_sport, season)

    cache_key_summary = f"player:summary:{resolved_sport}:{player_id}"
    cache_key_profile = f"player:profile:{resolved_sport}:{player_id}"
    cache_key_stats = f"player:stats:base:{resolved_sport}:{player_id}:{season_key}"
    cache_key_pct = f"player:percentiles:base:{resolved_sport}:{player_id}:{season_key}"
    cache_key_shooting_stats = f"player:stats:shooting:{resolved_sport}:{player_id}:{season_key}"
    cache_key_shooting_pct = f"player:percentiles:shooting:{resolved_sport}:{player_id}:{season_key}"
    # NFL advanced stats groups (light mode: no percentile cohort yet)
    cache_key_nfl_rushing = f"player:stats:nfl_rushing:{resolved_sport}:{player_id}:{season_key}"
    cache_key_nfl_passing = f"player:stats:nfl_passing:{resolved_sport}:{player_id}:{season_key}"
    cache_key_nfl_receiving = f"player:stats:nfl_receiving:{resolved_sport}:{player_id}:{season_key}"
    # EPL season stats group
    cache_key_epl_player_stats = f"player:stats:epl_season_stats:{resolved_sport}:{player_id}:{season_key}"

    try:
        # Summary (basic info)
        summary = basic_cache.get(cache_key_summary)
        if summary is None:
            info = await get_player_info(player_id, resolved_sport, basic_only=True)
            team_obj = (info.get("team") or {})
            team_raw_id = team_obj.get("id")
            summary = {
                "id": str(info.get("id")),
                "sport": resolved_sport,
                "first_name": info.get("first_name"),
                "last_name": info.get("last_name"),
                "full_name": f"{info.get('first_name','')} {info.get('last_name','')}".strip(),
                "position": info.get("position"),
                # Force team_id to string if present
                "team_id": str(team_raw_id) if team_raw_id is not None else None,
                "team_name": team_obj.get("name"),
                "team_abbreviation": team_obj.get("abbreviation"),
            }
            basic_cache.set(cache_key_summary, summary, ttl=180)
        else:
            # Sanitize cached summary if earlier version stored int team_id
            if isinstance(summary, dict) and summary.get("team_id") is not None and not isinstance(summary.get("team_id"), str):
                summary["team_id"] = str(summary.get("team_id"))
                basic_cache.set(cache_key_summary, summary, ttl=180)

        # Full profile (richer fields). Cached separately to avoid heavier fetch if only summary needed elsewhere.
        profile = basic_cache.get(cache_key_profile)
        if profile is None:
            try:
                full_info = await get_player_info(player_id, resolved_sport, basic_only=False)
                if isinstance(full_info, dict):
                    team_full = full_info.get("team") or {}
                    profile = {
                        "height": full_info.get("height"),
                        "weight": full_info.get("weight"),
                        "jersey_number": full_info.get("jersey_number"),
                        "college": full_info.get("college"),
                        "country": full_info.get("country"),
                        "draft_year": full_info.get("draft_year"),
                        "draft_round": full_info.get("draft_round"),
                        "draft_number": full_info.get("draft_number"),
                        "team_conference": team_full.get("conference"),
                        "team_division": team_full.get("division"),
                        "team_city": team_full.get("city"),
                        "team_full_name": team_full.get("full_name") or team_full.get("name"),
                    }
                else:
                    profile = None
            except Exception as e:
                logger.warning("Failed fetching full profile", extra={"player_id": player_id, "error": str(e)})
                profile = None
            basic_cache.set(cache_key_profile, profile, ttl=600)

        # Base stats group
        stats = stats_cache.get(cache_key_stats)
        if stats is None:
            raw_stats = None
            try:
                raw_stats_list = await get_player_stats(player_id, resolved_sport, season=normalized_season)
                raw_stats = (raw_stats_list[0] if isinstance(raw_stats_list, list) and raw_stats_list else None)
            except Exception as e:
                logger.warning("Failed fetching stats", extra={"player_id": player_id, "sport": resolved_sport, "season": season, "normalized": normalized_season, "error": str(e)})
            stats = normalize_season_average(raw_stats) if raw_stats else None
            stats_cache.set(cache_key_stats, stats, ttl=300)

        percentiles = percentile_cache.get(cache_key_pct)
        if percentiles is None and stats:
            # We use the raw key version for percentile calculation; reconstruct raw-like dict subset
            try:
                # Rebuild a dict mapping back to raw keys for percentile service compatibility
                reverse_map = {v: k for k, v in {'min': 'minutes_per_game','pts':'points_per_game','ast':'assists_per_game','reb':'rebounds_per_game','stl':'steals_per_game','blk':'blocks_per_game','fg_pct':'field_goal_percentage','fg3_pct':'three_point_percentage','ft_pct':'free_throw_percentage','turnover':'turnovers_per_game'}.items()}
                raw_like = {reverse_map.get(k, k): v for k, v in stats.items()}
                raw_percentiles = await stats_percentile_service.calculate_percentiles(raw_like, resolved_sport, normalized_season)
                percentiles = remap_percentile_keys(raw_percentiles)
            except Exception as e:
                logger.warning("Percentile calculation failed", extra={"player_id": player_id, "sport": resolved_sport, "season": season, "normalized": normalized_season, "error": str(e)})
                percentiles = None
            percentile_cache.set(cache_key_pct, percentiles, ttl=1800)

        # Shooting stats group (placeholder retrieval; actual upstream already available in service layer)
        shooting_stats = stats_cache.get(cache_key_shooting_stats)
        if shooting_stats is None:
            try:
                from app.services.balldontlie_api import get_player_shooting_stats
                shooting_raw = await get_player_shooting_stats(player_id, resolved_sport, season=normalized_season)
                # shooting_raw format: {'data': [...]} or list; Keep as-is under stats for now
                shooting_stats = shooting_raw.get('data')[0] if isinstance(shooting_raw, dict) and shooting_raw.get('data') else shooting_raw
            except Exception as e:
                logger.warning("Shooting stats fetch failed", extra={"player_id": player_id, "sport": resolved_sport, "error": str(e)})
                shooting_stats = None
            stats_cache.set(cache_key_shooting_stats, shooting_stats, ttl=600)

        shooting_percentiles = percentile_cache.get(cache_key_shooting_pct)
        if shooting_percentiles is None and shooting_stats and isinstance(shooting_stats, dict):
            try:
                shooting_numeric = shooting_stats.get('stats') if 'stats' in shooting_stats else shooting_stats
                if isinstance(shooting_numeric, dict):
                    raw_shooting_percentiles = await stats_percentile_service.calculate_percentiles(shooting_numeric, resolved_sport, normalized_season)
                    shooting_percentiles = raw_shooting_percentiles  # keys already descriptive
                else:
                    shooting_percentiles = None
            except Exception as e:
                logger.warning("Shooting percentile calc failed", extra={"player_id": player_id, "sport": resolved_sport, "error": str(e)})
                shooting_percentiles = None
            percentile_cache.set(cache_key_shooting_pct, shooting_percentiles, ttl=1800)

        # Mentions (optional, no caching for now—RSS ttl would be separate if added)
        mentions = None
        if include_mentions:
            try:
                rss = await get_entity_mentions("player", player_id, resolved_sport)
                mentions = rss or []
            except Exception as e:
                logger.warning("Mentions fetch failed", extra={"player_id": player_id, "sport": resolved_sport, "error": str(e)})
                mentions = []

        # Build metrics groups collection
        metrics_groups = {}
        if stats:
            metrics_groups['base'] = build_metrics_group('base', stats, percentiles)
        if shooting_stats:
            metrics_groups['shooting'] = build_metrics_group('shooting', shooting_stats, shooting_percentiles)

        # NFL-specific advanced groups (only if sport is NFL)
        if resolved_sport == 'NFL':
            # Light mode: fetch single-player rows from advanced endpoints (raw only)
            from app.services.cache import stats_cache as _sc
            async def _fetch_adv(endpoint: str, cache_key: str):
                cached = _sc.get(cache_key)
                if cached is not None:
                    return cached
                import httpx
                headers = {"Authorization": f"Bearer {settings.BALLDONTLIE_API_KEY}"}
                url_base = "https://api.balldontlie.io/nfl/v1/advanced_stats"
                final_url = f"{url_base}/{endpoint}"
                params = {}
                if normalized_season:
                    params['season'] = normalized_season
                params['player_ids[]'] = player_id
                try:
                    async with httpx.AsyncClient(timeout=20.0) as client:
                        r = await client.get(final_url, headers=headers, params=params)
                        r.raise_for_status()
                        payload = r.json()
                        data_list = payload.get('data') if isinstance(payload, dict) else None
                        row = data_list[0] if data_list else None
                except Exception as e:
                    logger.warning("NFL advanced stats fetch failed", extra={"endpoint": endpoint, "player_id": player_id, "error": str(e)})
                    row = None
                _sc.set(cache_key, row, ttl=600)
                return row
            nfl_rushing = await _fetch_adv('rushing', cache_key_nfl_rushing)
            nfl_passing = await _fetch_adv('passing', cache_key_nfl_passing)
            nfl_receiving = await _fetch_adv('receiving', cache_key_nfl_receiving)
            # Build groups with percentiles = None and meta flag
            if nfl_rushing:
                g = build_metrics_group('nfl_rushing', nfl_rushing, None)
                g['meta'] = {'percentiles_available': False, 'mode': 'light'}
                metrics_groups['nfl_rushing'] = g
            if nfl_passing:
                g = build_metrics_group('nfl_passing', nfl_passing, None)
                g['meta'] = {'percentiles_available': False, 'mode': 'light'}
                metrics_groups['nfl_passing'] = g
            if nfl_receiving:
                g = build_metrics_group('nfl_receiving', nfl_receiving, None)
                g['meta'] = {'percentiles_available': False, 'mode': 'light'}
                metrics_groups['nfl_receiving'] = g

        # EPL player season stats (list of {name,value}) → flatten to map; light mode percentiles
        if resolved_sport == 'EPL':
            from app.services.cache import stats_cache as _sc
            from app.services.metrics_utils import epl_stats_list_to_map
            cached = _sc.get(cache_key_epl_player_stats)
            if cached is None:
                try:
                    from app.services.balldontlie_api import get_epl_player_season_stats
                    season_int = int(season) if season and str(season).isdigit() else None
                    payload = await get_epl_player_season_stats(player_id, season_int)
                    stats_list = payload.get('data') if isinstance(payload, dict) else None
                    cached = epl_stats_list_to_map(stats_list)
                except Exception as e:
                    logger.warning("EPL player season stats fetch failed", extra={"player_id": player_id, "error": str(e)})
                    cached = None
                _sc.set(cache_key_epl_player_stats, cached, ttl=900)
            if cached:
                g = build_metrics_group('epl_player_season_stats', cached, None)
                g['meta'] = {'percentiles_available': False, 'mode': 'light'}
                metrics_groups['epl_player_season_stats'] = g

        try:
            model_obj = PlayerFullResponse(
                summary=summary,
                season=season_key,
                stats=stats,  # back-compat
                percentiles=percentiles,  # back-compat
                mentions=mentions,
                profile=profile,
                metrics={'groups': metrics_groups}
            )
        except ValidationError as ve:
            logger.error("PlayerFullResponse validation failed", extra={
                "player_id": player_id,
                "errors": ve.errors(),
                "summary_keys": list(summary.keys()) if isinstance(summary, dict) else type(summary).__name__,
                "stats_type": type(stats).__name__,
                "percentiles_type": type(percentiles).__name__ if percentiles is not None else None
            })
            raise HTTPException(status_code=422, detail={"message": "PlayerFullResponse validation failed", "errors": ve.errors()})
        return model_obj
    except HTTPException:
        raise
    except Exception as e:
        # Log unexpected exception with contextual data, then raise 500
        logger.exception("Unhandled error building player full response", extra={
            "player_id": player_id,
            "sport": resolved_sport,
            "season": season,
            "normalized_season": normalized_season
        })
        raise HTTPException(status_code=500, detail="Failed to build full player response")

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