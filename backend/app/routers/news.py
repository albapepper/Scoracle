"""
News Router - Entity-validated news service using Aho-Corasick matching.

This redesigned news service:
1. Fetches news broadly by sport/league
2. Validates each article against known entities using Aho-Corasick
3. Returns only articles that match verified entities with confidence scores

Endpoints:
- GET /api/v1/news?sport=NFL&hours=48 - Get validated news for a sport
- GET /api/v1/news?sport=NFL&entity_id=123&entity_type=player - Filter by entity
"""
import asyncio
import logging
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from urllib.parse import quote_plus

from fastapi import APIRouter, Query, Response, Request, HTTPException
import httpx

from app.services.cache import widget_cache
from app.services.singleflight import singleflight
from app.services.entity_index import (
    get_entity_index,
    Sport,
    EntityType,
    MatchedEntity,
)
from app.utils.http_cache import build_cache_control, compute_etag, if_none_match_matches

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/news", tags=["news"])

# Cache TTL: 10 minutes for news
NEWS_CACHE_TTL = 10 * 60

# Cache policy
NEWS_CACHE_CONTROL = build_cache_control(
    max_age=60,
    s_maxage=NEWS_CACHE_TTL,
    stale_while_revalidate=60 * 60,
    stale_if_error=60 * 60,
)

# Maximum articles to return
MAX_ARTICLES = 50

# Minimum articles before extending time range
MIN_ARTICLES_THRESHOLD = 3

# Time range escalation (in hours)
TIME_RANGE_ESCALATION = [48, 96, 168]

# Sport-specific search queries for broad news fetching
SPORT_QUERIES = {
    Sport.NFL: [
        "NFL football news",
        "NFL players news",
    ],
    Sport.NBA: [
        "NBA basketball news",
        "NBA players news",
    ],
    Sport.FOOTBALL: [
        "Premier League football news",
        "La Liga soccer news",
        "Champions League football",
    ],
}


async def _fetch_rss_feed(
    client: httpx.AsyncClient,
    query: str,
    hours: int,
) -> list[dict[str, Any]]:
    """
    Fetch news articles from Google News RSS for a query.

    Returns raw articles with title, link, pub_date, source.
    """
    import feedparser
    import time

    encoded_query = quote_plus(query)
    rss_url = f"https://news.google.com/rss/search?q={encoded_query}"

    try:
        resp = await client.get(rss_url, timeout=10.0)
        resp.raise_for_status()
    except httpx.HTTPError as e:
        logger.warning(f"RSS fetch failed for '{query}': {e}")
        return []

    feed = feedparser.parse(resp.text)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    articles = []

    for entry in getattr(feed, "entries", []) or []:
        pub_date = None
        try:
            if getattr(entry, "published_parsed", None):
                dt = datetime.fromtimestamp(
                    time.mktime(entry.published_parsed)
                ).replace(tzinfo=timezone.utc)
                if dt < cutoff:
                    continue
                pub_date = dt.isoformat()
        except Exception:
            pass

        source = ""
        if hasattr(entry, "source") and isinstance(entry.source, dict):
            source = entry.source.get("title", "")

        articles.append({
            "title": getattr(entry, "title", "") or "",
            "link": getattr(entry, "link", "") or "",
            "pub_date": pub_date,
            "source": source,
            "description": getattr(entry, "summary", "") or "",
        })

    return articles


