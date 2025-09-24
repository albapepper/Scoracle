from fastapi import APIRouter, Depends, HTTPException, Path, Query
from app.services.google_rss import get_entity_mentions
from app.services.balldontlie_api import get_player_info, get_team_info

router = APIRouter()

@router.get("/{entity_type}/{entity_id}")
async def get_mentions(
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
    
    # Get mentions from RSS service
    mentions = await get_entity_mentions(entity_type, entity_id, sport)
    
    # Get basic entity info from the appropriate API
    if entity_type == "player":
        entity_info = await get_player_info(entity_id, sport, basic_only=True)
    else:
        entity_info = await get_team_info(entity_id, sport, basic_only=True)
    
    return {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "sport": sport,
        "entity_info": entity_info,
        "mentions": mentions
    }