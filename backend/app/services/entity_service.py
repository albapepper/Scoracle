"""
Unified Entity Service - Single source of truth for all entity data.

This service provides entity information from bundled JSON data,
with optional API-Sports enhancement for live data.
"""
from __future__ import annotations

import json
import os
import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

# In-memory cache for bundled data
_DATA_CACHE: Dict[str, Dict[str, Any]] = {}


@dataclass
class EntityInfo:
    """Unified entity information structure."""
    id: str
    name: str
    entity_type: str  # 'player' or 'team'
    sport: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    team: Optional[str] = None  # For players: their current team
    league: Optional[str] = None  # For teams: their league
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "entity_type": self.entity_type,
            "sport": self.sport,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "team": self.team,
            "league": self.league,
        }


def _get_bundled_data_path() -> Path:
    """Get path to bundled JSON data directory."""
    # Check multiple locations for flexibility
    candidates = [
        Path(__file__).parent.parent.parent.parent / "frontend" / "public" / "data",
        Path(__file__).parent.parent.parent.parent / "frontend" / "dist" / "data",
        Path("/var/task/frontend/dist/data"),  # Vercel
        Path("/var/task/data"),  # Vercel alternative
    ]
    
    for path in candidates:
        if path.exists():
            return path
    
    # Fallback to first candidate (will fail gracefully if not found)
    return candidates[0]


def _load_sport_data(sport: str) -> Dict[str, Any]:
    """Load bundled JSON data for a sport."""
    sport_upper = sport.upper()
    
    if sport_upper in _DATA_CACHE:
        return _DATA_CACHE[sport_upper]
    
    data_dir = _get_bundled_data_path()
    sport_lower = sport_upper.lower()
    json_path = data_dir / f"{sport_lower}.json"
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            _DATA_CACHE[sport_upper] = data
            logger.info(f"Loaded {sport_upper} data: {data.get('players', {}).get('count', 0)} players, {data.get('teams', {}).get('count', 0)} teams")
            return data
    except FileNotFoundError:
        logger.warning(f"Bundled data not found for {sport_upper} at {json_path}")
        return {"players": {"items": []}, "teams": {"items": []}}
    except Exception as e:
        logger.error(f"Failed to load bundled data for {sport_upper}: {e}")
        return {"players": {"items": []}, "teams": {"items": []}}


def get_entity(entity_type: str, entity_id: str, sport: str) -> Optional[EntityInfo]:
    """
    Get entity info from bundled data.
    
    This is the primary method - fast and always works.
    """
    sport_upper = sport.upper()
    data = _load_sport_data(sport_upper)
    
    try:
        id_int = int(entity_id)
    except ValueError:
        id_int = None
    
    if entity_type == "player":
        for player in data.get("players", {}).get("items", []):
            if player.get("id") == id_int or str(player.get("id")) == entity_id:
                first_name = player.get("firstName", "")
                last_name = player.get("lastName", "")
                name = f"{first_name} {last_name}".strip() or f"Player {entity_id}"
                return EntityInfo(
                    id=str(player.get("id")),
                    name=name,
                    entity_type="player",
                    sport=sport_upper,
                    first_name=first_name or None,
                    last_name=last_name or None,
                    team=player.get("currentTeam"),
                )
    
    elif entity_type == "team":
        for team in data.get("teams", {}).get("items", []):
            if team.get("id") == id_int or str(team.get("id")) == entity_id:
                return EntityInfo(
                    id=str(team.get("id")),
                    name=team.get("name", f"Team {entity_id}"),
                    entity_type="team",
                    sport=sport_upper,
                    league=team.get("league"),
                )
    
    # Not found in bundled data
    logger.debug(f"Entity not found in bundled data: {entity_type}/{entity_id}/{sport_upper}")
    return None


def get_entity_or_fallback(entity_type: str, entity_id: str, sport: str) -> EntityInfo:
    """
    Get entity info, with fallback to minimal data if not found.
    
    This never fails - always returns something usable.
    """
    entity = get_entity(entity_type, entity_id, sport)
    if entity:
        return entity
    
    # Create fallback entity
    sport_upper = sport.upper()
    if entity_type == "player":
        return EntityInfo(
            id=entity_id,
            name=f"Player {entity_id}",
            entity_type="player",
            sport=sport_upper,
        )
    else:
        return EntityInfo(
            id=entity_id,
            name=f"Team {entity_id}",
            entity_type="team",
            sport=sport_upper,
        )


def search_entities(query: str, sport: str, entity_type: Optional[str] = None, limit: int = 10) -> List[EntityInfo]:
    """
    Search entities in bundled data.
    
    This provides the same functionality as the frontend autocomplete,
    but on the backend for cases where frontend can't do it.
    """
    sport_upper = sport.upper()
    data = _load_sport_data(sport_upper)
    query_lower = query.lower().strip()
    
    if len(query_lower) < 2:
        return []
    
    results: List[EntityInfo] = []
    
    # Search players
    if entity_type in (None, "player"):
        for player in data.get("players", {}).get("items", []):
            first_name = player.get("firstName", "")
            last_name = player.get("lastName", "")
            name = f"{first_name} {last_name}".strip()
            if query_lower in name.lower():
                results.append(EntityInfo(
                    id=str(player.get("id")),
                    name=name,
                    entity_type="player",
                    sport=sport_upper,
                    first_name=first_name or None,
                    last_name=last_name or None,
                    team=player.get("currentTeam"),
                ))
    
    # Search teams
    if entity_type in (None, "team"):
        for team in data.get("teams", {}).get("items", []):
            name = team.get("name", "")
            if query_lower in name.lower():
                results.append(EntityInfo(
                    id=str(team.get("id")),
                    name=name,
                    entity_type="team",
                    sport=sport_upper,
                    league=team.get("league"),
                ))
    
    return results[:limit]


def get_all_entities(sport: str, entity_type: str) -> List[EntityInfo]:
    """Get all entities of a type for a sport (for entity matching in news)."""
    sport_upper = sport.upper()
    data = _load_sport_data(sport_upper)
    results: List[EntityInfo] = []
    
    if entity_type == "player":
        for player in data.get("players", {}).get("items", []):
            first_name = player.get("firstName", "")
            last_name = player.get("lastName", "")
            name = f"{first_name} {last_name}".strip()
            if name:
                results.append(EntityInfo(
                    id=str(player.get("id")),
                    name=name,
                    entity_type="player",
                    sport=sport_upper,
                    first_name=first_name or None,
                    last_name=last_name or None,
                    team=player.get("currentTeam"),
                ))
    
    elif entity_type == "team":
        for team in data.get("teams", {}).get("items", []):
            name = team.get("name", "")
            if name:
                results.append(EntityInfo(
                    id=str(team.get("id")),
                    name=name,
                    entity_type="team",
                    sport=sport_upper,
                    league=team.get("league"),
                ))
    
    return results

