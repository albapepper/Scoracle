from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response
from typing import Dict, Optional, List, Any
from pydantic import BaseModel, Field
from app.services.google_rss import get_entity_mentions
from app.models.schemas import PlayerBase, TeamBase, MentionsResponse

router = APIRouter()

"""
Note: legacy /sport/{sport}/players and /sport/{sport}/teams endpoints using balldontlie were removed
to standardize on API-Sports and sport-first routes under app/api/sport.py
"""

@router.get("/mentions/{entity_type}/{entity_id}", response_model=MentionsResponse)
async def get_mentions(
    response: Response,
    entity_type: str = Path(..., description="Type of entity: player or team"),
    entity_id: str = Path(..., description="ID of the entity to fetch mentions for"),
    sport: str = Query(None, description="Sport type (NBA, NFL, FOOTBALL)")
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
            if sport.upper() == 'NBA':
                try:
                    from app.services.apisports import apisports_service
                    entity_info = await apisports_service.get_basketball_player_basic(entity_id)
                except Exception:
                    entity_info = None
            else:
                if sport.upper() == 'EPL':
                    from app.services.apisports import apisports_service
                    entity_info = await apisports_service.get_football_player_basic(entity_id)
                else:
                    entity_info = None
        else:
            if sport.upper() == 'NBA':
                try:
                    from app.services.apisports import apisports_service
                    entity_info = await apisports_service.get_basketball_team_basic(entity_id)
                except Exception:
                    entity_info = None
            else:
                if sport.upper() == 'EPL':
                    from app.services.apisports import apisports_service
                    entity_info = await apisports_service.get_football_team_basic(entity_id)
                else:
                    entity_info = None
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