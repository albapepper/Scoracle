from fastapi import APIRouter, Depends, HTTPException, Path, Query
from typing import Optional, Dict, Any, List
import logging
from app.services.sports_context import get_sports_context
from app.services.google_rss import get_entity_mentions
from app.services.cache import basic_cache, stats_cache
from pydantic import BaseModel
from app.models.schemas import PlayerFullResponse
from app.services.metrics_utils import build_metrics_group
from pydantic import ValidationError

from app.core.config import settings
import httpx
router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/{player_id}")
async def get_player_details(
    player_id: str = Path(..., description="ID of the player to fetch"),
    season: Optional[str] = Query(None, description="Season to fetch stats for"),
    sport: Optional[str] = Query(None, description="Override sport type (NBA, NFL, FOOTBALL)"),
    sports_context = Depends(get_sports_context)
):
    """
    Get detailed player information and statistics.
    """
    # Get active sport from context
    # Determine sport precedence: explicit query param > context default
    sport = (sport or sports_context.get_active_sport() or "NBA").upper()
    
    try:
        from app.services.apisports import apisports_service
        if sport.upper() == "NBA":
            info = await apisports_service.get_basketball_player_basic(player_id)
            stats = await apisports_service.get_basketball_player_statistics(player_id, season)
            return {"player_id": player_id, "sport": sport, "season": season or "current", "info": info, "statistics": stats}
        elif sport.upper() == "EPL":
            info = await apisports_service.get_football_player_basic(player_id)
            return {"player_id": player_id, "sport": sport, "season": season or "current", "info": info, "statistics": None}
        else:
            raise HTTPException(status_code=501, detail=f"Player details not implemented for sport {sport.upper()}")
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
    sport: Optional[str] = Query(None, description="Override sport type (NBA, NFL, FOOTBALL)"),
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
    cache_key_shooting_stats = f"player:stats:shooting:{resolved_sport}:{player_id}:{season_key}"
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
            # Prefer API-Sports for NBA basic identity
            if resolved_sport == 'NBA':
                from app.services.apisports import apisports_service
                info = await apisports_service.get_basketball_player_basic(player_id)
            elif resolved_sport == 'EPL':
                from app.services.apisports import apisports_service
                info = await apisports_service.get_football_player_basic(player_id)
            else:
                raise HTTPException(status_code=501, detail=f"Player summary not implemented for sport {resolved_sport}")
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
            # Source hint no longer used (registry removed)
            basic_cache.set(cache_key_summary, summary, ttl=180)
        else:
            # Sanitize cached summary if earlier version stored int team_id
            if isinstance(summary, dict) and summary.get("team_id") is not None and not isinstance(summary.get("team_id"), str):
                summary["team_id"] = str(summary.get("team_id"))
                basic_cache.set(cache_key_summary, summary, ttl=180)

        # Full profile (richer fields). Cached separately to avoid heavier fetch if only summary needed elsewhere.
        profile = basic_cache.get(cache_key_profile)
        if profile is None:
            profile = None  # Rich profile mapping from API-Sports TBD
            basic_cache.set(cache_key_profile, profile, ttl=600)

        # Base stats group (API-Sports only for NBA; other sports keep current service until migrated)
        stats = stats_cache.get(cache_key_stats)
        if stats is None:
            raw_stats = None
            try:
                if resolved_sport == 'NBA':
                    from app.services.apisports import apisports_service
                    raw_stats = await apisports_service.get_basketball_player_statistics(player_id, normalized_season)
                    stats = raw_stats or None
                elif resolved_sport == 'EPL':
                    stats = None
                else:
                    raise HTTPException(status_code=501, detail=f"Stats not implemented for sport {resolved_sport}")
            except Exception as e:
                logger.warning("Failed fetching stats", extra={"player_id": player_id, "sport": resolved_sport, "season": season, "normalized": normalized_season, "error": str(e)})
                stats = None
            stats_cache.set(cache_key_stats, stats, ttl=300)

    # Percentiles removed (present raw stats only)
        shooting_stats = None
        

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
            metrics_groups['base'] = build_metrics_group('base', stats)

        # NFL support removed in balldontlie deprecation phase; can be reintroduced via API-Sports later

        # EPL player season stats (list of {name,value}) → flatten to map; light mode percentiles
        if resolved_sport == 'EPL':
            pass  # EPL player metrics groups TBD via API-Sports

        try:
            model_obj = PlayerFullResponse(
                summary=summary,
                season=season_key,
                stats=stats,
                percentiles=None,
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
                "percentiles_removed": True
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



"""
Legacy percentiles and NFL season stats endpoints were removed during migration away from balldontlie.
Percentiles will be reintroduced once cohorts are available for API-Sports payloads.
"""



@router.get("/{player_id}/seasons")
async def get_player_seasons(
    player_id: str = Path(..., description="ID of the player to fetch seasons for"),
    sport: Optional[str] = Query(None, description="Override sport type (NBA, NFL, FOOTBALL)"),
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