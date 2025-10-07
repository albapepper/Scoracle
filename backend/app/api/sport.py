from fastapi import APIRouter, Path, Query, HTTPException
from app.adapters.balldontlie_api import get_player_info, get_player_stats, get_team_info, get_team_stats
from app.adapters.google_rss import get_entity_mentions

router = APIRouter()

@router.get("/{sport}/players/{player_id}")
async def sport_player_summary(sport: str, player_id: str):
    info = await get_player_info(player_id, sport, basic_only=True)
    return {"summary": info, "sport": sport.upper(), "id": player_id}

@router.get("/{sport}/players/{player_id}/stats")
async def sport_player_stats(sport: str, player_id: str, season: str | None = Query(None)):
    stats = await get_player_stats(player_id, sport, season=season)
    return {"player_id": player_id, "sport": sport.upper(), "season": season or "current", "stats": stats}

@router.get("/{sport}/players/{player_id}/mentions")
async def sport_player_mentions(sport: str, player_id: str):
    mentions = await get_entity_mentions("player", player_id, sport)
    return {"player_id": player_id, "sport": sport.upper(), "mentions": mentions}

@router.get("/{sport}/teams/{team_id}")
async def sport_team_summary(sport: str, team_id: str):
    info = await get_team_info(team_id, sport, basic_only=True)
    return {"summary": info, "sport": sport.upper(), "id": team_id}

@router.get("/{sport}/teams/{team_id}/stats")
async def sport_team_stats(sport: str, team_id: str, season: str | None = Query(None)):
    stats = await get_team_stats(team_id, sport, season=season)
    return {"team_id": team_id, "sport": sport.upper(), "season": season or "current", "stats": stats}

@router.get("/{sport}/teams/{team_id}/mentions")
async def sport_team_mentions(sport: str, team_id: str):
    mentions = await get_entity_mentions("team", team_id, sport)
    return {"team_id": team_id, "sport": sport.upper(), "mentions": mentions}
