"""
Co-mentions Service - Find entities mentioned alongside a searched entity.

Cross-references articles fetched from news providers with entities in the
local database to identify co-mentions. Returns entities sorted by frequency.
"""
import logging
import re
from typing import Any, Dict, List, Optional, Tuple
from collections import Counter

import httpx

from app.database.local_dbs import (
    list_all_players,
    list_all_teams,
    normalize_text,
    get_player_by_id,
    get_team_by_id,
)
from app.services.cache import basic_cache
from app.services.singleflight import singleflight

logger = logging.getLogger(__name__)

# Cache TTL: 10 minutes (same as news)
CO_MENTIONS_CACHE_TTL = 10 * 60


def _get_last_name(name: str) -> Optional[str]:
    """Extract the last name from a player's full name.

    Handles common suffixes like Jr., Sr., II, III, etc.
    Returns None if the name is a single word (to avoid false positives).
    """
    if not name:
        return None
    parts = name.split()
    if len(parts) <= 1:
        return None  # Single word names - don't match on just the name

    last = parts[-1]
    suffixes = {"jr", "jr.", "sr", "sr.", "ii", "iii", "iv", "v"}
    if last.lower().strip(". ") in suffixes and len(parts) >= 3:
        last = parts[-2]

    return last if len(last) >= 4 else None  # Require at least 4 chars for last name


def _build_entity_patterns(
    players: List[Tuple[int, str]], teams: List[Tuple[int, str]]
) -> Dict[str, Tuple[str, int, str]]:
    """
    Build a lookup dictionary for entity matching.

    Returns a dict mapping normalized name -> (entity_type, entity_id, display_name)

    For players, also adds last name as a pattern for better matching since
    news articles often use just last names (e.g., "Semenyo" instead of "Antoine Semenyo").
    """
    patterns: Dict[str, Tuple[str, int, str]] = {}

    for player_id, player_name in players:
        if not player_name:
            continue
        norm = normalize_text(player_name)
        if norm and len(norm) >= 3:  # Skip very short names to avoid false matches
            patterns[norm] = ("player", player_id, player_name)

        # Also add last name as a pattern for players
        last_name = _get_last_name(player_name)
        if last_name:
            norm_last = normalize_text(last_name)
            # Only add if not already taken by another entity (avoid collisions)
            if norm_last and norm_last not in patterns:
                patterns[norm_last] = ("player", player_id, player_name)

    for team_id, team_name in teams:
        if not team_name:
            continue
        norm = normalize_text(team_name)
        if norm and len(norm) >= 3:
            patterns[norm] = ("team", team_id, team_name)

    return patterns


def _find_mentions_in_text(
    text: str,
    entity_patterns: Dict[str, Tuple[str, int, str]],
    exclude_entity_id: Optional[int] = None,
    exclude_entity_type: Optional[str] = None,
) -> List[Tuple[str, int, str]]:
    """
    Find all entity mentions in a text string.

    Returns list of (entity_type, entity_id, display_name) for each match.
    """
    if not text:
        return []

    normalized_text = normalize_text(text)
    found: List[Tuple[str, int, str]] = []

    for norm_name, (entity_type, entity_id, display_name) in entity_patterns.items():
        # Skip the entity being searched for
        if exclude_entity_id is not None and exclude_entity_type is not None:
            if entity_id == exclude_entity_id and entity_type == exclude_entity_type:
                continue

        # Check if the normalized name appears in the text
        # Use word boundary matching to avoid partial matches
        # For multi-word names, check if all words appear in sequence
        words = norm_name.split()
        if len(words) == 1:
            # Single word: check with word boundaries
            pattern = r'\b' + re.escape(norm_name) + r'\b'
            if re.search(pattern, normalized_text):
                found.append((entity_type, entity_id, display_name))
        else:
            # Multi-word: check if the phrase exists
            if norm_name in normalized_text:
                found.append((entity_type, entity_id, display_name))

    return found


async def get_co_mentions(
    client: httpx.AsyncClient,
    entity_type: str,
    entity_id: int,
    sport: str,
    hours: int = 48,
) -> List[Dict[str, Any]]:
    """
    Get entities co-mentioned with the given entity in recent news articles.

    1. Fetches the entity's details to get its name
    2. Fetches news articles for that entity
    3. Scans articles for mentions of other entities in the same sport's database
    4. Returns entities sorted by mention frequency

    Args:
        client: Async HTTP client for fetching news
        entity_type: "player" or "team"
        entity_id: The entity's database ID
        sport: Sport code (e.g., "FOOTBALL", "NBA", "NFL")
        hours: Hours to look back for news (default 48)

    Returns:
        List of co-mentioned entities with frequency counts
    """
    cache_key = f"co_mentions:{sport}:{entity_type}:{entity_id}:{hours}"
    cached = basic_cache.get(cache_key)
    if cached is not None:
        logger.debug(f"Co-mentions cache HIT: {cache_key}")
        return cached

    async def _work() -> List[Dict[str, Any]]:
        # Re-check cache after singleflight wait
        cached2 = basic_cache.get(cache_key)
        if cached2 is not None:
            return cached2

        # 1. Get the entity's name for article search
        if entity_type == "player":
            entity = get_player_by_id(sport, entity_id)
            entity_name = entity.get("name") if entity else None
        else:
            entity = get_team_by_id(sport, entity_id)
            entity_name = entity.get("name") if entity else None

        if not entity_name:
            logger.warning(f"Entity not found: {entity_type}/{entity_id} in {sport}")
            return []

        # 2. Fetch news articles for this entity
        from app.routers.news import _fetch_news_async
        articles = await _fetch_news_async(client, entity_name, hours=hours)

        if not articles:
            logger.info(f"No articles found for {entity_name}")
            basic_cache.set(cache_key, [], ttl=CO_MENTIONS_CACHE_TTL)
            return []

        # 3. Load all entities from the sport's database
        players = list_all_players(sport)
        teams = list_all_teams(sport)

        # Build pattern dictionary for matching
        entity_patterns = _build_entity_patterns(players, teams)

        # 4. Scan articles for entity mentions
        mention_counter: Counter[Tuple[str, int, str]] = Counter()

        for article in articles:
            title = article.get("title", "")
            # Combine title for scanning (could also include description if available)
            text_to_scan = title

            mentions = _find_mentions_in_text(
                text_to_scan,
                entity_patterns,
                exclude_entity_id=entity_id,
                exclude_entity_type=entity_type,
            )

            for mention in mentions:
                mention_counter[mention] += 1

        # 5. Build sorted results
        results: List[Dict[str, Any]] = []
        for (ent_type, ent_id, display_name), count in mention_counter.most_common():
            results.append({
                "entity_type": ent_type,
                "entity_id": ent_id,
                "name": display_name,
                "mention_count": count,
            })

        # Cache results
        basic_cache.set(cache_key, results, ttl=CO_MENTIONS_CACHE_TTL)
        logger.info(f"Co-mentions cache SET: {cache_key} ({len(results)} entities)")

        return results

    try:
        return await singleflight.do(cache_key, _work)
    except Exception as e:
        logger.error(f"Co-mentions error for {entity_type}/{entity_id}: {e}")
        return []
