from fastapi import APIRouter, Response
from app.services import reddit_service

router = APIRouter(prefix="/reddit", tags=["reddit"])

@router.get("/{entity_type}/{entity_id}")
async def entity_posts(response: Response, entity_type: str, entity_id: str):
    posts = await reddit_service.get_entity_posts(entity_type, entity_id)
    response.headers["Cache-Control"] = "public, max-age=60"
    return {"entity_type": entity_type, "entity_id": entity_id, "count": len(posts), "posts": posts}
