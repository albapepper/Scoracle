from fastapi import APIRouter, Depends, HTTPException, Query
from app.services.sports_context import get_sports_context
from app.services.balldontlie_api import balldontlie_service
import httpx

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
    sports_context = Depends(get_sports_context),
):
    """
    Search for players or teams based on query string.
    """
    if not entity_type:
        entity_type = "player"  # Default to player search
    
    # Use sports context to determine the active sport if not specified
    active_sport = sport or sports_context.get_active_sport()
    
    # Perform the actual search using the BallDontLie API
    try:
        if entity_type == "player":
            results = await balldontlie_service.search_players(query, sport=active_sport)
        else:
            results = await balldontlie_service.search_teams(query, sport=active_sport)
        
        # Debug logging
        print(f"Search results for '{query}': {results}")
        
        return {
            "query": query,
            "entity_type": entity_type,
            "sport": active_sport,
            "results": results
        }
    except httpx.HTTPError as e:
        print(f"HTTP Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error searching for {entity_type}s: {str(e)}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")