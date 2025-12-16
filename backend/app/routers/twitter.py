from fastapi import APIRouter, Response
from app.services import twitter_service

router = APIRouter(prefix="/twitter", tags=["twitter"])

@router.get("/{entity_type}/{entity_id}")
async def entity_tweets(response: Response, entity_type: str, entity_id: str):
    tweets = await twitter_service.get_entity_tweets(entity_type, entity_id)
    response.headers["Cache-Control"] = "public, max-age=60"
    return {"entity_type": entity_type, "entity_id": entity_id, "count": len(tweets), "tweets": tweets}
