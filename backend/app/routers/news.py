"""
News Router - Enhanced news/mentions endpoint with multi-query strategy.

GET /api/v1/news/{entity_name}?hours=48&sport=NFL&team=Chiefs

Fetches news from Google News RSS using multiple query strategies for better coverage.
Cached for 10 minutes. Adaptive time range extends up to 1 week if < 3 hits.
"""
import logging
from typing import Any, Dict, List, Optional, Set
from datetime import datetime, timedelta, timezone
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

# Cache policy (snappy news)
# - Browser: 60s
# - CDN: 10m
# - SWR: 1h (serve instantly, refresh in background)
NEWS_CACHE_CONTROL = build_cache_control(
    max_age=60,
    s_maxage=NEWS_CACHE_TTL,
    stale_while_revalidate=60 * 60,
    stale_if_error=60 * 60,
)

# Minimum articles threshold - if below this, extend time range
MIN_ARTICLES_THRESHOLD = 3

# Maximum articles to return
MAX_ARTICLES = 50

# Time range escalation (in hours): 48h -> 96h -> 168h (1 week)
TIME_RANGE_ESCALATION = [48, 96, 168]

# Sport display names for query enhancement
SPORT_KEYWORDS = {
    "NFL": ["NFL", "football"],
    "NBA": ["NBA", "basketball"],
    "FOOTBALL": ["soccer", "football"],
}


def _build_query_variations(
    entity_name: str,
    sport: Optional[str] = None,
    team: Optional[str] = None,
) -> List[str]:
    """
    Build multiple query variations for better news coverage.

    Query strategies:
    1. Full name (baseline)
    2. "Full name" in quotes (exact phrase)
    3. Full name + sport keyword
    4. Last name + team (if available)
    5. Full name + team (if available)

    Returns list of query strings ordered by specificity.
    """
    queries = []
    name_parts = entity_name.strip().split()

    # 1. Quoted full name (exact phrase match - highest precision)
    queries.append(f'"{entity_name}"')

    # 2. Full name + sport keyword (if sport provided)
    if sport and sport.upper() in SPORT_KEYWORDS:
        keywords = SPORT_KEYWORDS[sport.upper()]
        # Use primary keyword
        queries.append(f"{entity_name} {keywords[0]}")

    # 3. Full name + team (if available)
    if team:
        queries.append(f"{entity_name} {team}")

    # 4. Last name + team (for players with team context)
    if team and len(name_parts) >= 2:
        last_name = name_parts[-1]
        # Only use if last name is substantial (4+ chars)
        if len(last_name) >= 4:
            queries.append(f"{last_name} {team}")

    # 5. Plain full name (broadest search - catches everything)
    queries.append(entity_name)

    return queries


async def _fetch_single_query(
    client: httpx.AsyncClient,
    query: str,
    hours: int,
) -> List[Dict[str, Any]]:
    """
    Fetch news for a single query string.

    Returns raw articles without deduplication (caller handles that).
    """
    import feedparser
    import time

    # URL-encode the query
    encoded_query = quote_plus(query)
    rss_url = f"https://news.google.com/rss/search?q={encoded_query}"

    try:
        resp = await client.get(rss_url, timeout=10.0)
        resp.raise_for_status()
    except httpx.HTTPError as e:
        logger.warning(f"Query failed '{query}': {e}")
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


