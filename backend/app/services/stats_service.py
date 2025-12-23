"""
Stats Service - API-Sports statistics data fetching.

Fetches statistical data from sport-specific API-Sports endpoints
and transforms them into a unified format for the StatsCard component.

Endpoints used:
- Football Player: GET https://v3.football.api-sports.io/players?id={id}&season={season}
- Football Team: GET https://v3.football.api-sports.io/teams/statistics?league={league_id}&season={season}&team={id}
- NFL Player: GET https://v1.american-football.api-sports.io/players/statistics?id={id}&season={season}
- NFL Team: GET https://v1.american-football.api-sports.io/standings?league=1&season={season}&team={id}
- NBA Player: GET https://v2.nba.api-sports.io/players/statistics?id={id}&season={season}
- NBA Team: GET https://v2.nba.api-sports.io/teams/statistics?id={id}&season={season}
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
from fastapi import HTTPException

from app.config import settings
from app.services.cache import widget_cache
from app.services.singleflight import singleflight
from app.database.local_dbs import get_team_by_id

logger = logging.getLogger(__name__)

# Cache TTL: 6 hours (stats update during/after games)
STATS_CACHE_TTL = 6 * 60 * 60


def _get_default_season(sport: str) -> str:
    """Get the default (most recent) season for a sport."""
    current_year = datetime.now().year
    sport_upper = sport.upper()
    
    # Football (soccer) seasons span two years (e.g., 2024-2025 season = "2024")
    # NBA seasons also span two years (e.g., 2024-2025 season = "2024")
    # NFL seasons are single year
    if sport_upper == "FOOTBALL":
        # If we're in the first half of the year, use previous year's season
        if datetime.now().month <= 6:
            return str(current_year - 1)
        return str(current_year)
    elif sport_upper == "NBA":
        # NBA season starts in October, so if before October use previous year
        if datetime.now().month < 10:
            return str(current_year - 1)
        return str(current_year)
    elif sport_upper == "NFL":
        # NFL season runs Sept-Feb, so if Jan-Feb use previous year
        if datetime.now().month <= 2:
            return str(current_year - 1)
        return str(current_year)
    
    return str(current_year)


def _get_headers() -> Dict[str, str]:
    """Get API-Sports authentication headers."""
    if not settings.API_SPORTS_KEY:
        raise HTTPException(status_code=502, detail="API-Sports key not configured on server")
    return {"x-apisports-key": settings.API_SPORTS_KEY}


def _get_base_url(sport: str) -> str:
    """Get base URL for sport-specific API-Sports endpoint."""
    sport_upper = sport.upper()
    if sport_upper == "FOOTBALL":
        return "https://v3.football.api-sports.io"
    elif sport_upper == "NBA":
        return "https://v2.nba.api-sports.io"
    elif sport_upper == "NFL":
        return "https://v1.american-football.api-sports.io"
    raise HTTPException(status_code=400, detail=f"Unknown sport: {sport}")


# =============================================================================
# FOOTBALL (Soccer) Stats Transformers
# =============================================================================

def _transform_football_team_stats(data: Dict[str, Any]) -> List[Dict[str, str]]:
    """Transform Football team statistics response to flat stat list."""
    stats = []
    
    # Basic info
    fixtures = data.get("fixtures", {})
    played = fixtures.get("played", {})
    wins = fixtures.get("wins", {})
    draws = fixtures.get("draws", {})
    loses = fixtures.get("loses", {})
    
    stats.append({"label": "Matches Played", "value": str(played.get("total", "-"))})
    stats.append({"label": "Wins", "value": str(wins.get("total", "-"))})
    stats.append({"label": "Draws", "value": str(draws.get("total", "-"))})
    stats.append({"label": "Losses", "value": str(loses.get("total", "-"))})
    
    # Goals
    goals = data.get("goals", {})
    goals_for = goals.get("for", {})
    goals_against = goals.get("against", {})
    
    stats.append({"label": "Goals Scored", "value": str(goals_for.get("total", {}).get("total", "-"))})
    stats.append({"label": "Goals Conceded", "value": str(goals_against.get("total", {}).get("total", "-"))})
    stats.append({"label": "Goals per Game", "value": str(goals_for.get("average", {}).get("total", "-"))})
    
    # Clean sheets
    clean_sheet = data.get("clean_sheet", {})
    stats.append({"label": "Clean Sheets", "value": str(clean_sheet.get("total", "-"))})
    
    # Penalty
    penalty = data.get("penalty", {})
    stats.append({"label": "Penalties Scored", "value": str(penalty.get("scored", {}).get("total", "-"))})
    
    return stats


def _transform_football_player_stats(data: Dict[str, Any]) -> List[Dict[str, str]]:
    """Transform Football player response to flat stat list."""
    stats = []
    
    # Get statistics array (contains stats per competition)
    statistics = data.get("statistics", [])
    if not statistics:
        return stats
    
    # Aggregate across all competitions
    total_games = 0
    total_goals = 0
    total_assists = 0
    total_shots = 0
    total_passes = 0
    total_tackles = 0
    total_yellow = 0
    total_red = 0
    
    for stat in statistics:
        games = stat.get("games", {})
        total_games += games.get("appearences", 0) or 0
        
        goals_data = stat.get("goals", {})
        total_goals += goals_data.get("total", 0) or 0
        total_assists += goals_data.get("assists", 0) or 0
        
        shots = stat.get("shots", {})
        total_shots += shots.get("total", 0) or 0
        
        passes = stat.get("passes", {})
        total_passes += passes.get("total", 0) or 0
        
        tackles = stat.get("tackles", {})
        total_tackles += tackles.get("total", 0) or 0
        
        cards = stat.get("cards", {})
        total_yellow += cards.get("yellow", 0) or 0
        total_red += cards.get("red", 0) or 0
    
    stats.append({"label": "Appearances", "value": str(total_games)})
    stats.append({"label": "Goals", "value": str(total_goals)})
    stats.append({"label": "Assists", "value": str(total_assists)})
    stats.append({"label": "Shots", "value": str(total_shots)})
    stats.append({"label": "Passes", "value": str(total_passes)})
    stats.append({"label": "Tackles", "value": str(total_tackles)})
    stats.append({"label": "Yellow Cards", "value": str(total_yellow)})
    stats.append({"label": "Red Cards", "value": str(total_red)})
    
    return stats


# =============================================================================
# NFL Stats Transformers
# =============================================================================

def _transform_nfl_team_stats(data: Dict[str, Any]) -> List[Dict[str, str]]:
    """Transform NFL team standings response to flat stat list."""
    stats = []
    
    # NFL standings endpoint returns different structure
    stats.append({"label": "Wins", "value": str(data.get("won", "-"))})
    stats.append({"label": "Losses", "value": str(data.get("lost", "-"))})
    stats.append({"label": "Ties", "value": str(data.get("ties", "-"))})
    
    # Points
    points = data.get("points", {})
    stats.append({"label": "Points For", "value": str(points.get("for", "-"))})
    stats.append({"label": "Points Against", "value": str(points.get("against", "-"))})
    
    # Records
    records = data.get("records", {})
    stats.append({"label": "Home Record", "value": str(records.get("home", "-"))})
    stats.append({"label": "Away Record", "value": str(records.get("road", "-"))})
    stats.append({"label": "Division Record", "value": str(records.get("division", "-"))})
    stats.append({"label": "Conference Record", "value": str(records.get("conference", "-"))})
    
    # Streak
    streak = data.get("streak", "-")
    stats.append({"label": "Current Streak", "value": str(streak)})
    
    return stats


def _transform_nfl_player_stats(data: Dict[str, Any]) -> List[Dict[str, str]]:
    """Transform NFL player statistics response to flat stat list."""
    stats = []
    
    # NFL player stats structure
    teams = data.get("teams", [])
    if not teams:
        return stats
    
    # Get first team's stats (most recent/current)
    team_stats = teams[0] if teams else {}
    groups = team_stats.get("groups", [])
    
    # Flatten all stat groups
    for group in groups:
        group_name = group.get("name", "")
        statistics = group.get("statistics", [])
        
        for stat in statistics:
            label = stat.get("name", "")
            value = stat.get("value", "-")
            if label and value is not None:
                # Format label nicely
                formatted_label = label.replace("_", " ").title()
                stats.append({"label": formatted_label, "value": str(value)})
    
    # Limit to most relevant stats (first 10)
    return stats[:10] if len(stats) > 10 else stats


# =============================================================================
# NBA Stats Transformers
# =============================================================================

def _transform_nba_team_stats(data: Dict[str, Any]) -> List[Dict[str, str]]:
    """Transform NBA team statistics response to flat stat list."""
    stats = []
    
    # Check if data is a list (API returns array) or dict
    if isinstance(data, list) and data:
        data = data[0]
    
    stats.append({"label": "Games Played", "value": str(data.get("games", "-"))})
    stats.append({"label": "Points", "value": str(data.get("points", "-"))})
    stats.append({"label": "Field Goals Made", "value": str(data.get("fgm", "-"))})
    stats.append({"label": "Field Goals Attempted", "value": str(data.get("fga", "-"))})
    stats.append({"label": "FG%", "value": str(data.get("fgp", "-"))})
    stats.append({"label": "3PT Made", "value": str(data.get("tpm", "-"))})
    stats.append({"label": "3PT%", "value": str(data.get("tpp", "-"))})
    stats.append({"label": "Free Throws Made", "value": str(data.get("ftm", "-"))})
    stats.append({"label": "FT%", "value": str(data.get("ftp", "-"))})
    stats.append({"label": "Rebounds", "value": str(data.get("totReb", "-"))})
    stats.append({"label": "Assists", "value": str(data.get("assists", "-"))})
    stats.append({"label": "Steals", "value": str(data.get("steals", "-"))})
    stats.append({"label": "Blocks", "value": str(data.get("blocks", "-"))})
    stats.append({"label": "Turnovers", "value": str(data.get("turnovers", "-"))})
    
    return stats


def _transform_nba_player_stats(data: Dict[str, Any]) -> List[Dict[str, str]]:
    """Transform NBA player statistics response to flat stat list."""
    stats = []
    
    # Check if data is a list
    if isinstance(data, list) and data:
        data = data[0]
    
    stats.append({"label": "Games Played", "value": str(data.get("games", "-"))})
    stats.append({"label": "Points", "value": str(data.get("points", "-"))})
    stats.append({"label": "Minutes", "value": str(data.get("min", "-"))})
    stats.append({"label": "Field Goals Made", "value": str(data.get("fgm", "-"))})
    stats.append({"label": "FG%", "value": str(data.get("fgp", "-"))})
    stats.append({"label": "3PT Made", "value": str(data.get("tpm", "-"))})
    stats.append({"label": "3PT%", "value": str(data.get("tpp", "-"))})
    stats.append({"label": "Free Throws Made", "value": str(data.get("ftm", "-"))})
    stats.append({"label": "FT%", "value": str(data.get("ftp", "-"))})
    stats.append({"label": "Rebounds", "value": str(data.get("totReb", "-"))})
    stats.append({"label": "Assists", "value": str(data.get("assists", "-"))})
    stats.append({"label": "Steals", "value": str(data.get("steals", "-"))})
    stats.append({"label": "Blocks", "value": str(data.get("blocks", "-"))})
    stats.append({"label": "Turnovers", "value": str(data.get("turnovers", "-"))})
    
    return stats


# =============================================================================
# Main Service Functions
# =============================================================================

async def get_team_stats(
    team_id: str,
    sport: str,
    season: Optional[str] = None,
    league_id: Optional[int] = None,
    *,
    client: httpx.AsyncClient | None = None
) -> Optional[Dict[str, Any]]:
    """
    Fetch team statistics from API-Sports.

    Args:
        team_id: Team ID
        sport: Sport code (FOOTBALL, NBA, NFL)
        season: Season year (defaults to most recent)
        league_id: League ID (required for FOOTBALL, optional for NFL)
        client: Optional HTTP client for connection reuse

    Returns:
        Dict with "stats" list and "season" in format:
        {
            "season": "2024",
            "stats": [{"label": "...", "value": "..."}, ...]
        }
        Returns None if stats not found.
    """
    sport_upper = sport.upper()
    season = season or _get_default_season(sport_upper)
    
    # For Football teams, we need league_id - try to get from DB if not provided
    if sport_upper == "FOOTBALL" and league_id is None:
        team_info = get_team_by_id("FOOTBALL", int(team_id))
        if team_info:
            league_id = team_info.get("league_id")
        if league_id is None:
            logger.warning(f"No league_id for Football team {team_id}, defaulting to Premier League (39)")
            league_id = 39  # Default to Premier League
    
    # NFL always uses league 1
    if sport_upper == "NFL":
        league_id = 1
    
    cache_key = f"stats:team:{sport_upper}:{team_id}:{season}"
    if league_id:
        cache_key += f":{league_id}"

    cached = widget_cache.get(cache_key)
    if cached is not None:
        logger.debug(f"Cache HIT: {cache_key}")
        return cached

    async def _work() -> Optional[Dict[str, Any]]:
        # Double-check cache after singleflight wait
        cached2 = widget_cache.get(cache_key)
        if cached2 is not None:
            return cached2

        # Fetch from API-Sports
        base = _get_base_url(sport_upper)
        headers = _get_headers()
        
        # Build endpoint and params based on sport
        if sport_upper == "FOOTBALL":
            # Football: /teams/statistics?league={league_id}&season={season}&team={id}
            endpoint = f"{base}/teams/statistics"
            params = {"team": team_id, "season": season, "league": league_id}
        elif sport_upper == "NFL":
            # NFL: /standings?league=1&season={season}&team={id}
            endpoint = f"{base}/standings"
            params = {"team": team_id, "season": season, "league": 1}
        elif sport_upper == "NBA":
            # NBA: /teams/statistics?id={id}&season={season}
            endpoint = f"{base}/teams/statistics"
            params = {"id": team_id, "season": season}
        else:
            return None

        try:
            if client is None:
                async with httpx.AsyncClient(timeout=15.0) as tmp:
                    resp = await tmp.get(endpoint, headers=headers, params=params)
                    resp.raise_for_status()
                    data = resp.json()
            else:
                resp = await client.get(endpoint, headers=headers, params=params)
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch team stats {team_id} ({sport_upper}): {e}")
            return None

        # Extract response
        response_data = data.get("response", {})
        if not response_data:
            logger.warning(f"No stats found for team {team_id} ({sport_upper})")
            return None

        # Handle NFL which returns array in response
        if sport_upper == "NFL" and isinstance(response_data, list):
            if not response_data:
                return None
            response_data = response_data[0]

        # Transform based on sport
        if sport_upper == "FOOTBALL":
            stats_list = _transform_football_team_stats(response_data)
        elif sport_upper == "NFL":
            stats_list = _transform_nfl_team_stats(response_data)
        elif sport_upper == "NBA":
            stats_list = _transform_nba_team_stats(response_data)
        else:
            stats_list = []

        result = {"season": season, "stats": stats_list}

        # Cache and return
        widget_cache.set(cache_key, result, ttl=STATS_CACHE_TTL)
        logger.info(f"Cache SET: {cache_key}")
        return result

    try:
        return await singleflight.do(cache_key, _work)
    except Exception as e:
        logger.error(f"Failed to fetch team stats: {e}")
        return None


async def get_player_stats(
    player_id: str,
    sport: str,
    season: Optional[str] = None,
    *,
    client: httpx.AsyncClient | None = None
) -> Optional[Dict[str, Any]]:
    """
    Fetch player statistics from API-Sports.

    Args:
        player_id: Player ID
        sport: Sport code (FOOTBALL, NBA, NFL)
        season: Season year (defaults to most recent)
        client: Optional HTTP client for connection reuse

    Returns:
        Dict with "stats" list and "season" in format:
        {
            "season": "2024",
            "stats": [{"label": "...", "value": "..."}, ...]
        }
        Returns None if stats not found.
    """
    sport_upper = sport.upper()
    season = season or _get_default_season(sport_upper)
    
    cache_key = f"stats:player:{sport_upper}:{player_id}:{season}"

    cached = widget_cache.get(cache_key)
    if cached is not None:
        logger.debug(f"Cache HIT: {cache_key}")
        return cached

    async def _work() -> Optional[Dict[str, Any]]:
        # Double-check cache after singleflight wait
        cached2 = widget_cache.get(cache_key)
        if cached2 is not None:
            return cached2

        # Fetch from API-Sports
        base = _get_base_url(sport_upper)
        headers = _get_headers()
        
        # Build endpoint and params based on sport
        if sport_upper == "FOOTBALL":
            # Football: /players?id={id}&season={season}
            endpoint = f"{base}/players"
            params = {"id": player_id, "season": season}
        elif sport_upper == "NFL":
            # NFL: /players/statistics?id={id}&season={season}
            endpoint = f"{base}/players/statistics"
            params = {"id": player_id, "season": season}
        elif sport_upper == "NBA":
            # NBA: /players/statistics?id={id}&season={season}
            endpoint = f"{base}/players/statistics"
            params = {"id": player_id, "season": season}
        else:
            return None

        try:
            if client is None:
                async with httpx.AsyncClient(timeout=15.0) as tmp:
                    resp = await tmp.get(endpoint, headers=headers, params=params)
                    resp.raise_for_status()
                    data = resp.json()
            else:
                resp = await client.get(endpoint, headers=headers, params=params)
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch player stats {player_id} ({sport_upper}): {e}")
            return None

        # Extract response
        response_list = data.get("response", [])
        if not response_list:
            logger.warning(f"No stats found for player {player_id} ({sport_upper})")
            return None

        # Get first item
        response_data = response_list[0] if isinstance(response_list, list) else response_list

        # Transform based on sport
        if sport_upper == "FOOTBALL":
            stats_list = _transform_football_player_stats(response_data)
        elif sport_upper == "NFL":
            stats_list = _transform_nfl_player_stats(response_data)
        elif sport_upper == "NBA":
            stats_list = _transform_nba_player_stats(response_data)
        else:
            stats_list = []

        result = {"season": season, "stats": stats_list}

        # Cache and return
        widget_cache.set(cache_key, result, ttl=STATS_CACHE_TTL)
        logger.info(f"Cache SET: {cache_key}")
        return result

    try:
        return await singleflight.do(cache_key, _work)
    except Exception as e:
        logger.error(f"Failed to fetch player stats: {e}")
        return None
