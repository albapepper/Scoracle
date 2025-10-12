from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response
from typing import Dict, Optional, List, Any
from pydantic import BaseModel, Field
from app.services.google_rss import get_entity_mentions
from app.services.balldontlie_api import get_player_info, get_team_info, get_players, get_teams
from app.models.schemas import PlayerBase, TeamBase, MentionsResponse

router = APIRouter()

@router.get("/sport/{sport}/players")
async def get_sport_players(
    sport: str = Path(..., description="Sport type (NBA, NFL, EPL)"),
    page: int = Query(1, description="Page number for pagination"),
    per_page: int = Query(25, description="Number of results per page")
):
    """
    Get players for a specific sport.
    Returns a list of players based on the sport.
    """
    try:
        # Set up pagination parameters
        params = {"page": page, "per_page": per_page}
        players_data = await get_players(sport, params)
        return players_data
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching players: {str(e)}")

@router.get("/sport/{sport}/teams")
async def get_sport_teams(
    sport: str = Path(..., description="Sport type (NBA, NFL, EPL)")
):
    """
    Get teams for a specific sport.
    Returns a list of teams based on the sport.
    """
    try:
        teams_data = await get_teams(sport)
        return teams_data
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching teams: {str(e)}")

@router.get("/mentions/{entity_type}/{entity_id}", response_model=MentionsResponse)
async def get_mentions(
    response: Response,
    entity_type: str = Path(..., description="Type of entity: player or team"),
    entity_id: str = Path(..., description="ID of the entity to fetch mentions for"),
    sport: str = Query(None, description="Sport type (NBA, NFL, EPL)")
):
    """
    Get mentions and basic information for a player or team.
    Returns RSS feed results and basic entity information.
    """
    if entity_type not in ["player", "team"]:
        raise HTTPException(status_code=400, detail="Entity type must be 'player' or 'team'")
    
    # Get mentions from RSS service (empty list acceptable)
    sport = sport or "NBA"
    mentions = await get_entity_mentions(entity_type, entity_id, sport) or []

    entity_info = None
    missing_entity = False
    try:
        if entity_type == "player":
            entity_info = await get_player_info(entity_id, sport, basic_only=True)
        else:
            entity_info = await get_team_info(entity_id, sport, basic_only=True)
        # If fallback marker present, set response header
        if isinstance(entity_info, dict) and entity_info.get("fallback_source"):
            response.headers["X-Entity-Source"] = entity_info["fallback_source"]
        # Guarantee id presence in response entity_info
        if isinstance(entity_info, dict):
            entity_info.setdefault("id", int(entity_id) if str(entity_id).isdigit() else entity_id)
    except ValueError:
        missing_entity = True
    except Exception as e:
        print(f"entity_info fetch failed: {e}")
        missing_entity = True

    # If missing entity, still return a minimal entity_info with id to prevent downstream KeyErrors
    safe_entity_info = entity_info
    if missing_entity and not isinstance(entity_info, dict):
        safe_entity_info = {"id": int(entity_id) if str(entity_id).isdigit() else entity_id}

    return MentionsResponse(
        entity_type=entity_type,
        entity_id=entity_id,
        sport=sport,
        entity_info=safe_entity_info,
        mentions=mentions,
        missing_entity=missing_entity
    )