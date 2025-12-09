"""
Enhanced Entity Service - Combines bundled data with optional API-Sports enhancement.

Security: API key never leaves the backend.
Efficiency: Aggressive caching minimizes API calls.

Data Tiers:
- Tier 1: Bundled JSON (always available, free, instant)
- Tier 2: Cached API-Sports data (enhanced, cached for hours)
- Tier 3: Fresh API-Sports data (on-demand, careful use)
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional
from dataclasses import dataclass, field

from app.services.entity_service import get_entity_or_fallback, EntityInfo
from app.services.cache import widget_cache
from app.services.apisports import apisports_service

logger = logging.getLogger(__name__)

# Cache TTLs (seconds)
CACHE_ENHANCED_PROFILE = 6 * 3600    # 6 hours for profile data
CACHE_ENHANCED_STATS = 2 * 3600      # 2 hours for stats (changes after games)


@dataclass
class EnhancedEntityData:
    """Enhanced entity data combining bundled + API-Sports data."""
    # Basic info (always available from bundled JSON)
    entity: EntityInfo
    
    # Enhanced profile data (from API-Sports, optional)
    photo_url: Optional[str] = None
    position: Optional[str] = None
    height: Optional[str] = None
    weight: Optional[str] = None
    age: Optional[int] = None
    nationality: Optional[str] = None
    
    # Team enhanced data
    logo_url: Optional[str] = None
    conference: Optional[str] = None
    division: Optional[str] = None
    
    # Stats (from API-Sports, optional)
    stats: Dict[str, Any] = field(default_factory=dict)
    
    # Meta
    enhanced: bool = False  # True if API-Sports data was fetched
    
    def to_dict(self) -> Dict[str, Any]:
        base = self.entity.to_dict()
        base.update({
            "photo_url": self.photo_url,
            "position": self.position,
            "height": self.height,
            "weight": self.weight,
            "age": self.age,
            "nationality": self.nationality,
            "logo_url": self.logo_url,
            "conference": self.conference,
            "division": self.division,
            "stats": self.stats if self.stats else None,
            "enhanced": self.enhanced,
        })
        return {k: v for k, v in base.items() if v is not None}


def _cache_key(prefix: str, *args) -> str:
    return ":".join([prefix] + [str(a).upper() for a in args])


async def get_enhanced_entity(
    entity_type: str,
    entity_id: str,
    sport: str,
    include_stats: bool = False,
    force_refresh: bool = False,
) -> EnhancedEntityData:
    """
    Get entity with optional API-Sports enhancement.
    
    Always returns data (falls back to bundled JSON if API fails).
    API key is never exposed to frontend.
    
    Args:
        entity_type: 'player' or 'team'
        entity_id: Entity ID
        sport: 'NBA', 'NFL', or 'FOOTBALL'
        include_stats: Whether to fetch stats (more API calls)
        force_refresh: Skip cache and fetch fresh
    """
    sport_upper = sport.upper()
    entity_type_lower = entity_type.lower()
    
    # Step 1: Get basic info from bundled JSON (always works, instant)
    entity = get_entity_or_fallback(entity_type_lower, entity_id, sport_upper)
    result = EnhancedEntityData(entity=entity)
    
    # Step 2: Check cache for enhanced data
    cache_key = _cache_key("enhanced", entity_type_lower, entity_id, sport_upper, str(include_stats))
    
    if not force_refresh:
        cached = widget_cache.get(cache_key)
        if cached is not None:
            logger.debug(f"Enhanced cache hit: {entity_type_lower}/{entity_id}")
            return cached
    
    # Step 3: Try to enhance with API-Sports (backend only, key is secure)
    try:
        if entity_type_lower == "player":
            result = await _enhance_player(entity, sport_upper, include_stats)
        else:
            result = await _enhance_team(entity, sport_upper, include_stats)
        
        # Cache the enhanced result
        ttl = CACHE_ENHANCED_STATS if include_stats else CACHE_ENHANCED_PROFILE
        widget_cache.set(cache_key, result, ttl=ttl)
        
    except Exception as e:
        logger.warning(f"API-Sports enhancement failed for {entity_type_lower}/{entity_id}: {e}")
        # Return basic data without enhancement
        result.enhanced = False
    
    return result


async def _enhance_player(entity: EntityInfo, sport: str, include_stats: bool) -> EnhancedEntityData:
    """Enhance player data with API-Sports."""
    result = EnhancedEntityData(entity=entity)
    
    try:
        # Fetch profile based on sport
        if sport == "NBA":
            profile = await apisports_service.get_nba_player_profile(entity.id)
            _extract_nba_player_profile(profile, result)
            
            if include_stats:
                stats = await apisports_service.get_basketball_player_statistics(entity.id)
                result.stats = stats if stats else {}
                
        elif sport == "FOOTBALL":
            profile = await apisports_service.get_football_player_profile(entity.id)
            _extract_football_player_profile(profile, result)
            
        elif sport == "NFL":
            profile = await apisports_service.get_nfl_player_profile(entity.id)
            _extract_nfl_player_profile(profile, result)
        
        result.enhanced = True
        
    except Exception as e:
        logger.warning(f"Player enhancement failed: {e}")
        result.enhanced = False
    
    return result


async def _enhance_team(entity: EntityInfo, sport: str, include_stats: bool) -> EnhancedEntityData:
    """Enhance team data with API-Sports."""
    result = EnhancedEntityData(entity=entity)
    
    try:
        if sport == "NBA":
            profile = await apisports_service.get_nba_team_profile(entity.id)
            _extract_nba_team_profile(profile, result)
            
            if include_stats:
                stats = await apisports_service.get_basketball_team_statistics(entity.id)
                result.stats = stats if stats else {}
                
        elif sport == "FOOTBALL":
            profile = await apisports_service.get_football_team_profile(entity.id)
            _extract_football_team_profile(profile, result)
            
        elif sport == "NFL":
            profile = await apisports_service.get_nfl_team_profile(entity.id)
            _extract_nfl_team_profile(profile, result)
        
        result.enhanced = True
        
    except Exception as e:
        logger.warning(f"Team enhancement failed: {e}")
        result.enhanced = False
    
    return result


# ============ Profile Extractors ============

def _extract_nba_player_profile(profile: Dict[str, Any], result: EnhancedEntityData):
    """Extract relevant fields from NBA player profile."""
    if not profile:
        return
    
    # NBA API structure: direct fields on player object
    result.photo_url = profile.get("photo")
    
    # Height/weight from nested birth or directly
    birth = profile.get("birth") or {}
    result.nationality = birth.get("country")
    
    # NBA v2 returns height/weight in nested structures
    height_obj = profile.get("height") or {}
    weight_obj = profile.get("weight") or {}
    
    if isinstance(height_obj, dict):
        result.height = height_obj.get("feets") or height_obj.get("meters")
    elif height_obj:
        result.height = str(height_obj)
        
    if isinstance(weight_obj, dict):
        result.weight = weight_obj.get("pounds") or weight_obj.get("kilograms")
    elif weight_obj:
        result.weight = str(weight_obj)
    
    # Position from leagues.standard or direct
    leagues = profile.get("leagues") or {}
    standard = leagues.get("standard") or {}
    result.position = standard.get("pos") or profile.get("position")
    
    # Calculate age from birthdate if available
    if birth.get("date"):
        try:
            from datetime import datetime
            bd = datetime.strptime(birth["date"], "%Y-%m-%d")
            today = datetime.now()
            result.age = today.year - bd.year - ((today.month, today.day) < (bd.month, bd.day))
        except Exception:
            pass


def _extract_football_player_profile(profile: Dict[str, Any], result: EnhancedEntityData):
    """Extract relevant fields from Football player profile."""
    if not profile:
        return
    
    player = profile.get("player") or profile
    
    result.photo_url = player.get("photo")
    result.nationality = player.get("nationality")
    result.age = player.get("age")
    result.height = player.get("height")
    result.weight = player.get("weight")
    
    # Position from statistics if available
    stats = profile.get("statistics") or []
    if stats and isinstance(stats, list) and len(stats) > 0:
        games = stats[0].get("games") or {}
        result.position = games.get("position")


def _extract_nfl_player_profile(profile: Dict[str, Any], result: EnhancedEntityData):
    """Extract relevant fields from NFL player profile."""
    if not profile:
        return
    
    result.photo_url = profile.get("image")
    result.position = profile.get("position")
    result.height = profile.get("height")
    result.weight = profile.get("weight")
    result.age = profile.get("age")
    
    # NFL might have college info
    college = profile.get("college")
    if college:
        result.nationality = f"College: {college}"


def _extract_nba_team_profile(profile: Dict[str, Any], result: EnhancedEntityData):
    """Extract relevant fields from NBA team profile."""
    if not profile:
        return
    
    result.logo_url = profile.get("logo")
    
    leagues = profile.get("leagues") or {}
    standard = leagues.get("standard") or {}
    result.conference = standard.get("conference")
    result.division = standard.get("division")


def _extract_football_team_profile(profile: Dict[str, Any], result: EnhancedEntityData):
    """Extract relevant fields from Football team profile."""
    if not profile:
        return
    
    team = profile.get("team") or profile
    result.logo_url = team.get("logo")
    
    venue = profile.get("venue") or {}
    if venue:
        # Store venue info
        result.division = venue.get("name")  # Stadium name


def _extract_nfl_team_profile(profile: Dict[str, Any], result: EnhancedEntityData):
    """Extract relevant fields from NFL team profile."""
    if not profile:
        return
    
    team = profile.get("team") or profile
    result.logo_url = profile.get("logo") or team.get("logo")
    result.conference = team.get("conference")
    result.division = team.get("division")

