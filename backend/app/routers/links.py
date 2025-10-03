from fastapi import APIRouter, HTTPException, Path, Query
from typing import List, Optional
from app.services.google_rss import get_related_links

router = APIRouter()

@router.get("/links/{entity_type}/{entity_id}")
async def get_entity_links(
    entity_type: str = Path(..., description="Type of entity: player or team"),
    entity_id: str = Path(..., description="ID of the entity to fetch links for"),
    category: Optional[str] = Query(None, description="Category of links to fetch"),
    limit: int = Query(10, description="Maximum number of links to return"),
):
    """
    Get related links for a player or team, optionally filtered by category.
    Categories might include news, statistics, social media, etc.
    """
    if entity_type not in ["player", "team"]:
        raise HTTPException(status_code=400, detail="Entity type must be 'player' or 'team'")
    
    # Get related links from service
    links = await get_related_links(entity_type, entity_id, category, limit)
    
    return {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "category": category,
        "links": links
    }