from fastapi import APIRouter, Query
from typing import Optional

from app.services import news_service

router = APIRouter()


@router.get("/news/mentions/{entity_type}/{entity_id}")
async def mentions(entity_type: str, entity_id: str, sport: Optional[str] = Query(None), debug: int = Query(0)):
    if debug:
        return await news_service.get_entity_mentions_with_debug(entity_type, entity_id, sport)
    items = await news_service.get_entity_mentions(entity_type, entity_id, sport)
    return {"entity_type": entity_type, "entity_id": entity_id, "sport": (sport or "").upper(), "items": items}
