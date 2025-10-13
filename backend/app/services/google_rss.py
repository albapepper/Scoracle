from typing import List, Optional, Dict, Any
import httpx
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import urllib.parse
from app.services.apisports import apisports_service

async def _resolve_entity_name(entity_type: str, entity_id: str, sport: Optional[str]) -> str:
    """Resolve a human-friendly entity name for RSS queries.
    Order: registry -> upstream basic info -> raw id fallback.
    """
    sport_upper = (sport or "NBA").upper()
    # Registry lookup removed for simplicity; resolve via upstream only
    # Upstream basic info fallback
    try:
        if sport_upper == 'NBA':
            if entity_type == "player":
                info = await apisports_service.get_basketball_player_basic(entity_id)
                fn = info.get("first_name") or ""
                ln = info.get("last_name") or ""
                name = f"{fn} {ln}".strip()
                if name:
                    return name
            elif entity_type == "team":
                info = await apisports_service.get_basketball_team_basic(entity_id)
                name = info.get("name") or info.get("abbreviation")
                if name:
                    return name
        elif sport_upper == 'EPL':
            if entity_type == "player":
                info = await apisports_service.get_football_player_basic(entity_id)
                fn = info.get("first_name") or ""
                ln = info.get("last_name") or ""
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
    return entity_id  # final fallback

async def get_entity_mentions(entity_type: str, entity_id: str, sport: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get mentions of a player or team from Google RSS feed.
    """
    # Format the search query based on entity type, ID, and sport
    resolved_name = await _resolve_entity_name(entity_type, entity_id, sport)
    search_term = format_search_term(entity_type, resolved_name, sport)
    
    # Calculate timestamp for 36 hours ago
    time_period = (datetime.now() - timedelta(hours=36)).strftime('%Y-%m-%dT%H:%M:%SZ')
    
    # Construct the Google RSS search URL
    encoded_term = urllib.parse.quote(search_term)
    url = f"https://news.google.com/rss/search?q={encoded_term}+after:{time_period}&hl=en-US&gl=US&ceid=US:en"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        
        # Parse the RSS feed
        mentions = parse_rss_feed(response.text)
        
        return mentions

async def get_related_links(entity_type: str, entity_id: str, category: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get related links for an entity, optionally filtered by category.
    """
    # Format the search query based on entity type, ID, category, and sport
    resolved_name = await _resolve_entity_name(entity_type, entity_id, None)
    search_term = format_search_term(entity_type, resolved_name)
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

def format_search_term(entity_type: str, entity_id: str, sport: Optional[str] = None) -> str:
    """
    Format the search term based on entity type, ID, and sport.
    This is a placeholder and would need to be replaced with actual logic
    to convert entity IDs to names based on the API responses.
    """
    # In a real implementation, this would look up the entity name from the ID
    # For now, we'll just use the ID as the search term
    search_term = entity_id
    
    if sport:
        search_term += f" {sport}"
        
    if entity_type == "player":
        search_term += " player"
    elif entity_type == "team":
        search_term += " team"
        
    return search_term

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
        pub_date = item.find("pubDate").text if item.find("pubDate") is not None else ""
        source = item.find("source").text if item.find("source") is not None else ""
        
        items.append({
            "title": title,
            "link": link,
            "description": description,
            "pub_date": pub_date,
            "source": source
        })
    
    return items