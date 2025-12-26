"""
News Router - Entity-validated news service using Aho-Corasick matching.

This redesigned news service:
1. Fetches news using entity-specific queries (like before)
2. Validates each article against known entities using Aho-Corasick
3. Returns only articles that match verified entities with confidence scores

The key improvement over the old approach is that we validate matches against
our database of known entities, eliminating false positives from substring
matches or common names.

Endpoints:
- GET /api/v1/news?sport=NFL&hours=48 - Get validated news for a sport
- GET /api/v1/news?sport=NFL&entity_id=123&entity_type=player - Filter by entity
- GET /api/v1/news/{entity_name}?sport=NFL - Legacy endpoint (validated)
"""
import asyncio
import logging
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

# Sport keywords for query enhancement
SPORT_KEYWORDS = {
    Sport.NFL: "NFL",
    Sport.NBA: "NBA",
    Sport.FOOTBALL: "football soccer",
}

# Top entities to query for sport-wide news (populated from DB)
# These are fetched dynamically but we have fallbacks
SPORT_QUERIES_FALLBACK = {
    Sport.NFL: [
        "Patrick Mahomes", "Josh Allen", "Lamar Jackson", "Travis Kelce",
        "Jalen Hurts", "Tyreek Hill", "Justin Jefferson", "Micah Parsons",
        "Chiefs", "Eagles", "49ers", "Cowboys", "Bills", "Ravens",
    ],
    Sport.NBA: [
        "LeBron James", "Stephen Curry", "Kevin Durant", "Giannis Antetokounmpo",
        "Luka Doncic", "Jayson Tatum", "Joel Embiid", "Nikola Jokic",
        "Lakers", "Celtics", "Warriors", "Nuggets", "Bucks", "76ers",
    ],
    Sport.FOOTBALL: [
        "Erling Haaland", "Kylian Mbappe", "Jude Bellingham", "Vinicius Junior",
        "Bukayo Saka", "Mohamed Salah", "Cole Palmer", "Rodri",
        "Manchester City", "Arsenal", "Liverpool", "Real Madrid", "Barcelona",
    ],
}


