"""
Unified Entity Router - Single endpoint for all entity operations.

Provides entity info, widget data, and news mentions in one call.
Simplifies frontend by reducing multiple API calls to one.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import JSONResponse

from app.services.entity_service import get_entity_or_fallback, search_entities, get_all_entities, EntityInfo

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/entity", tags=["entities"])


# ============ Simple News Fetching ============

def _fetch_news_articles(query: str, hours: int = 48) -> List[Dict[str, Any]]:
    """
    Fetch news articles from Google News RSS.
    
    Simple, direct approach - no complex entity matching.
    """
    try:
        import feedparser
        from datetime import datetime, timedelta, timezone
        import time
        
        # Clean query for RSS
        rss_url = f"https://news.google.com/rss/search?q={query.replace(' ', '+')}"
        feed = feedparser.parse(rss_url)
        
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        articles = []
        
        for entry in getattr(feed, "entries", []) or []:
            # Filter by date
            try:
                if getattr(entry, "published_parsed", None):
                    dt = datetime.fromtimestamp(time.mktime(entry.published_parsed)).replace(tzinfo=timezone.utc)
                    if dt < cutoff:
                        continue
            except Exception:
                pass
            
            # Extract article info
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
        
        return articles[:20]  # Limit to 20 articles
        
    except Exception as e:
        logger.error(f"Failed to fetch news for '{query}': {e}")
        return []


# ============ Widget Data Generation ============

def _build_widget_data(entity: EntityInfo) -> Dict[str, Any]:
    """
    Build widget display data from entity info.
    
    Simple approach - just format the bundled data nicely.
    No external API calls needed.
    """
    if entity.entity_type == "player":
        return {
            "type": "player",
            "id": entity.id,
            "name": entity.name,
            "first_name": entity.first_name,
            "last_name": entity.last_name,
            "team": entity.team,
            "sport": entity.sport,
            "display_name": entity.name,
            "subtitle": entity.team or entity.sport,
        }
    else:
        return {
            "type": "team",
            "id": entity.id,
            "name": entity.name,
            "league": entity.league,
            "sport": entity.sport,
            "display_name": entity.name,
            "subtitle": entity.league or entity.sport,
        }


# ============ Main Endpoints ============

@router.get("/{entity_type}/{entity_id}")
async def get_entity_unified(
    entity_type: str,
    entity_id: str,
    sport: str = Query(..., description="Sport code: NBA, NFL, FOOTBALL"),
    include: str = Query("widget,news", description="Comma-separated: widget, news"),
):
    """
    Unified entity endpoint - returns entity info with optional widget and news.
    
    This single endpoint replaces:
    - /{sport}/players/{id}
    - /{sport}/teams/{id}
    - /{sport}/players/{id}/widget/basic
    - /{sport}/teams/{id}/widget/basic
    - /news/fast/{entity_type}/{entity_id}
    
    Example: GET /entity/player/123?sport=FOOTBALL&include=widget,news
    """
    sport_upper = sport.upper()
    entity_type_lower = entity_type.lower()
    
    if entity_type_lower not in ("player", "team"):
        raise HTTPException(status_code=400, detail="entity_type must be 'player' or 'team'")
    
    if sport_upper not in ("NBA", "NFL", "FOOTBALL"):
        raise HTTPException(status_code=400, detail="sport must be NBA, NFL, or FOOTBALL")
    
    # Get entity info (never fails)
    entity = get_entity_or_fallback(entity_type_lower, entity_id, sport_upper)
    
    # Parse includes
    includes = [x.strip().lower() for x in include.split(",")]
    
    # Build response
    response: Dict[str, Any] = {
        "entity": entity.to_dict(),
    }
    
    # Add widget data
    if "widget" in includes:
        response["widget"] = _build_widget_data(entity)
    
    # Add news
    if "news" in includes:
        # Use entity name for news search
        articles = _fetch_news_articles(entity.name, hours=48)
        response["news"] = {
            "query": entity.name,
            "count": len(articles),
            "articles": articles,
        }
    
    return response


@router.get("/search")
async def search_entities_endpoint(
    query: str = Query(..., min_length=2),
    sport: str = Query(...),
    entity_type: Optional[str] = Query(None, description="Filter by 'player' or 'team'"),
    limit: int = Query(10, le=50),
):
    """
    Search entities - backend version of autocomplete.
    
    Useful for cases where frontend autocomplete isn't available.
    """
    sport_upper = sport.upper()
    
    if entity_type and entity_type.lower() not in ("player", "team"):
        raise HTTPException(status_code=400, detail="entity_type must be 'player' or 'team'")
    
    results = search_entities(query, sport_upper, entity_type, limit)
    
    return {
        "query": query,
        "sport": sport_upper,
        "count": len(results),
        "results": [e.to_dict() for e in results],
    }


# ============ Legacy Compatibility ============
# These endpoints maintain backwards compatibility with existing frontend code

@router.get("/{entity_type}/{entity_id}/mentions")
async def get_entity_mentions(
    entity_type: str,
    entity_id: str,
    sport: str = Query(...),
    hours: int = Query(48),
):
    """
    Get news mentions for an entity.
    
    Legacy endpoint for backwards compatibility.
    New code should use GET /entity/{type}/{id}?include=news
    """
    entity = get_entity_or_fallback(entity_type.lower(), entity_id, sport.upper())
    articles = _fetch_news_articles(entity.name, hours=hours)
    
    return {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "sport": sport.upper(),
        "entity_info": entity.to_dict(),
        "mentions": articles,
    }

