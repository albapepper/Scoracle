"""
News Router - Entity-enriched news service using Aho-Corasick matching.

This service:
1. Fetches news using entity-specific queries (proven to work)
2. ENRICHES articles with matched entity data (does NOT filter)
3. Returns ALL articles, with entity matches where found

Key principle: Entity matching is an ENRICHMENT, not a filter.
Articles are always returned - matched_entities is bonus metadata.

Endpoints:
- GET /api/v1/news/{entity_name}?sport=NFL - Get news for entity (enriched)
- GET /api/v1/news?sport=NFL - Get sport-wide news (enriched)
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
from app.utils.http_cache import build_cache_control, compute_etag, if_none_match_matches

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/news", tags=["news"])

# Cache TTL: 10 minutes for news
NEWS_CACHE_TTL = 10 * 60

NEWS_CACHE_CONTROL = build_cache_control(
    max_age=60,
    s_maxage=NEWS_CACHE_TTL,
    stale_while_revalidate=60 * 60,
    stale_if_error=60 * 60,
)

MAX_ARTICLES = 50
MIN_ARTICLES_THRESHOLD = 3
TIME_RANGE_ESCALATION = [48, 96, 168]

# Sport keywords for query enhancement
SPORT_KEYWORDS = {
    "NFL": "NFL football",
    "NBA": "NBA basketball",
    "FOOTBALL": "football soccer",
}


def _get_entity_index():
    """Safely get entity index, returns None if not available."""
    try:
        from app.services.entity_index import get_entity_index, Sport, EntityType
        index = get_entity_index()
        return index if index.is_loaded else None
    except Exception as e:
        logger.warning(f"Entity index not available: {e}")
        return None


def _enrich_with_entities(text: str, sport_str: Optional[str] = None) -> list[dict[str, Any]]:
    """
    Find matching entities in text. Returns empty list if index unavailable.
    This is ENRICHMENT - failure just means no entity tags, not an error.
    """
    try:
        from app.services.entity_index import get_entity_index, Sport
        index = get_entity_index()
        if not index.is_loaded:
            return []

        sport_enum = None
        if sport_str:
            try:
                sport_enum = Sport(sport_str.upper())
            except ValueError:
                pass

        matches = index.find_entities(text, sport=sport_enum)
        return [
            {
                "type": m.entity_type.value,
                "id": m.entity_id,
                "name": m.entity_name,
                "sport": m.sport.value,
                "confidence": m.confidence,
            }
            for m in matches
        ]
    except Exception as e:
        logger.debug(f"Entity enrichment failed: {e}")
        return []


async def _fetch_rss_feed(
    client: httpx.AsyncClient,
    query: str,
    hours: int,
) -> list[dict[str, Any]]:
    """Fetch news articles from Google News RSS."""
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


async def _fetch_news_for_query(
    client: httpx.AsyncClient,
    query: str,
    hours: int,
    sport: Optional[str] = None,
) -> list[dict[str, Any]]:
    """
    Fetch news for a query and enrich with entity data.

    ALWAYS returns articles - entity matching is optional enrichment.
    """
    articles = await _fetch_rss_feed(client, query, hours)

    # Enrich each article with entity matches (best effort)
    enriched = []
    for article in articles:
        text = f"{article.get('title', '')} {article.get('description', '')}"
        matched_entities = _enrich_with_entities(text, sport)

        enriched.append({
            "title": article.get("title", ""),
            "link": article.get("link", ""),
            "pub_date": article.get("pub_date"),
            "source": article.get("source", ""),
            "matched_entities": matched_entities,
        })

    return enriched


def _build_query(entity_name: str, sport: Optional[str] = None) -> str:
    """Build search query with optional sport context."""
    if sport and sport.upper() in SPORT_KEYWORDS:
        return f'"{entity_name}" {SPORT_KEYWORDS[sport.upper()]}'
    return f'"{entity_name}"'


@router.get("/{entity_name}")
async def get_news_by_name(
    request: Request,
    response: Response,
    entity_name: str,
    hours: int = Query(48, description="Hours to look back"),
    sport: Optional[str] = Query(None, description="Sport (NFL, NBA, FOOTBALL)"),
    team: Optional[str] = Query(None, description="Team context (unused)"),
) -> dict[str, Any]:
    """
    Get news for an entity by name.

    Returns ALL matching articles, enriched with entity metadata where
    we can identify known players/teams. Entity matching uses Aho-Corasick
    for accuracy but articles are never filtered out - you always get results.
    """
    client = getattr(request.app.state, "http_client", None)
    if client is None:
        raise HTTPException(status_code=500, detail="HTTP client not initialized")

    query = _build_query(entity_name, sport)

    # Try escalating time ranges if needed
    final_hours = hours
    articles = []

    for try_hours in TIME_RANGE_ESCALATION:
        if try_hours < hours:
            continue

        articles = await _fetch_news_for_query(client, query, try_hours, sport)
        final_hours = try_hours

        if len(articles) >= MIN_ARTICLES_THRESHOLD:
            break

    # Deduplicate and sort
    articles = _sort_by_date(_deduplicate_articles(articles))[:MAX_ARTICLES]

    # Count entities found
    entities_found = set()
    for a in articles:
        for me in a.get("matched_entities", []):
            entities_found.add((me.get("type"), me.get("id")))

    payload = {
        "query": entity_name,
        "sport": sport,
        "hours": final_hours,
        "hours_requested": hours,
        "extended": final_hours > hours,
        "count": len(articles),
        "entities_found": len(entities_found),
        "articles": articles,
    }

    etag = compute_etag(payload)
    if if_none_match_matches(request.headers.get("if-none-match"), etag):
        return Response(status_code=304, headers={"ETag": etag, "Cache-Control": NEWS_CACHE_CONTROL})

    response.headers["ETag"] = etag
    response.headers["Cache-Control"] = NEWS_CACHE_CONTROL
    return payload


# Top entities for sport-wide queries
SPORT_TOP_ENTITIES = {
    "NFL": ["Patrick Mahomes", "Josh Allen", "Lamar Jackson", "Chiefs", "Eagles", "49ers", "Cowboys", "Bills"],
    "NBA": ["LeBron James", "Stephen Curry", "Kevin Durant", "Giannis Antetokounmpo", "Lakers", "Celtics", "Warriors"],
    "FOOTBALL": ["Erling Haaland", "Kylian Mbappe", "Jude Bellingham", "Manchester City", "Arsenal", "Real Madrid"],
}


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
    Get news for a sport by querying top entities.

    Fetches news for popular players/teams in the sport and merges results.
    Each article is enriched with matched entity data.
    """
    client = getattr(request.app.state, "http_client", None)
    if client is None:
        raise HTTPException(status_code=500, detail="HTTP client not initialized")

    sport_upper = sport.upper()
    if sport_upper not in SPORT_TOP_ENTITIES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid sport. Must be one of: NFL, NBA, FOOTBALL"
        )

    # Query multiple entities in parallel
    entities = SPORT_TOP_ENTITIES[sport_upper][:8]  # Limit to avoid rate limiting
    tasks = [
        _fetch_news_for_query(client, _build_query(entity, sport), hours, sport)
        for entity in entities
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Merge results
    all_articles = []
    for result in results:
        if isinstance(result, Exception):
            logger.warning(f"Query failed: {result}")
            continue
        all_articles.extend(result)

    # Deduplicate and sort
    articles = _sort_by_date(_deduplicate_articles(all_articles))

    # Filter by entity if requested
    if entity_id is not None and entity_type is not None:
        articles = [
            a for a in articles
            if any(
                me.get("id") == entity_id and me.get("type") == entity_type
                for me in a.get("matched_entities", [])
            )
        ]

    articles = articles[:MAX_ARTICLES]

    # Count entities
    entities_found = set()
    for a in articles:
        for me in a.get("matched_entities", []):
            entities_found.add((me.get("type"), me.get("id")))

    payload = {
        "sport": sport_upper,
        "hours": hours,
        "count": len(articles),
        "entities_found": len(entities_found),
        "articles": articles,
    }

    etag = compute_etag(payload)
    if if_none_match_matches(request.headers.get("if-none-match"), etag):
        return Response(status_code=304, headers={"ETag": etag, "Cache-Control": NEWS_CACHE_CONTROL})

    response.headers["ETag"] = etag
    response.headers["Cache-Control"] = NEWS_CACHE_CONTROL
    return payload