async def _fetch_rss_feed(
    client: httpx.AsyncClient,
    query: str,
    hours: int,
) -> list[dict[str, Any]]:
    """
    Fetch news articles from Google News RSS for a query.

    Returns raw articles with title, link, pub_date, source, description.
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


def _build_query(entity_name: str, sport: Optional[Sport] = None) -> str:
    """Build a search query for an entity with optional sport context."""
    if sport and sport in SPORT_KEYWORDS:
        return f'"{entity_name}" {SPORT_KEYWORDS[sport]}'
    return f'"{entity_name}"'


async def _fetch_entity_news(
    client: httpx.AsyncClient,
    entity_name: str,
    hours: int,
    sport: Optional[Sport] = None,
) -> list[dict[str, Any]]:
    """
    Fetch news for a specific entity and validate against known entities.

    Returns validated articles with matched_entities.
    """
    entity_index = get_entity_index()

    # Build query and fetch
    query = _build_query(entity_name, sport)
    articles = await _fetch_rss_feed(client, query, hours)

    if not entity_index.is_loaded:
        # Fallback: return unvalidated articles if index not loaded
        logger.warning("Entity index not loaded, returning unvalidated articles")
        return [
            {
                "title": a.get("title", ""),
                "link": a.get("link", ""),
                "pub_date": a.get("pub_date"),
                "source": a.get("source", ""),
                "matched_entities": [],
            }
            for a in articles
        ]

    # Validate each article
    validated = []
    for article in articles:
        text = f"{article.get('title', '')} {article.get('description', '')}"

        # Find matching entities
        matches = entity_index.find_entities(text, sport=sport)

        if not matches:
            continue

        validated.append({
            "title": article.get("title", ""),
            "link": article.get("link", ""),
            "pub_date": article.get("pub_date"),
            "source": article.get("source", ""),
            "matched_entities": [_matched_entity_to_dict(m) for m in matches],
        })

    return validated


async def _fetch_sport_news(
    client: httpx.AsyncClient,
    sport: Sport,
    hours: int,
    entity_id: Optional[int] = None,
    entity_type: Optional[EntityType] = None,
) -> dict[str, Any]:
    """
    Fetch news for a sport by querying multiple popular entities.

    This queries news for top players/teams and validates all results,
    giving a broad view of sport news with entity tagging.
    """
    entity_index = get_entity_index()

    # Get query entities - use top entities for the sport
    query_entities = SPORT_QUERIES_FALLBACK.get(sport, [])

    if not query_entities:
        return {"articles": [], "hours_used": hours, "entities_matched": 0}

    # Fetch news for multiple entities in parallel
    tasks = [
        _fetch_entity_news(client, entity, hours, sport)
        for entity in query_entities[:10]  # Limit to top 10 to avoid rate limiting
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Merge all results
    all_articles = []
    for result in results:
        if isinstance(result, Exception):
            logger.warning(f"Query failed: {result}")
            continue
        all_articles.extend(result)

    # Deduplicate and sort
    unique = _deduplicate_articles(all_articles)
    sorted_articles = _sort_by_date(unique)

    # Filter by specific entity if requested
    if entity_id is not None and entity_type is not None:
        sorted_articles = [
            a for a in sorted_articles
            if any(
                me.get("id") == entity_id and me.get("type") == entity_type.value
                for me in a.get("matched_entities", [])
            )
        ]

    # Count unique entities
    entities_seen: set[tuple[str, int]] = set()
    for article in sorted_articles:
        for me in article.get("matched_entities", []):
            entities_seen.add((me.get("type", ""), me.get("id", 0)))

    return {
        "articles": sorted_articles[:MAX_ARTICLES],
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
    """
    cache_key = f"news:v4:{sport.value}:{hours}:{entity_type.value if entity_type else ''}:{entity_id or ''}"
    cached = widget_cache.get(cache_key)
    if cached is not None:
        logger.debug(f"News cache HIT: {cache_key}")
        return cached

    async def _work() -> dict[str, Any]:
        cached2 = widget_cache.get(cache_key)
        if cached2 is not None:
            return cached2

        final_hours = hours
        result = {"articles": [], "hours_used": hours, "entities_matched": 0}

        for try_hours in TIME_RANGE_ESCALATION:
            if try_hours < hours:
                continue

            result = await _fetch_sport_news(
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
        logger.info(f"News cache SET: {cache_key} ({len(result['articles'])} articles)")
        return result

    try:
        return await singleflight.do(cache_key, _work)
    except httpx.HTTPError as e:
        logger.error(f"News network error: {e}")
        raise HTTPException(status_code=502, detail="News network error")
    except Exception as e:
        logger.error(f"News fetch failed: {e}")
        return {"articles": [], "hours_used": hours, "entities_matched": 0}


@router.get("/{entity_name}")
async def get_news_by_name(
    request: Request,
    response: Response,
    entity_name: str,
    hours: int = Query(48, description="Hours to look back"),
    sport: Optional[str] = Query(None, description="Sport (NFL, NBA, FOOTBALL)"),
    team: Optional[str] = Query(None, description="Team context (unused, for compatibility)"),
) -> dict[str, Any]:
    """
    Get validated news for an entity by name.

    This endpoint queries Google News for the entity name and validates
    all results against our database of known entities using Aho-Corasick
    matching. This eliminates false positives from substring matches.

    The response includes matched_entities for each article showing which
    database entities were found with confidence scores.
    """
    client = getattr(request.app.state, "http_client", None)
    if client is None:
        raise HTTPException(status_code=500, detail="HTTP client not initialized")

    # Parse sport
    sport_enum: Optional[Sport] = None
    if sport:
        try:
            sport_enum = Sport(sport.upper())
        except ValueError:
            pass

    # Fetch and validate news
    articles = await _fetch_entity_news(client, entity_name, hours, sport_enum)

    # Deduplicate and sort
    articles = _sort_by_date(_deduplicate_articles(articles))[:MAX_ARTICLES]

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

    This endpoint fetches news for popular entities in the sport and
    validates all results against our entity database. Each article
    includes matched_entities with confidence scores.

    Optionally filter to a specific entity_id + entity_type.
    """
    client = getattr(request.app.state, "http_client", None)
    if client is None:
        raise HTTPException(status_code=500, detail="HTTP client not initialized")

    try:
        sport_enum = Sport(sport.upper())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid sport. Must be one of: {', '.join(s.value for s in Sport)}"
        )

    entity_type_enum: Optional[EntityType] = None
    if entity_type:
        try:
            entity_type_enum = EntityType(entity_type.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid entity_type. Must be one of: {', '.join(e.value for e in EntityType)}"
            )

    if (entity_id is not None) != (entity_type_enum is not None):
        raise HTTPException(
            status_code=400,
            detail="Both entity_id and entity_type must be provided together"
        )

    result = await _fetch_news_with_escalation(
        client, sport_enum, hours,
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
