from fastapi import APIRouter
from app.services import twitter_service

router = APIRouter()


@router.get("/twitter/{entity_type}/{entity_id}")
async def entity_tweets(entity_type: str, entity_id: str):
    tweets = await twitter_service.get_entity_tweets(entity_type, entity_id)
    return {"entity_type": entity_type, "entity_id": entity_id, "tweets": tweets}
