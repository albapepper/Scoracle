"""Stub Twitter service module.

Future implementation will wrap Twitter API client interactions for mentions, trends,
and embedding. For now we provide placeholder async functions so routers can be wired.
"""
from typing import List, Dict


async def get_entity_tweets(entity_type: str, entity_id: str) -> List[Dict]:
    return []
