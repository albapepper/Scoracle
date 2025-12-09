"""
Unified Entity Router - Single endpoint for all entity operations.

Features:
- Tiered data: bundled JSON (fast) + optional API-Sports enhancement
- Multi-layer caching for performance
- API key never exposed to frontend
- Graceful fallbacks - never crashes
"""
from __future__ import annotations

import logging
import hashlib
import json
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Query, HTTPException, Request, Response

from app.services.entity_service import get_entity_or_fallback, search_entities, EntityInfo
from app.services.enhanced_entity import get_enhanced_entity
from app.services.cache import widget_cache

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/entity", tags=["entities"])

# Cache TTLs (in seconds)
CACHE_TTL_ENTITY = 300      # 5 minutes for basic entity/widget data
CACHE_TTL_NEWS = 600        # 10 minutes for news (RSS is slow)
CACHE_TTL_COMBINED = 300    # 5 minutes for combined response


# ============ Caching Helpers ============

def _cache_key(prefix: str, *args) -> str:
    """Build a cache key from prefix and arguments."""
    key_parts = [prefix] + [str(a).upper() for a in args]
    return ":".join(key_parts)


def _compute_etag(data: Dict[str, Any]) -> str:
    """Compute ETag for response data."""
    try:
        content = json.dumps(data, sort_keys=True, separators=(",", ":"), default=str)
        return hashlib.md5(content.encode()).hexdigest()[:16]
    except Exception:
        return ""


# ============ News Fetching with Cache ============

def _fetch_news_articles(query: str, hours: int = 48) -> List[Dict[str, Any]]:
    """Fetch news articles from Google News RSS with caching."""
    cache_key = _cache_key("news", query, hours)
    cached = widget_cache.get(cache_key)
    if cached is not None:
        logger.debug(f"News cache hit for '{query}'")
        return cached
    
    try:
        import feedparser
        import time
        
        rss_url = f"https://news.google.com/rss/search?q={query.replace(' ', '+')}"
        feed = feedparser.parse(rss_url)
        
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        articles = []
        
        for entry in getattr(feed, "entries", []) or []:
            try:
                if getattr(entry, "published_parsed", None):
                    dt = datetime.fromtimestamp(time.mktime(entry.published_parsed)).replace(tzinfo=timezone.utc)
                    if dt < cutoff:
                        continue
            except Exception:
                pass
            
            title = getattr(entry, "title", "") or ""
            link = getattr(entry, "link", "") or ""
            pub_date = None
            try:
                if getattr(entry, "published_parsed", None):
                    dt = datetime.fromtimestamp(time.mktime(entry.published_parsed)).replace(tzinfo=timezone.utc)
                    pub_date = dt.isoformat()
            except Exception:
                pass
            
            source = ""
            if isinstance(getattr(entry, "source", None), dict):
                source = entry.source.get("title", "")
            
            articles.append({
                "title": title,
                "link": link,
                "pub_date": pub_date,
                "source": source,
            })
        
        result = articles[:20]
        widget_cache.set(cache_key, result, ttl=CACHE_TTL_NEWS)
        logger.debug(f"Cached news for '{query}': {len(result)} articles")
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to fetch news for '{query}': {e}")
        return []


# ============ Widget Data Generation ============

def _build_widget_data(entity: EntityInfo, enhanced_data: Optional[Dict] = None) -> Dict[str, Any]:
    """Build widget display data from entity info with optional enhancement."""
    base = {
        "type": entity.entity_type,
        "id": entity.id,
        "name": entity.name,
        "sport": entity.sport,
        "display_name": entity.name,
    }
    
    if entity.entity_type == "player":
        base["first_name"] = entity.first_name
        base["last_name"] = entity.last_name
        base["team"] = entity.team
        base["subtitle"] = entity.team or entity.sport
    else:
        base["league"] = entity.league
        base["subtitle"] = entity.league or entity.sport
    
    # Add enhanced data if available
    if enhanced_data:
        if enhanced_data.get("photo_url"):
            base["photo_url"] = enhanced_data["photo_url"]
        if enhanced_data.get("logo_url"):
            base["logo_url"] = enhanced_data["logo_url"]
        if enhanced_data.get("position"):
            base["position"] = enhanced_data["position"]
        if enhanced_data.get("age"):
            base["age"] = enhanced_data["age"]
        if enhanced_data.get("height"):
            base["height"] = enhanced_data["height"]
        if enhanced_data.get("conference"):
            base["conference"] = enhanced_data["conference"]
        if enhanced_data.get("division"):
            base["division"] = enhanced_data["division"]
        base["enhanced"] = True
    else:
        base["enhanced"] = False
    
    return base


# ============ Main Endpoints ============

