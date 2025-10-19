from fastapi import APIRouter, Depends, HTTPException, Query
from app.services.sports_context import get_sports_context
from app.services.apisports import apisports_service
from app.models.schemas import SearchResult, SearchResponse
import httpx
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/")
async def get_home_info(sport: str = Query(None, description="Sport type (NBA, NFL, FOOTBALL)")):
    """
    Get home page information and configuration.
    """
    return {
        "sport": sport or "NBA",  # Default to NBA if no sport specified
    "available_sports": ["NBA", "NFL", "FOOTBALL"],
        "app_name": "Scoracle",
        "version": "0.1.0"
    }

@router.get("/search", response_model=SearchResponse)
async def search_entities(
    query: str = Query(..., description="Search query for player or team name"),
    entity_type: str = Query(None, description="Type of entity: player or team"),
    sport: str = Query(None, description="Sport type (NBA, NFL, FOOTBALL)"),
    sports_context = Depends(get_sports_context),
):
    """
    Search for players or teams based on query string.
    """
    if not entity_type:
        entity_type = "player"  # Default to player search
    
    # Use sports context to determine the active sport if not specified
    active_sport = sport or sports_context.get_active_sport()
    
    # Directly query API-Sports for search to ensure comprehensive coverage
    normalized = []
    try:
        if entity_type == "player":
            results = await apisports_service.search_players(query, active_sport)
            for r in results:
                name = f"{(r.get('first_name') or '').strip()} {(r.get('last_name') or '').strip()}".strip()
                normalized.append(SearchResult(
                    entity_type=entity_type,
                    id=str(r.get("id")),
                    name=name or "Unknown",
                    sport=active_sport,
                    additional_info={"source": "api-sports", "team_abbr": r.get("team_abbr")}
                ))
        else:
            results = await apisports_service.search_teams(query, active_sport)
            for r in results:
                name = r.get("name") or r.get("abbreviation") or "Unknown"
                normalized.append(SearchResult(
                    entity_type=entity_type,
                    id=str(r.get("id")),
                    name=name,
                    sport=active_sport,
                    additional_info={"source": "api-sports", "abbr": r.get("abbreviation")}
                ))
    except httpx.HTTPError as e:
        logger.error("HTTP error during API-Sports search: %s", e)
        raise HTTPException(status_code=502, detail=f"Upstream error searching for {entity_type}s")
    except Exception as e:
        logger.error("Unexpected error during API-Sports search: %s", e)
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

    return SearchResponse(
        query=query,
        entity_type=entity_type,
        sport=active_sport,
        results=normalized
    )