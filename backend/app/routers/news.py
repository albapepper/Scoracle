from fastapi import APIRouter, Query
from typing import Optional

from app.services import news_service
from app.services import news_fast

router = APIRouter()


@router.get("/news/mentions/{entity_type}/{entity_id}")
async def mentions(entity_type: str, entity_id: str, sport: Optional[str] = Query(None), debug: int = Query(0)):
    if debug:
        return await news_service.get_entity_mentions_with_debug(entity_type, entity_id, sport)
    items = await news_service.get_entity_mentions(entity_type, entity_id, sport)
    return {"entity_type": entity_type, "entity_id": entity_id, "sport": (sport or "").upper(), "items": items}


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
