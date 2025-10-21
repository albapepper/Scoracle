from typing import List, Optional, Dict, Any
import httpx
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import urllib.parse
from app.services.apisports import apisports_service
from app.db.local_dbs import get_player_by_id as local_get_player_by_id, get_team_by_id as local_get_team_by_id

async def _resolve_entity_name(entity_type: str, entity_id: str, sport: Optional[str]) -> str:
    """Resolve a human-friendly entity name for RSS queries.
    Order: registry -> upstream basic info -> raw id fallback.
    """
    sport_upper = (sport or "NBA").upper()
    # Prefer upstream basic info; fallback to local DB if needed
    try:
        if sport_upper == 'NBA':
            if entity_type == "player":
                info = await apisports_service.get_basketball_player_basic(entity_id)
                fn = (info.get("first_name") or "").strip()
                ln = (info.get("last_name") or "").strip()
                name = f"{fn} {ln}".strip()
                if name:
                    return name
            elif entity_type == "team":
                info = await apisports_service.get_basketball_team_basic(entity_id)
                name = info.get("name") or info.get("abbreviation")
                if name:
                    return name
        elif sport_upper in ('EPL', 'FOOTBALL'):
            if entity_type == "player":
                info = await apisports_service.get_football_player_basic(entity_id)
                fn = (info.get("first_name") or "").strip()
                ln = (info.get("last_name") or "").strip()
                name = f"{fn} {ln}".strip()
                if name:
                    return name
            elif entity_type == "team":
                info = await apisports_service.get_football_team_basic(entity_id)
                name = info.get("name") or info.get("abbreviation")
                if name:
                    return name
    except Exception:
        pass
    # Local DB fallback
    try:
        if entity_type == "player":
            row = local_get_player_by_id(sport_upper, int(entity_id))
            if row and row.get("name"):
                # Reduce to first + last token only
                parts = str(row["name"]).split()
                if parts:
                    first = parts[0]
                    last = "".join(parts[-1:]) if len(parts) > 1 else ""
                    return (first + (" " + last if last else "")).strip()
                return row["name"]
        elif entity_type == "team":
            row = local_get_team_by_id(sport_upper, int(entity_id))
            if row and row.get("name"):
                return row["name"]
    except Exception:
        pass
    return entity_id  # final fallback

