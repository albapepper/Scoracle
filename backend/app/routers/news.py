from fastapi import APIRouter, Query
from typing import Optional
import os

from app.services import news_fast

router = APIRouter()


@router.get("/news/mentions/{entity_type}/{entity_id}")
async def mentions(entity_type: str, entity_id: str, sport: Optional[str] = Query(None)):
    """Legacy endpoint - redirects to fast endpoint. Kept for backward compatibility."""
    resolved_name = await news_fast.resolve_entity_name(entity_type, entity_id, sport)
    result = news_fast.fast_mentions(query=resolved_name.strip(), sport=(sport or "NBA").upper(), hours=48, mode="auto")
    articles = result.get("articles", [])
    return {"entity_type": entity_type, "entity_id": entity_id, "sport": (sport or "").upper(), "items": articles}


@router.get("/news/fast")
def mentions_fast(query: str = Query(...), sport: str = Query("NBA"), hours: int = Query(48), mode: str = Query("auto")):
    """High-performance mentions endpoint using Aho-Corasick.

    - query: free text, e.g., player or team name(s)
    - sport: NBA | EPL/FOOTBALL | NFL
    - hours: recency window for RSS filtering
    """
    result = news_fast.fast_mentions(query=query.strip(), sport=(sport or "NBA").upper(), hours=max(1, min(hours, 168)), mode=mode.lower())
    return result


@router.get("/news/fast/{entity_type}/{entity_id}")
async def mentions_fast_by_entity(entity_type: str, entity_id: str, sport: Optional[str] = Query(None), hours: int = Query(48), mode: str = Query("auto")):
    """High-performance mentions endpoint that resolves entity_id to name."""
    resolved_name = await news_fast.resolve_entity_name(entity_type, entity_id, sport)
    result = news_fast.fast_mentions(query=resolved_name.strip(), sport=(sport or "NBA").upper(), hours=max(1, min(hours, 168)), mode=mode.lower())
    return result


@router.get("/news/debug")
def news_debug():
    """Debug endpoint to check service status."""
    from app.database.local_dbs import _candidate_db_dirs, _db_path_for_sport
    
    debug_info = {
        "vercel_env": os.getenv("VERCEL", "0"),
        "cwd": os.getcwd(),
        "candidate_db_dirs": _candidate_db_dirs(),
    }
    
    for sport in ["NBA", "NFL", "FOOTBALL"]:
        db_path = _db_path_for_sport(sport)
        debug_info[f"db_path_{sport.lower()}"] = db_path
        debug_info[f"db_exists_{sport.lower()}"] = os.path.exists(db_path)
    
    return debug_info
