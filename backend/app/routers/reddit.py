from fastapi import APIRouter
from app.services import reddit_service

router = APIRouter()


@router.get("/reddit/{entity_type}/{entity_id}")
async def entity_posts(entity_type: str, entity_id: str):
    posts = await reddit_service.get_entity_posts(entity_type, entity_id)
    return {"entity_type": entity_type, "entity_id": entity_id, "posts": posts}
