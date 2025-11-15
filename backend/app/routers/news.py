from fastapi import APIRouter, Query
from typing import Optional

from app.services import news_fast

router = APIRouter()


@router.get("/news/mentions/{entity_type}/{entity_id}")
async def mentions(entity_type: str, entity_id: str, sport: Optional[str] = Query(None), debug: int = Query(0)):
    """Legacy endpoint - redirects to fast endpoint. Kept for backward compatibility."""
    resolved_name = await news_fast.resolve_entity_name(entity_type, entity_id, sport)
    result = news_fast.fast_mentions(query=resolved_name.strip(), sport=(sport or "NBA").upper(), hours=48, mode="auto")
    articles = result.get("articles", [])
    return {"entity_type": entity_type, "entity_id": entity_id, "sport": (sport or "").upper(), "items": articles}


@router.get("/news/fast")
def mentions_fast(query: str = Query(...), sport: str = Query("NBA"), hours: int = Query(48), mode: str = Query("auto")):
    """High-performance mentions endpoint based on Aho-Corasick over local aliases.

    - query: free text, e.g., player or team name(s)
    - sport: NBA | EPL/FOOTBALL | NFL (depending on populated local DBs)
    - hours: recency window for RSS filtering
    Returns ranked players/teams mentioned and raw recent articles.
    """
    result = news_fast.fast_mentions(query=query.strip(), sport=(sport or "NBA").upper(), hours=max(1, min(hours, 168)), mode=mode.lower())
    return result


@router.get("/news/fast/{entity_type}/{entity_id}")
async def mentions_fast_by_entity(entity_type: str, entity_id: str, sport: Optional[str] = Query(None), hours: int = Query(48), mode: str = Query("auto")):
    """High-performance mentions endpoint that resolves entity_id to name and uses news_fast.
    
    - entity_type: player or team
    - entity_id: the entity ID
    - sport: NBA | EPL/FOOTBALL | NFL
    - hours: recency window for RSS filtering (default 48)
    - mode: auto | player | team (default auto)
    Returns articles with only essential fields: title, link, source, pub_date.
    """
    resolved_name = await news_fast.resolve_entity_name(entity_type, entity_id, sport)
    result = news_fast.fast_mentions(query=resolved_name.strip(), sport=(sport or "NBA").upper(), hours=max(1, min(hours, 168)), mode=mode.lower())
    return result
