from fastapi import APIRouter, Depends, HTTPException, Query
from app.services.sports_context import get_sports_context
from app.services.balldontlie_api import balldontlie_service
from app.models.schemas import SearchResult, SearchResponse
from app.db.registry import entity_registry
import httpx
import logging

logger = logging.getLogger(__name__)

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

@router.get("/search", response_model=SearchResponse)
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
    
    # Registry-first strategy
    normalized = []
    used_registry = False
    try:
        registry_rows = await entity_registry.search(active_sport, entity_type, query, limit=25)
        if registry_rows:
            used_registry = True
            for r in registry_rows:
                name = r.get("full_name") or r.get("team_abbr") or "Unknown"
                normalized.append(SearchResult(
                    entity_type=entity_type,
                    id=str(r.get("id")),
                    name=name,
                    sport=active_sport,
                    additional_info={"source": "registry", "team_abbr": r.get("team_abbr")}
                ))
    except Exception as e:
        logger.warning("Registry search failed, falling back to upstream: %s", e)

    if not normalized:
        # Fallback to upstream API (only fully supported for NBA currently)
        try:
            if entity_type == "player":
                results = await balldontlie_service.search_players(query, sport=active_sport)
            else:
                results = await balldontlie_service.search_teams(query, sport=active_sport)
            for r in results:
                if entity_type == "player":
                    name = f"{r.get('first_name','')} {r.get('last_name','')}".strip()
                else:
                    name = r.get("full_name") or r.get("name") or "Unknown"
                normalized.append(SearchResult(
                    entity_type=entity_type,
                    id=str(r.get("id")),
                    name=name,
                    sport=active_sport,
                    additional_info={"source": "upstream", "raw": r}
                ))
        except httpx.HTTPError as e:
            logger.error("HTTP error during upstream search: %s", e)
            raise HTTPException(status_code=502, detail=f"Upstream error searching for {entity_type}s")
        except Exception as e:
            logger.error("Unexpected error during search: %s", e)
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

    return SearchResponse(
        query=query,
        entity_type=entity_type,
        sport=active_sport,
        results=normalized
    )