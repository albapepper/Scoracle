from fastapi import APIRouter, Depends, HTTPException, Query
from app.services.sports_context import get_sports_context

router = APIRouter()

@router.get("/")
async def get_home_info(sport: str = Query(None, description="Sport type (NBA, NFL, EPL)")):
    """
    Get home page information and configuration.
    """
    return {
        "sport": sport or "NBA",  # Default to NBA if no sport specified
        "available_sports": ["NBA", "NFL", "EPL"],
        "app_name": "Scoracle",
        "version": "0.1.0"
    }

@router.get("/search")
async def search_entities(
    query: str = Query(..., description="Search query for player or team name"),
    entity_type: str = Query(None, description="Type of entity: player or team"),
    sport: str = Query(None, description="Sport type (NBA, NFL, EPL)"),
    sports_context = Depends(get_sports_context)
):
    """
    Search for players or teams based on query string.
    """
    if not entity_type:
        entity_type = "player"  # Default to player search
    
    # Use sports context to determine the active sport if not specified
    active_sport = sport or sports_context.get_active_sport()
    
    # This would typically call a service to perform the search
    # For now, return a placeholder response
    return {
        "query": query,
        "entity_type": entity_type,
        "sport": active_sport,
        "results": []  # Will be populated by the actual search service
    }