from fastapi import APIRouter, Depends, HTTPException, Path, Query
from typing import Optional, Dict, Any, List
from fastapi import HTTPException
from app.services.apisports import apisports_service
from app.services.sports_context import get_sports_context
from app.services.google_rss import get_entity_mentions
from app.services.cache import basic_cache, stats_cache
from pydantic import BaseModel
from app.models.schemas import TeamFullResponse
from app.services.metrics_utils import build_metrics_group, epl_stats_list_to_map

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
    
    # Fetch team details and stats
    if sport == 'NBA':
        team_info = await apisports_service.get_basketball_team_basic(team_id)
        stats = await apisports_service.get_basketball_team_statistics(team_id, season)
    elif sport == 'EPL':
        team_info = await apisports_service.get_football_team_basic(team_id)
        stats = None
    else:
        raise HTTPException(status_code=501, detail=f"Team details not implemented for sport {sport}")
    
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
    """Aggregate endpoint returning summary + stats (+ mentions). Percentiles removed."""
    resolved_sport = (sport or sports_context.get_active_sport() or "NBA").upper()
    season_key = season or "current"
    cache_key_summary = f"team:summary:{resolved_sport}:{team_id}"
    cache_key_profile = f"team:profile:{resolved_sport}:{team_id}"
    cache_key_stats = f"team:stats:base:{resolved_sport}:{team_id}:{season_key}"
    cache_key_standings = f"team:stats:standings:{resolved_sport}:{team_id}:{season_key}"

    summary = basic_cache.get(cache_key_summary)
    if summary is None:
        # Prefer API-Sports for NBA basic identity
        if resolved_sport == 'NBA':
            info = await apisports_service.get_basketball_team_basic(team_id)
        elif resolved_sport == 'EPL':
            info = await apisports_service.get_football_team_basic(team_id)
        else:
            raise HTTPException(status_code=501, detail=f"Team summary not implemented for sport {resolved_sport}")
        summary = {
            "id": str(info.get("id")),
            "sport": resolved_sport,
            "name": info.get("name"),
            "abbreviation": info.get("abbreviation"),
            "city": info.get("city"),
            "conference": info.get("conference"),
            "division": info.get("division"),
        }
        if isinstance(info, dict) and info.get("fallback_source"):
            summary["source"] = info.get("fallback_source")
        basic_cache.set(cache_key_summary, summary, ttl=300)

    # Full profile (richer fields)
    profile = basic_cache.get(cache_key_profile)
    if profile is None:
        profile = None
        basic_cache.set(cache_key_profile, profile, ttl=600)

    stats = stats_cache.get(cache_key_stats)
    if stats is None:
        try:
            if resolved_sport == 'NBA':
                stats = await apisports_service.get_basketball_team_statistics(team_id, season)
            elif resolved_sport == 'EPL':
                stats = None
            else:
                raise HTTPException(status_code=501, detail=f"Team stats not implemented for sport {resolved_sport}")
        except Exception:
            stats = None
        stats_cache.set(cache_key_stats, stats, ttl=300)

    # Percentiles removed

    # Standings group
    standings_entry = stats_cache.get(cache_key_standings)
    if standings_entry is None:
        try:
            if resolved_sport == 'NBA':
                standings_payload = await apisports_service.get_basketball_standings(season)
            else:
                standings_payload = None
            # Attempt to find this team in the standings payload (shape differs per provider)
            found = None
            def try_extract_list(payload):
                if not isinstance(payload, dict):
                    return None
                # API-Sports: response -> [ { league: { standings: [[...]] } } ]
                # But some sports return {response:[...]}
                if 'response' in payload and isinstance(payload['response'], list):
                    return payload['response']
                if 'data' in payload and isinstance(payload['data'], list):
                    return payload['data']
                return None
            lst = try_extract_list(standings_payload)
            if isinstance(lst, list):
                # Try nested standings arrays
                for item in lst:
                    league = item.get('league') if isinstance(item, dict) else None
                    standings = None
                    if league and isinstance(league, dict):
                        standings = league.get('standings')
                    if isinstance(standings, list):
                        # API-Sports returns list of groups; pick the first group list
                        grp = standings[0] if standings and isinstance(standings[0], list) else standings
                        for row in grp:
                            tid = (row.get('team') or {}).get('id') if isinstance(row, dict) else None
                            if str(tid) == str(team_id):
                                found = row
                                break
                        if found:
                            break
                # Fallback flat list
                if not found:
                    for d in lst:
                        team_obj = (d.get('team') or {}) if isinstance(d, dict) else {}
                        if str(team_obj.get('id')) == str(team_id):
                            found = d
                            break
            standings_entry = found
        except Exception:
            standings_entry = None
        stats_cache.set(cache_key_standings, standings_entry, ttl=600)

    standings_percentiles = None  # Backward compatibility placeholder

    # EPL metrics groups TBD via API-Sports
    epl_team_stats_group = None

    mentions = None
    if include_mentions:
        try:
            rss = await get_entity_mentions("team", team_id, resolved_sport)
            mentions = rss or []
        except Exception:
            mentions = []

    metrics_groups = {}
    if stats:
        metrics_groups['base'] = build_metrics_group('base', stats)
    if standings_entry:
        metrics_groups['standings'] = build_metrics_group('standings', standings_entry)
    if epl_team_stats_group:
        # We keep meta to indicate absence of percentiles
        g = build_metrics_group('epl_team_season_stats', epl_team_stats_group)
        g['meta'] = {'percentiles_available': False, 'mode': 'raw'}
        metrics_groups['epl_team_season_stats'] = g

    return {
        "summary": summary,
        "season": season_key,
        "stats": stats,
    "percentiles": None,
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

# Removed legacy sport-specific team endpoints tied to balldontlie; prefer sport-first routes in app/api/sport.py

@router.get("/nba/standings")
async def get_nba_standings_legacy_proxy(season: Optional[int] = Query(None, description="Season to fetch standings for (year)")):
    """Temporary legacy route to fetch NBA standings via API-Sports. Prefer sport-first routes."""
    return await apisports_service.get_basketball_standings(season)