def _deduplicate_articles(articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Deduplicate articles by link URL.

    Preserves order (first occurrence wins).
    """
    seen_links: Set[str] = set()
    unique = []

    for article in articles:
        link = article.get("link", "")
        if link and link not in seen_links:
            seen_links.add(link)
            unique.append(article)

    return unique


def _sort_articles_by_date(articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Sort articles by publication date (newest first).

    Articles without dates go to the end.
    """
    def sort_key(article: Dict[str, Any]) -> str:
        # ISO format sorts correctly as strings
        return article.get("pub_date") or "0000-00-00"

    return sorted(articles, key=sort_key, reverse=True)


async def _fetch_news_multi_query(
    client: httpx.AsyncClient,
    entity_name: str,
    hours: int,
    sport: Optional[str] = None,
    team: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Fetch news using multiple query strategies and merge results.

    Executes queries in parallel for speed, deduplicates by link,
    and sorts by date.
    """
    queries = _build_query_variations(entity_name, sport, team)
    logger.debug(f"Multi-query for '{entity_name}': {queries}")

    # Fetch all queries in parallel
    import asyncio
    tasks = [_fetch_single_query(client, q, hours) for q in queries]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Merge all results
    all_articles = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.warning(f"Query {i} failed: {result}")
            continue
        all_articles.extend(result)

    # Deduplicate and sort
    unique = _deduplicate_articles(all_articles)
    sorted_articles = _sort_articles_by_date(unique)

    return sorted_articles[:MAX_ARTICLES]


async def _fetch_news_async(
    client: httpx.AsyncClient,
    entity_name: str,
    hours: int = 48,
    sport: Optional[str] = None,
    team: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Fetch news articles with multi-query strategy and adaptive time range.

    If fewer than MIN_ARTICLES_THRESHOLD articles are found, automatically
    extends the time range up to 1 week maximum.

    Returns dict with articles and metadata about the search.
    """
    # Build cache key including all parameters
    cache_key = f"news:v2:{entity_name.lower()}:{hours}:{(sport or '').lower()}:{(team or '').lower()}"
    cached = widget_cache.get(cache_key)
    if cached is not None:
        logger.debug(f"News cache HIT: {cache_key}")
        return cached

    async def _work() -> Dict[str, Any]:
        # Re-check cache after waiting
        cached2 = widget_cache.get(cache_key)
        if cached2 is not None:
            return cached2

        final_hours = hours
        articles = []

        # Try escalating time ranges if not enough results
        for try_hours in TIME_RANGE_ESCALATION:
            if try_hours < hours:
                continue  # Skip if requested hours is already higher

            articles = await _fetch_news_multi_query(
                client, entity_name, try_hours, sport, team
            )

            final_hours = try_hours

            # If we have enough articles, stop escalating
            if len(articles) >= MIN_ARTICLES_THRESHOLD:
                break

            logger.info(
                f"Only {len(articles)} articles for '{entity_name}' with {try_hours}h, "
                f"extending time range..."
            )

        result = {
            "articles": articles,
            "hours_used": final_hours,
            "hours_requested": hours,
            "extended": final_hours > hours,
        }

        widget_cache.set(cache_key, result, ttl=NEWS_CACHE_TTL)
        logger.info(
            f"News cache SET: {cache_key} ({len(articles)} articles, "
            f"hours={final_hours}, extended={result['extended']})"
        )
        return result

    try:
        return await singleflight.do(cache_key, _work)
    except httpx.HTTPStatusError as e:
        status = e.response.status_code if e.response is not None else None
        logger.error(f"News upstream status error for '{entity_name}' status={status}")
        raise HTTPException(status_code=502, detail="News upstream error")
    except httpx.HTTPError as e:
        logger.error(f"News network error for '{entity_name}': {e}")
        raise HTTPException(status_code=502, detail="News network error")
    except Exception as e:
        logger.error(f"News fetch failed for '{entity_name}': {e}")
        return {"articles": [], "hours_used": hours, "hours_requested": hours, "extended": False}


def _fetch_news(query: str, hours: int = 48) -> List[Dict[str, Any]]:
    """Deprecated sync fetch.

    Kept only to avoid accidental import errors in older call sites.
    Prefer `_fetch_news_async` which uses the shared http client.
    """
    return []


@router.get("/{entity_name}")
async def get_news(
    request: Request,
    response: Response,
    entity_name: str,
    hours: int = Query(48, description="Hours to look back for news (may auto-extend if few results)"),
    sport: Optional[str] = Query(None, description="Sport context (NFL, NBA, FOOTBALL) for better search relevance"),
    team: Optional[str] = Query(None, description="Team name for player context"),
) -> Dict[str, Any]:
    """
    Get news articles for an entity with enhanced multi-query search.

    Features:
    - Multiple query strategies for better coverage
    - Sport/team context for relevance filtering
    - Adaptive time range: auto-extends up to 1 week if < 3 results
    - Returns up to 50 deduplicated articles sorted by date
    - Cached for 10 minutes
    """
    client = getattr(request.app.state, "http_client", None)
    if client is None:
        raise HTTPException(status_code=500, detail="HTTP client not initialized")

    result = await _fetch_news_async(
        client,
        entity_name,
        hours=hours,
        sport=sport,
        team=team,
    )

    articles = result.get("articles", [])

    payload = {
        "query": entity_name,
        "sport": sport,
        "team": team,
        "hours": result.get("hours_used", hours),
        "hours_requested": result.get("hours_requested", hours),
        "extended": result.get("extended", False),
        "count": len(articles),
        "articles": articles,
    }

    etag = compute_etag(payload)
    if if_none_match_matches(request.headers.get("if-none-match"), etag):
        return Response(status_code=304, headers={"ETag": etag, "Cache-Control": NEWS_CACHE_CONTROL})

    response.headers["ETag"] = etag
    response.headers["Cache-Control"] = NEWS_CACHE_CONTROL
    return payload