@router.get("/{entity_type}/{entity_id}")
async def get_entity_unified(
    request: Request,
    response: Response,
    entity_type: str,
    entity_id: str,
    sport: str = Query(..., description="Sport code: NBA, NFL, FOOTBALL"),
    include: str = Query("widget", description="Comma-separated: widget, news, stats"),
    refresh: bool = Query(False, description="Force refresh from API-Sports"),
):
    """
    Unified entity endpoint - returns entity info with optional widget, news, and stats.
    
    Tiered Data:
    - Basic: Always from bundled JSON (instant, free)
    - Widget: Includes basic entity display data
    - Enhanced: Includes API-Sports profile data (photo, position, etc.)
    - Stats: Includes API-Sports statistics (more API calls)
    - News: Includes recent news articles
    
    Caching:
    - Browser: Cache-Control header
    - Backend: In-memory cache
    - ETag support for conditional requests
    
    Security:
    - API key never exposed to frontend
    - All external API calls happen on backend
    """
    sport_upper = sport.upper()
    entity_type_lower = entity_type.lower()
    
    if entity_type_lower not in ("player", "team"):
        raise HTTPException(status_code=400, detail="entity_type must be 'player' or 'team'")
    
    if sport_upper not in ("NBA", "NFL", "FOOTBALL"):
        raise HTTPException(status_code=400, detail="sport must be NBA, NFL, or FOOTBALL")
    
    # Parse includes
    includes = set(x.strip().lower() for x in include.split(","))
    include_widget = "widget" in includes
    include_news = "news" in includes
    include_stats = "stats" in includes
    include_enhanced = "enhanced" in includes or include_stats
    
    # Check cache
    cache_key = _cache_key("entity_v2", entity_type_lower, entity_id, sport_upper, 
                           ",".join(sorted(includes)), str(refresh))
    
    if not refresh:
        cached = widget_cache.get(cache_key)
        if cached is not None:
            etag = cached.get("_etag", "")
            if_none_match = request.headers.get("if-none-match")
            if if_none_match and if_none_match == etag:
                return Response(status_code=304, headers={"ETag": etag})
            
            response.headers["ETag"] = etag
            response.headers["Cache-Control"] = f"public, max-age={CACHE_TTL_COMBINED}"
            response.headers["X-Cache"] = "HIT"
            return {k: v for k, v in cached.items() if not k.startswith("_")}
    
    # Get entity data
    if include_enhanced:
        # Fetch enhanced data from API-Sports (cached on backend)
        enhanced_data = await get_enhanced_entity(
            entity_type_lower, entity_id, sport_upper,
            include_stats=include_stats,
            force_refresh=refresh
        )
        entity = enhanced_data.entity
        enhanced_dict = enhanced_data.to_dict()
    else:
        # Just use bundled JSON (instant)
        entity = get_entity_or_fallback(entity_type_lower, entity_id, sport_upper)
        enhanced_dict = None
    
    # Build response
    result: Dict[str, Any] = {
        "entity": entity.to_dict() if not enhanced_dict else enhanced_dict,
    }
    
    # Add widget data
    if include_widget:
        result["widget"] = _build_widget_data(entity, enhanced_dict)
    
    # Add stats if requested and available
    if include_stats and enhanced_dict and enhanced_dict.get("stats"):
        result["stats"] = enhanced_dict.get("stats")
    
    # Add news
    if include_news:
        articles = _fetch_news_articles(entity.name, hours=48)
        result["news"] = {
            "query": entity.name,
            "count": len(articles),
            "articles": articles,
        }
    
    # Compute ETag and cache
    etag = _compute_etag(result)
    cache_data = {**result, "_etag": etag}
    widget_cache.set(cache_key, cache_data, ttl=CACHE_TTL_COMBINED)
    
    # Set response headers
    response.headers["ETag"] = etag
    response.headers["Cache-Control"] = f"public, max-age={CACHE_TTL_ENTITY}"
    response.headers["X-Cache"] = "MISS"
    
    return result


@router.get("/search")
async def search_entities_endpoint(
    response: Response,
    query: str = Query(..., min_length=2),
    sport: str = Query(...),
    entity_type: Optional[str] = Query(None, description="Filter by 'player' or 'team'"),
    limit: int = Query(10, le=50),
):
    """Search entities with caching."""
    sport_upper = sport.upper()
    
    if entity_type and entity_type.lower() not in ("player", "team"):
        raise HTTPException(status_code=400, detail="entity_type must be 'player' or 'team'")
    
    results = search_entities(query, sport_upper, entity_type, limit)
    
    response.headers["Cache-Control"] = "public, max-age=60"
    
    return {
        "query": query,
        "sport": sport_upper,
        "count": len(results),
        "results": [e.to_dict() for e in results],
    }


# ============ Legacy Compatibility Endpoints ============

@router.get("/{entity_type}/{entity_id}/mentions")
async def get_entity_mentions(
    response: Response,
    entity_type: str,
    entity_id: str,
    sport: str = Query(...),
    hours: int = Query(48),
):
    """Get news mentions for an entity (legacy endpoint)."""
    entity = get_entity_or_fallback(entity_type.lower(), entity_id, sport.upper())
    articles = _fetch_news_articles(entity.name, hours=hours)
    
    response.headers["Cache-Control"] = f"public, max-age={CACHE_TTL_NEWS}"
    
    return {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "sport": sport.upper(),
        "entity_info": entity.to_dict(),
        "mentions": articles,
    }
