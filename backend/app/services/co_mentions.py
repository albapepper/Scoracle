"""
Co-mentions service - Analyze articles to find entities mentioned together.

This service cross-references the local DB with articles to identify which
entities are frequently mentioned alongside a given entity.
"""
import logging
from typing import List, Dict, Tuple, Any
from collections import Counter
import re

from app.database.local_dbs import list_all_players, list_all_teams

logger = logging.getLogger(__name__)


def _build_entity_index(sport: str) -> Dict[str, Tuple[str, str, str]]:
    """Build an index of entity names for fast matching.
    
    Returns a dict mapping normalized entity names to (entity_type, entity_id, display_name).
    Uses case-insensitive matching for better results.
    """
    index = {}
    
    # Add all players
    try:
        players = list_all_players(sport)
        for player_id, name in players:
            # Use lowercase for matching
            key = name.lower().strip()
            if key:
                index[key] = ("player", str(player_id), name)
    except Exception as e:
        logger.warning(f"Failed to load players for co-mentions: {e}")
    
    # Add all teams
    try:
        teams = list_all_teams(sport)
        for team_id, name in teams:
            key = name.lower().strip()
            if key:
                index[key] = ("team", str(team_id), name)
    except Exception as e:
        logger.warning(f"Failed to load teams for co-mentions: {e}")
    
    return index


def _extract_entity_mentions(text: str, entity_index: Dict[str, Tuple[str, str, str]]) -> List[Tuple[str, str, str]]:
    """Extract all entity mentions from text.
    
    Returns list of (entity_type, entity_id, display_name) tuples.
    Uses simple case-insensitive substring matching.
    """
    if not text:
        return []
    
    text_lower = text.lower()
    mentions = []
    
    # Sort by length descending to match longer names first (e.g., "Manchester United" before "Manchester")
    sorted_entities = sorted(entity_index.items(), key=lambda x: len(x[0]), reverse=True)
    
    # Track already matched positions to avoid overlapping matches
    matched_positions = set()
    
    for entity_name, (entity_type, entity_id, display_name) in sorted_entities:
        # Find all occurrences of this entity name
        start = 0
        while True:
            pos = text_lower.find(entity_name, start)
            if pos == -1:
                break
            
            # Check if this position overlaps with an already matched entity
            end_pos = pos + len(entity_name)
            if any(p in matched_positions for p in range(pos, end_pos)):
                start = pos + 1
                continue
            
            # Mark these positions as matched
            for p in range(pos, end_pos):
                matched_positions.add(p)
            
            mentions.append((entity_type, entity_id, display_name))
            start = pos + len(entity_name)
    
    return mentions


def analyze_co_mentions(
    entity_type: str,
    entity_id: str,
    entity_name: str,
    sport: str,
    articles: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Analyze articles to find entities mentioned alongside the target entity.
    
    Args:
        entity_type: Type of the target entity ("player" or "team")
        entity_id: ID of the target entity
        entity_name: Name of the target entity
        sport: Sport code (NBA, NFL, FOOTBALL)
        articles: List of article dicts with "title" and optionally "summary"
        
    Returns:
        List of co-mentioned entities with counts, sorted by frequency descending.
        Each item has: entity_type, entity_id, name, count
    """
    # Build entity index for this sport
    entity_index = _build_entity_index(sport)
    
    if not entity_index:
        logger.warning(f"No entities found in local DB for sport {sport}")
        return []
    
    # Count co-mentions
    co_mention_counter = Counter()
    target_key = entity_name.lower().strip()
    
    for article in articles:
        # Combine title and summary for analysis
        text = f"{article.get('title', '')} {article.get('summary', '')}"
        
        # Extract all entity mentions from this article
        mentions = _extract_entity_mentions(text, entity_index)
        
        # Check if target entity is mentioned
        target_mentioned = False
        mentioned_entities = set()
        
        for ent_type, ent_id, ent_name in mentions:
            key = (ent_type, ent_id)
            mentioned_entities.add(key)
            
            # Check if this is the target entity
            if ent_type == entity_type and ent_id == entity_id:
                target_mentioned = True
            elif ent_name.lower().strip() == target_key:
                target_mentioned = True
        
        # If target is mentioned, count all other entities in this article
        if target_mentioned:
            for ent_type, ent_id in mentioned_entities:
                # Don't count the target entity itself
                if not (ent_type == entity_type and ent_id == entity_id):
                    if not (entity_index.get(ent_type, ("", "", ""))[2].lower().strip() == target_key):
                        co_mention_counter[(ent_type, ent_id)] += 1
    
    # Build result list
    results = []
    for (ent_type, ent_id), count in co_mention_counter.most_common():
        # Find the display name
        display_name = None
        for name_key, (e_type, e_id, d_name) in entity_index.items():
            if e_type == ent_type and e_id == ent_id:
                display_name = d_name
                break
        
        if display_name:
            results.append({
                "entity_type": ent_type,
                "entity_id": ent_id,
                "name": display_name,
                "count": count
            })
    
    return results