def _deduplicate_articles(articles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Deduplicate articles by link URL."""
    seen: set[str] = set()
    unique = []
    for article in articles:
        link = article.get("link", "")
        if link and link not in seen:
            seen.add(link)
            unique.append(article)
    return unique


def _sort_by_date(articles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Sort articles by publication date (newest first)."""
    return sorted(
        articles,
        key=lambda a: a.get("pub_date") or "0000-00-00",
        reverse=True,
    )


def _matched_entity_to_dict(entity: MatchedEntity) -> dict[str, Any]:
    """Convert MatchedEntity to JSON-serializable dict."""
    return {
        "type": entity.entity_type.value,
        "id": entity.entity_id,
        "name": entity.entity_name,
        "sport": entity.sport.value,
        "confidence": entity.confidence,
    }


async def _fetch_and_validate_news(
    client: httpx.AsyncClient,
    sport: Sport,
    hours: int,
    entity_id: Optional[int] = None,
    entity_type: Optional[EntityType] = None,
) -> dict[str, Any]:
    """
    Fetch news for a sport and validate against known entities.

    Returns articles enriched with matched entity information.
    """
    entity_index = get_entity_index()
    if not entity_index.is_loaded:
        logger.warning("Entity index not loaded, returning empty results")
        return {"articles": [], "hours_used": hours, "entities_matched": 0}

    # Fetch from multiple queries for the sport
    queries = SPORT_QUERIES.get(sport, [f"{sport.value} sports news"])

    tasks = [_fetch_rss_feed(client, q, hours) for q in queries]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Merge all results
    all_articles = []
    for result in results:
        if isinstance(result, Exception):
            logger.warning(f"Query failed: {result}")
            continue
        all_articles.extend(result)

    # Deduplicate
    unique_articles = _deduplicate_articles(all_articles)
    logger.debug(f"Fetched {len(unique_articles)} unique articles for {sport.value}")

    # Validate each article against entity index
    validated_articles = []
    entities_seen: set[tuple[str, int]] = set()

    for article in unique_articles:
        # Combine title and description for matching
        text_to_match = f"{article.get('title', '')} {article.get('description', '')}"

        # Find matching entities
        matches = entity_index.find_entities(
            text=text_to_match,
            sport=sport,
            entity_id=entity_id,
            entity_type=entity_type,
        )

        if not matches:
            continue

        # Filter by entity if specified
        if entity_id is not None and entity_type is not None:
            matches = [m for m in matches if m.entity_id == entity_id and m.entity_type == entity_type]
            if not matches:
                continue

        # Track unique entities
        for m in matches:
            entities_seen.add((m.entity_type.value, m.entity_id))

        # Remove description from output (we only needed it for matching)
        output_article = {
            "title": article.get("title", ""),
            "link": article.get("link", ""),
            "pub_date": article.get("pub_date"),
            "source": article.get("source", ""),
            "matched_entities": [_matched_entity_to_dict(m) for m in matches],
        }
        validated_articles.append(output_article)

    # Sort by date
    validated_articles = _sort_by_date(validated_articles)

    return {
        "articles": validated_articles[:MAX_ARTICLES],
        "hours_used": hours,
        "entities_matched": len(entities_seen),
    }


async def _fetch_news_with_escalation(
    client: httpx.AsyncClient,
    sport: Sport,
    hours: int,
    entity_id: Optional[int] = None,
    entity_type: Optional[EntityType] = None,
) -> dict[str, Any]:
    """
    Fetch news with adaptive time range escalation.

    If fewer than MIN_ARTICLES_THRESHOLD articles are found,
    automatically extends the time range.
    """
    # Build cache key
    cache_key = f"news:v3:{sport.value}:{hours}:{entity_type.value if entity_type else ''}:{entity_id or ''}"
    cached = widget_cache.get(cache_key)
    if cached is not None:
        logger.debug(f"News cache HIT: {cache_key}")
        return cached

    async def _work() -> dict[str, Any]:
        # Re-check cache
        cached2 = widget_cache.get(cache_key)
        if cached2 is not None:
            return cached2

        final_hours = hours
        result = {"articles": [], "hours_used": hours, "entities_matched": 0}

        for try_hours in TIME_RANGE_ESCALATION:
            if try_hours < hours:
                continue

            result = await _fetch_and_validate_news(
                client, sport, try_hours, entity_id, entity_type
            )
            final_hours = try_hours

            if len(result["articles"]) >= MIN_ARTICLES_THRESHOLD:
                break

            logger.info(
                f"Only {len(result['articles'])} articles for {sport.value}, "
                f"extending from {try_hours}h..."
            )

        result["hours_used"] = final_hours
        result["hours_requested"] = hours
        result["extended"] = final_hours > hours

        widget_cache.set(cache_key, result, ttl=NEWS_CACHE_TTL)
        logger.info(
            f"News cache SET: {cache_key} ({len(result['articles'])} articles)"
        )
        return result

    try:
        return await singleflight.do(cache_key, _work)
    except httpx.HTTPError as e:
        logger.error(f"News network error: {e}")
        raise HTTPException(status_code=502, detail="News network error")
    except Exception as e:
        logger.error(f"News fetch failed: {e}")
        return {"articles": [], "hours_used": hours, "entities_matched": 0}


# Legacy endpoint for backwards compatibility
@router.get("/{entity_name}")
async def get_news_by_name(
    request: Request,
    response: Response,
    entity_name: str,
    hours: int = Query(48, description="Hours to look back"),
    sport: Optional[str] = Query(None, description="Sport (NFL, NBA, FOOTBALL)"),
    team: Optional[str] = Query(None, description="Team context (deprecated)"),
) -> dict[str, Any]:
    """
    Legacy endpoint: Get news for an entity by name.

    This endpoint is maintained for backwards compatibility.
    For better results, use the new sport-based endpoint with entity_id.
    """
    client = getattr(request.app.state, "http_client", None)
    if client is None:
        raise HTTPException(status_code=500, detail="HTTP client not initialized")

    # Try to determine sport
    sport_enum: Optional[Sport] = None
    if sport:
        try:
            sport_enum = Sport(sport.upper())
        except ValueError:
            pass

    # If no sport, try all sports and merge
    if sport_enum is None:
        all_results: list[dict] = []
        for s in Sport:
            try:
                result = await _fetch_and_validate_news(client, s, hours)
                all_results.extend(result.get("articles", []))
            except Exception:
                continue

        # Filter by entity name in matched entities
        entity_name_lower = entity_name.lower()
        filtered = [
            a for a in all_results
            if any(
                entity_name_lower in me.get("name", "").lower()
                for me in a.get("matched_entities", [])
            )
        ]
        articles = _sort_by_date(_deduplicate_articles(filtered))[:MAX_ARTICLES]
    else:
        result = await _fetch_and_validate_news(client, sport_enum, hours)
        # Filter by entity name
        entity_name_lower = entity_name.lower()
        articles = [
            a for a in result.get("articles", [])
            if any(
                entity_name_lower in me.get("name", "").lower()
                for me in a.get("matched_entities", [])
            )
        ]

    payload = {
        "query": entity_name,
        "sport": sport,
        "hours": hours,
        "count": len(articles),
        "articles": articles,
    }

    etag = compute_etag(payload)
    if if_none_match_matches(request.headers.get("if-none-match"), etag):
        return Response(status_code=304, headers={"ETag": etag, "Cache-Control": NEWS_CACHE_CONTROL})

    response.headers["ETag"] = etag
    response.headers["Cache-Control"] = NEWS_CACHE_CONTROL
    return payload


@router.get("")
async def get_news(
    request: Request,
    response: Response,
    sport: str = Query(..., description="Sport (NFL, NBA, FOOTBALL)"),
    hours: int = Query(48, description="Hours to look back"),
    entity_id: Optional[int] = Query(None, description="Filter by entity ID"),
    entity_type: Optional[str] = Query(None, description="Entity type (player, team)"),
) -> dict[str, Any]:
    """
    Get validated news articles for a sport.

    Features:
    - Fetches broad sport news and validates against known entities
    - Each article includes matched_entities with confidence scores
    - Optionally filter by specific entity_id + entity_type
    - Adaptive time range: auto-extends if < 3 results
    - Cached for 10 minutes

    Response:
    {
        "sport": "NFL",
        "hours": 48,
        "count": 25,
        "entities_matched": 15,
        "articles": [
            {
                "title": "Mahomes leads Chiefs to victory",
                "link": "...",
                "pub_date": "2024-01-15T10:00:00Z",
                "source": "ESPN",
                "matched_entities": [
                    {"type": "player", "id": 123, "name": "Patrick Mahomes", "sport": "NFL", "confidence": "high"},
                    {"type": "team", "id": 456, "name": "Kansas City Chiefs", "sport": "NFL", "confidence": "high"}
                ]
            }
        ]
    }
    """
    client = getattr(request.app.state, "http_client", None)
    if client is None:
        raise HTTPException(status_code=500, detail="HTTP client not initialized")

    # Validate sport
    try:
        sport_enum = Sport(sport.upper())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid sport. Must be one of: {', '.join(s.value for s in Sport)}"
        )

    # Validate entity_type if provided
    entity_type_enum: Optional[EntityType] = None
    if entity_type:
        try:
            entity_type_enum = EntityType(entity_type.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid entity_type. Must be one of: {', '.join(e.value for e in EntityType)}"
            )

    # Require both entity_id and entity_type together
    if (entity_id is not None) != (entity_type_enum is not None):
        raise HTTPException(
            status_code=400,
            detail="Both entity_id and entity_type must be provided together"
        )

    result = await _fetch_news_with_escalation(
        client,
        sport_enum,
        hours,
        entity_id=entity_id,
        entity_type=entity_type_enum,
    )

    payload = {
        "sport": sport_enum.value,
        "hours": result.get("hours_used", hours),
        "hours_requested": result.get("hours_requested", hours),
        "extended": result.get("extended", False),
        "count": len(result.get("articles", [])),
        "entities_matched": result.get("entities_matched", 0),
        "articles": result.get("articles", []),
    }

    etag = compute_etag(payload)
    if if_none_match_matches(request.headers.get("if-none-match"), etag):
        return Response(status_code=304, headers={"ETag": etag, "Cache-Control": NEWS_CACHE_CONTROL})

    response.headers["ETag"] = etag
    response.headers["Cache-Control"] = NEWS_CACHE_CONTROL
    return payload
