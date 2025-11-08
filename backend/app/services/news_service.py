from typing import List, Optional, Dict, Any
import urllib.parse
from datetime import datetime, timedelta
import httpx

from app.services.apisports import apisports_service
from app.database.local_dbs import get_player_by_id as local_get_player_by_id, get_team_by_id as local_get_team_by_id
from app.services.cache import widget_cache

IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.avif')


def _is_probably_image(url: Optional[str], mime: Optional[str]) -> bool:
    if not url:
        return False
    if mime:
        mime_lower = mime.lower()
        if mime_lower.startswith('image/'):
            return True
    url_lower = url.lower()
    return any(url_lower.endswith(ext) for ext in IMAGE_EXTENSIONS)


def _extract_image_url(item):
    import xml.etree.ElementTree as ET
    for elem in item.iter():
        tag = elem.tag.lower() if isinstance(elem.tag, str) else ''
        url = elem.attrib.get('url') if hasattr(elem, 'attrib') else None
        if not url:
            continue
        mime = elem.attrib.get('type') if hasattr(elem, 'attrib') else None
        if tag.endswith('thumbnail'):
            return url
        if tag.endswith('content') and _is_probably_image(url, mime):
            return url
        if tag.endswith('enclosure') and _is_probably_image(url, mime):
            return url
    return None


async def _resolve_entity_name(entity_type: str, entity_id: str, sport: Optional[str]) -> str:
    sport_upper = (sport or "NBA").upper()
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
    try:
        if entity_type == "player":
            row = local_get_player_by_id(sport_upper, int(entity_id))
            if row and row.get("name"):
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
    return entity_id


def parse_rss_feed(xml_content: str) -> List[Dict[str, Any]]:
    import xml.etree.ElementTree as ET
    root = ET.fromstring(xml_content)
    items: List[Dict[str, Any]] = []
    for item in root.findall(".//item"):
        title = item.find("title").text if item.find("title") is not None else ""
        link = item.find("link").text if item.find("link") is not None else ""
        description = item.find("description").text if item.find("description") is not None else ""
        pub_date_raw = item.find("pubDate").text if item.find("pubDate") is not None else ""
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
        image_url = _extract_image_url(item)
        items.append({
            "title": title,
            "link": link,
            "description": description,
            "pub_date": pub_date,
            "source": source,
            "pub_ts": pub_ts,
            "image_url": image_url,
        })
    return items


async def get_entity_mentions(entity_type: str, entity_id: str, sport: Optional[str] = None) -> List[Dict[str, Any]]:
    cache_key = f"rss:mentions:{(sport or 'NBA').upper()}:{entity_type}:{entity_id}"
    cached = widget_cache.get(cache_key)
    if cached is not None:
        return cached
    resolved_name = await _resolve_entity_name(entity_type, entity_id, sport)

    # Try News API first when configured
    from app.services import news_api
    if news_api.is_configured():
        try:
            items, _meta = await news_api.search_news(resolved_name)
            if items:
                widget_cache.set(cache_key, items, ttl=600)
                return items
        except news_api.NewsApiError:
            pass

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
                    widget_cache.set(cache_key, items, ttl=600)
                    return items
            except httpx.HTTPError:
                continue
    widget_cache.set(cache_key, [], ttl=300)
    return []


async def get_entity_mentions_with_debug(entity_type: str, entity_id: str, sport: Optional[str] = None) -> Dict[str, Any]:
    cache_key = f"rss:mentions-debug:{(sport or 'NBA').upper()}:{entity_type}:{entity_id}"
    cached = widget_cache.get(cache_key)
    if cached is not None:
        return cached
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
    selected_provider: Optional[str] = None
    items: List[Dict[str, Any]] = []

    from app.services import news_api
    if news_api.is_configured():
        try:
            cand, meta = await news_api.search_news(resolved_name)
            attempts.append({
                "provider": "news-api",
                "query": meta.get("query"),
                "context": meta.get("language"),
                "url": meta.get("endpoint"),
                "count": len(cand),
            })
            if cand and selected_index is None:
                items = cand
                selected_index = len(attempts) - 1
                selected_provider = "news-api"
        except news_api.NewsApiError as exc:
            attempts.append({
                "provider": "news-api",
                "query": resolved_name,
                "context": None,
                "url": getattr(news_api, "DEFAULT_ENDPOINT", None),
                "count": 0,
                "error": str(exc),
            })

    if selected_index is None:
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
                    attempts.append({
                        "provider": "google",
                        "query": q,
                        "context": window_str,
                        "url": url,
                        "count": count,
                    })
                    if cand and selected_index is None:
                        items = cand
                        selected_index = len(attempts) - 1
                        selected_provider = "google"
                except httpx.HTTPError:
                    attempts.append({
                        "provider": "google",
                        "query": q,
                        "context": window_str,
                        "url": url,
                        "count": 0,
                    })
                    continue
    debug = {
        "resolved_name": resolved_name,
        "attempts": attempts,
        "selected_index": selected_index,
        "selected_provider": selected_provider,
    }
    result = {"mentions": items, "debug": debug}
    widget_cache.set(cache_key, result, ttl=600)
    return result
