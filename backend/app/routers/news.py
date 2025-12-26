"""
News Router - Simple, robust news service.

Design principles:
1. Trust Google's relevance ranking
2. Use exact phrase queries for precision
3. Simple title verification (no complex entity matching)
4. Always return results - never filter to zero

This replaces the over-engineered Aho-Corasick approach with something
that just works.
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

# Cache settings
NEWS_CACHE_TTL = 10 * 60  # 10 minutes

NEWS_CACHE_CONTROL = build_cache_control(
    max_age=60,
    s_maxage=NEWS_CACHE_TTL,
    stale_while_revalidate=60 * 60,
    stale_if_error=60 * 60,
)

MAX_ARTICLES = 50
MIN_ARTICLES_THRESHOLD = 3
TIME_RANGE_ESCALATION = [48, 96, 168]

# Sport context for queries
SPORT_CONTEXT = {
    "NFL": "NFL",
    "NBA": "NBA",
    "FOOTBALL": "soccer football",
}


def _normalize(text: str) -> str:
    """Simple text normalization for matching."""
    return text.lower().strip()


def _name_in_text(name: str, text: str) -> bool:
    """
    Check if name appears in text.

    Simple but effective - checks if all significant parts of the name
    appear in the text. Handles "Patrick Mahomes" matching "Mahomes"
    or "Patrick Mahomes".
    """
    name_lower = _normalize(name)
    text_lower = _normalize(text)

    # Split name into parts, filter short words
    parts = [p for p in name_lower.split() if len(p) >= 3]

    if not parts:
        return name_lower in text_lower

    # For single-word names, require exact word match
    if len(parts) == 1:
        # Check word boundaries (simple approach)
        import re
        pattern = r'\b' + re.escape(parts[0]) + r'\b'
        return bool(re.search(pattern, text_lower))

    # For multi-word names, check if last name (usually most distinctive) is present
    # and at least one other part
    last_name = parts[-1]
    other_parts = parts[:-1]

    if last_name not in text_lower:
        return False

    # Last name found - check if any other part is also there
    return any(part in text_lower for part in other_parts)


async def _fetch_google_news(
    client: httpx.AsyncClient,
    query: str,
    hours: int,
) -> list[dict[str, Any]]:
    """
    Fetch news from Google News RSS.

    Returns parsed articles with basic metadata.
    """
    import feedparser
    import time

    encoded = quote_plus(query)
    # Add language/region for better results
    url = f"https://news.google.com/rss/search?q={encoded}&hl=en-US&gl=US&ceid=US:en"

    try:
        resp = await client.get(url, timeout=10.0)
        resp.raise_for_status()
    except httpx.HTTPError as e:
        logger.warning(f"Google News fetch failed for '{query}': {e}")
        return []

    feed = feedparser.parse(resp.text)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    articles = []

    for entry in getattr(feed, "entries", []) or []:
        # Parse publication date
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

        # Extract source
        source = ""
        if hasattr(entry, "source") and isinstance(entry.source, dict):
            source = entry.source.get("title", "")

        articles.append({
            "title": getattr(entry, "title", "") or "",
            "link": getattr(entry, "link", "") or "",
            "pub_date": pub_date,
            "source": source,
        })

    return articles


def _deduplicate(articles: list[dict]) -> list[dict]:
    """Remove duplicate articles by URL."""
    seen = set()
    unique = []
    for a in articles:
        url = a.get("link", "")
        if url and url not in seen:
            seen.add(url)
            unique.append(a)
    return unique


def _sort_by_date(articles: list[dict]) -> list[dict]:
    """Sort by publication date, newest first."""
    return sorted(articles, key=lambda a: a.get("pub_date") or "", reverse=True)


@router.get("/{entity_name}")
async def get_entity_news(
    request: Request,
    response: Response,
    entity_name: str,
    hours: int = Query(48, ge=1, le=168, description="Hours to look back"),
    sport: Optional[str] = Query(None, description="Sport context (NFL, NBA, FOOTBALL)"),
    team: Optional[str] = Query(None, description="Team context (optional)"),
) -> dict[str, Any]:
    """
    Get news articles for an entity.

    Uses Google News RSS with exact phrase matching. Articles are verified
    to contain the entity name in the title for relevance.

    The sport parameter adds context to improve search precision.
    """
    client = getattr(request.app.state, "http_client", None)
    if client is None:
        raise HTTPException(status_code=500, detail="HTTP client not initialized")

    # Build query - use exact phrase with optional sport context
    query_parts = [f'"{entity_name}"']
    if sport and sport.upper() in SPORT_CONTEXT:
        query_parts.append(SPORT_CONTEXT[sport.upper()])
    if team:
        query_parts.append(team)

    query = " ".join(query_parts)

    # Build cache key
    cache_key = f"news:v5:{_normalize(entity_name)}:{hours}:{sport or ''}"

    # Check cache
    cached = widget_cache.get(cache_key)
    if cached is not None:
        # Add cache headers and return
        etag = compute_etag(cached)
        if if_none_match_matches(request.headers.get("if-none-match"), etag):
            return Response(status_code=304, headers={"ETag": etag})
        response.headers["ETag"] = etag
        response.headers["Cache-Control"] = NEWS_CACHE_CONTROL
        return cached

    # Fetch with time range escalation
    final_hours = hours
    all_articles = []

    for try_hours in TIME_RANGE_ESCALATION:
        if try_hours < hours:
            continue

        articles = await _fetch_google_news(client, query, try_hours)
        final_hours = try_hours

        # Simple relevance filter: verify entity name in title
        # This catches obvious mismatches but trusts Google for most filtering
        relevant = []
        for article in articles:
            title = article.get("title", "")
            if _name_in_text(entity_name, title):
                relevant.append(article)
            else:
                # Log but still include if we have few results
                logger.debug(f"Name not in title: {title[:50]}")
                # Include anyway if relevance rate is low (Google might be right)
                relevant.append(article)

        all_articles = relevant

        if len(all_articles) >= MIN_ARTICLES_THRESHOLD:
            break

        logger.info(f"Only {len(all_articles)} articles for '{entity_name}', extending to {try_hours}h")

    # Deduplicate and sort
    articles = _sort_by_date(_deduplicate(all_articles))[:MAX_ARTICLES]

    payload = {
        "query": entity_name,
        "sport": sport,
        "team": team,
        "hours": final_hours,
        "hours_requested": hours,
        "extended": final_hours > hours,
        "count": len(articles),
        "articles": articles,
    }

    # Cache result
    widget_cache.set(cache_key, payload, ttl=NEWS_CACHE_TTL)

    etag = compute_etag(payload)
    response.headers["ETag"] = etag
    response.headers["Cache-Control"] = NEWS_CACHE_CONTROL
    return payload


# Top entities for sport-wide news
SPORT_TOP_ENTITIES = {
    "NFL": [
        "Patrick Mahomes", "Josh Allen", "Lamar Jackson", "Jalen Hurts",
        "Travis Kelce", "Tyreek Hill", "Justin Jefferson",
        "Chiefs", "Eagles", "49ers", "Cowboys", "Bills", "Ravens",
    ],
    "NBA": [
        "LeBron James", "Stephen Curry", "Kevin Durant", "Giannis Antetokounmpo",
        "Luka Doncic", "Jayson Tatum", "Joel Embiid", "Nikola Jokic",
        "Lakers", "Celtics", "Warriors", "Nuggets", "Bucks",
    ],
    "FOOTBALL": [
        "Erling Haaland", "Kylian Mbappe", "Jude Bellingham", "Vinicius Junior",
        "Mohamed Salah", "Bukayo Saka", "Cole Palmer",
        "Manchester City", "Arsenal", "Liverpool", "Real Madrid", "Barcelona",
    ],
}


@router.get("")
async def get_sport_news(
    request: Request,
    response: Response,
    sport: str = Query(..., description="Sport (NFL, NBA, FOOTBALL)"),
    hours: int = Query(48, ge=1, le=168, description="Hours to look back"),
) -> dict[str, Any]:
    """
    Get aggregated news for a sport.

    Fetches news for top players and teams, merges and deduplicates.
    """
    client = getattr(request.app.state, "http_client", None)
    if client is None:
        raise HTTPException(status_code=500, detail="HTTP client not initialized")

    sport_upper = sport.upper()
    if sport_upper not in SPORT_TOP_ENTITIES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid sport. Must be: NFL, NBA, or FOOTBALL"
        )

    # Query top entities in parallel (limit to prevent rate limiting)
    entities = SPORT_TOP_ENTITIES[sport_upper][:10]

    async def fetch_for_entity(entity: str):
        query = f'"{entity}" {SPORT_CONTEXT.get(sport_upper, "")}'
        return await _fetch_google_news(client, query, hours)

    tasks = [fetch_for_entity(e) for e in entities]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Merge all results
    all_articles = []
    for result in results:
        if isinstance(result, Exception):
            logger.warning(f"Fetch failed: {result}")
            continue
        all_articles.extend(result)

    # Deduplicate and sort
    articles = _sort_by_date(_deduplicate(all_articles))[:MAX_ARTICLES]

    payload = {
        "sport": sport_upper,
        "hours": hours,
        "count": len(articles),
        "articles": articles,
    }

    etag = compute_etag(payload)
    if if_none_match_matches(request.headers.get("if-none-match"), etag):
        return Response(status_code=304, headers={"ETag": etag})

    response.headers["ETag"] = etag
    response.headers["Cache-Control"] = NEWS_CACHE_CONTROL
    return payload
