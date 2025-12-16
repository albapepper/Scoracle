"""
News Router - Simple news/mentions endpoint.

GET /api/v1/news/{entity_name}?hours=48

Fetches news from Google News RSS. Cached for 10 minutes.
"""
import logging
from typing import Any, Dict, List
from datetime import datetime, timedelta, timezone

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


def _fetch_news(query: str, hours: int = 48) -> List[Dict[str, Any]]:
    """Deprecated sync fetch.

    Kept only to avoid accidental import errors in older call sites.
    Prefer `_fetch_news_async` which uses the shared http client.
    """
    return []


async def _fetch_news_async(client: httpx.AsyncClient, query: str, hours: int = 48) -> List[Dict[str, Any]]:
    """Fetch news articles from Google News RSS with caching.

    Network fetch uses the shared httpx client for better connection reuse.
    Parsing is local via feedparser.
    """
    cache_key = f"news:{query.lower()}:{hours}"
    cached = widget_cache.get(cache_key)
    if cached is not None:
        logger.debug(f"News cache HIT: {cache_key}")
        return cached

    async def _work() -> List[Dict[str, Any]]:
        # Re-check cache after waiting (another caller may have filled it)
        cached2 = widget_cache.get(cache_key)
        if cached2 is not None:
            return cached2

        import feedparser
        import time

        rss_url = f"https://news.google.com/rss/search?q={query.replace(' ', '+')}"
        resp = await client.get(rss_url)
        resp.raise_for_status()
        feed = feedparser.parse(resp.text)

        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        articles = []

        for entry in getattr(feed, "entries", []) or []:
            # Filter by date
            pub_date = None
            try:
                if getattr(entry, "published_parsed", None):
                    dt = datetime.fromtimestamp(time.mktime(entry.published_parsed)).replace(tzinfo=timezone.utc)
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

        result = articles[:20]  # Limit to 20 articles
        widget_cache.set(cache_key, result, ttl=NEWS_CACHE_TTL)
        logger.info(f"News cache SET: {cache_key} ({len(result)} articles)")
        return result

    try:
        return await singleflight.do(cache_key, _work)
    except httpx.HTTPStatusError as e:
        status = e.response.status_code if e.response is not None else None
        logger.error(f"News upstream status error for '{query}' status={status}")
        raise HTTPException(status_code=502, detail="News upstream error")
    except httpx.HTTPError as e:
        logger.error(f"News network error for '{query}': {e}")
        raise HTTPException(status_code=502, detail="News network error")
    except Exception as e:
        logger.error(f"News parse failed for '{query}': {e}")
        return []


@router.get("/{entity_name}")
async def get_news(
    request: Request,
    response: Response,
    entity_name: str,
    hours: int = Query(48, description="Hours to look back for news"),
) -> Dict[str, Any]:
    """
    Get news articles for an entity.
    
    - Fetches from Google News RSS
    - Cached for 10 minutes
    - Returns up to 20 articles from the last N hours
    """
    client = getattr(request.app.state, "http_client", None)
    if client is None:
        raise HTTPException(status_code=500, detail="HTTP client not initialized")

    articles = await _fetch_news_async(client, entity_name, hours=hours)

    payload = {
        "query": entity_name,
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