async def get_entity_mentions(entity_type: str, entity_id: str, sport: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get mentions of a player or team from Google RSS feed.

    Strategy: try a few increasingly broad searches to avoid empty feeds:
    1) Quoted name with 48h window
    2) Quoted name without time filter
    3) Unquoted name with 7d window
    """
    resolved_name = await _resolve_entity_name(entity_type, entity_id, sport)
    now = datetime.now()
    windows = [timedelta(hours=48), None, timedelta(days=7)]
    queries = [f'"{resolved_name}"', f'"{resolved_name}"', resolved_name]

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
        "Accept": "application/rss+xml,application/xml,text/xml;q=0.9,*/*;q=0.8",
    }

    async with httpx.AsyncClient(headers=headers, timeout=15.0) as client:
        for q, window in zip(queries, windows):
            encoded_term = urllib.parse.quote(q)
            if window:
                time_period = (now - window).strftime('%Y-%m-%dT%H:%M:%SZ')
                url = f"https://news.google.com/rss/search?q={encoded_term}+after:{time_period}&hl=en-US&gl=US&ceid=US:en"
            else:
                url = f"https://news.google.com/rss/search?q={encoded_term}&hl=en-US&gl=US&ceid=US:en"
            try:
                resp = await client.get(url)
                resp.raise_for_status()
                items = parse_rss_feed(resp.text)
                if items:
                    return items
            except httpx.HTTPError:
                # try the next strategy
                continue
    return []

async def get_entity_mentions_with_debug(entity_type: str, entity_id: str, sport: Optional[str] = None) -> Dict[str, Any]:
    """Return mentions along with lightweight debug details.

    debug format:
    {
      resolved_name: str,
      attempts: [ { query: str, window: str|None, url: str, count: int }... ],
      selected_index: int | None
    }
    """
    resolved_name = await _resolve_entity_name(entity_type, entity_id, sport)
    now = datetime.now()
    windows = [timedelta(hours=48), None, timedelta(days=7)]
    queries = [f'"{resolved_name}"', f'"{resolved_name}"', resolved_name]
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
        "Accept": "application/rss+xml,application/xml,text/xml;q=0.9,*/*;q=0.8",
    }
    attempts: List[Dict[str, Any]] = []
    selected_index: Optional[int] = None
    items: List[Dict[str, Any]] = []
    async with httpx.AsyncClient(headers=headers, timeout=15.0) as client:
        for i, (q, window) in enumerate(zip(queries, windows)):
            encoded_term = urllib.parse.quote(q)
            if window:
                time_period = (now - window).strftime('%Y-%m-%dT%H:%M:%SZ')
                url = f"https://news.google.com/rss/search?q={encoded_term}+after:{time_period}&hl=en-US&gl=US&ceid=US:en"
                window_str = f"after {window}"
            else:
                url = f"https://news.google.com/rss/search?q={encoded_term}&hl=en-US&gl=US&ceid=US:en"
                window_str = None
            count = 0
            try:
                resp = await client.get(url)
                resp.raise_for_status()
                cand = parse_rss_feed(resp.text)
                count = len(cand)
                attempts.append({"query": q, "window": window_str, "url": url, "count": count})
                if cand and selected_index is None:
                    items = cand
                    selected_index = i
            except httpx.HTTPError:
                attempts.append({"query": q, "window": window_str, "url": url, "count": 0})
                continue
    debug = {"resolved_name": resolved_name, "attempts": attempts, "selected_index": selected_index}
    return {"mentions": items, "debug": debug}

async def get_related_links(entity_type: str, entity_id: str, category: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get related links for an entity, optionally filtered by category.
    """
    # Format the search query based on entity type, ID, category, and sport
    resolved_name = await _resolve_entity_name(entity_type, entity_id, None)
    search_term = resolved_name
    if category:
        search_term += f" {category}"
    
    # Construct the Google RSS search URL
    encoded_term = urllib.parse.quote(search_term)
    url = f"https://news.google.com/rss/search?q={encoded_term}&hl=en-US&gl=US&ceid=US:en"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        
        # Parse the RSS feed and limit results
        links = parse_rss_feed(response.text)[:limit]
        
        return links

def format_search_term(entity_type: str, resolved_name: str, sport: Optional[str] = None) -> str:
    """Legacy helper retained for compatibility; now returns name only."""
    return resolved_name

def parse_rss_feed(xml_content: str) -> List[Dict[str, Any]]:
    """
    Parse an RSS feed and extract the items.
    """
    root = ET.fromstring(xml_content)
    items = []
    
    # Find all item elements
    for item in root.findall(".//item"):
        # Extract item properties
        title = item.find("title").text if item.find("title") is not None else ""
        link = item.find("link").text if item.find("link") is not None else ""
        description = item.find("description").text if item.find("description") is not None else ""
        pub_date_raw = item.find("pubDate").text if item.find("pubDate") is not None else ""
        # Convert pubDate to ISO and timestamp if possible for easier sorting
        pub_date = pub_date_raw
        pub_ts = None
        try:
            from email.utils import parsedate_to_datetime
            dt = parsedate_to_datetime(pub_date_raw) if pub_date_raw else None
            if dt is not None:
                pub_ts = int(dt.timestamp())
                pub_date = dt.isoformat()
        except Exception:
            pass
        source = item.find("source").text if item.find("source") is not None else ""
        
        items.append({
            "title": title,
            "link": link,
            "description": description,
            "pub_date": pub_date,
            "source": source,
            "pub_ts": pub_ts
        })
    
    return items