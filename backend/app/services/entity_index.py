"""
Entity Index - Aho-Corasick based entity matching for news validation.

This module builds an automaton from all known entities (players, teams) in our
databases and provides efficient multi-pattern matching to validate news articles.

Key features:
- O(n) time complexity for matching against all patterns
- Word boundary enforcement to prevent substring false positives
- Disambiguation rules for common names (requires team context)
- Pattern metadata for confidence scoring
"""
import logging
import sqlite3
import unicodedata
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional

import ahocorasick

logger = logging.getLogger(__name__)

# Common surnames that require additional context for disambiguation
# These are surnames shared by many players across sports
COMMON_SURNAMES = frozenset({
    "smith", "johnson", "williams", "brown", "jones", "garcia", "miller",
    "davis", "rodriguez", "martinez", "hernandez", "lopez", "gonzalez",
    "wilson", "anderson", "thomas", "taylor", "moore", "jackson", "martin",
    "lee", "perez", "thompson", "white", "harris", "sanchez", "clark",
    "ramirez", "lewis", "robinson", "walker", "young", "allen", "king",
    "wright", "scott", "torres", "nguyen", "hill", "flores", "green",
    "adams", "nelson", "baker", "hall", "rivera", "campbell", "mitchell",
    "carter", "roberts", "silva", "santos", "costa", "ferreira", "oliveira",
})


class Sport(str, Enum):
    NFL = "NFL"
    NBA = "NBA"
    FOOTBALL = "FOOTBALL"


class PatternType(str, Enum):
    FULL_NAME = "full_name"
    LAST_NAME = "last_name"
    FIRST_LAST = "first_last"
    TEAM_FULL = "team_full"
    TEAM_SHORT = "team_short"
    TEAM_CITY = "team_city"


class EntityType(str, Enum):
    PLAYER = "player"
    TEAM = "team"


@dataclass
class EntityPattern:
    """Metadata attached to each pattern in the automaton."""
    entity_type: EntityType
    entity_id: int
    entity_name: str  # Original full name
    sport: Sport
    pattern_type: PatternType
    requires_context: bool = False  # True for ambiguous patterns
    context_team_id: Optional[int] = None  # Team ID for player disambiguation
    context_team_name: Optional[str] = None  # Team name for matching


@dataclass
class MatchedEntity:
    """A validated entity match with confidence score."""
    entity_type: EntityType
    entity_id: int
    entity_name: str
    sport: Sport
    confidence: str  # "high", "medium", "low"
    matched_patterns: list = field(default_factory=list)
    positions: list = field(default_factory=list)


def normalize_text(text: str) -> str:
    """
    Normalize text for matching.

    - Converts to lowercase
    - Removes accents/diacritics
    - Normalizes whitespace
    - Keeps alphanumeric and spaces only
    """
    # Normalize unicode (NFD decomposes accented chars)
    text = unicodedata.normalize("NFD", text)
    # Remove diacritics (combining characters)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    # Lowercase
    text = text.lower()
    # Replace non-alphanumeric (except space) with space
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    # Normalize whitespace
    text = " ".join(text.split())
    return text


def extract_name_parts(name: str) -> tuple[str, str, list[str]]:
    """
    Extract first name, last name, and all tokens from a name.

    Returns (first_name, last_name, all_tokens)
    """
    tokens = normalize_text(name).split()
    if not tokens:
        return ("", "", [])
    if len(tokens) == 1:
        return (tokens[0], tokens[0], tokens)
    return (tokens[0], tokens[-1], tokens)


def extract_team_parts(team_name: str) -> tuple[str, str, str]:
    """
    Extract city, nickname, and full name from team name.

    e.g., "Kansas City Chiefs" -> ("kansas city", "chiefs", "kansas city chiefs")
    """
    normalized = normalize_text(team_name)
    tokens = normalized.split()
    if not tokens:
        return ("", "", "")
    if len(tokens) == 1:
        return ("", tokens[0], normalized)
    # Assume last token is the team nickname
    city = " ".join(tokens[:-1])
    nickname = tokens[-1]
    return (city, nickname, normalized)


class EntityIndex:
    """
    Aho-Corasick based entity index for efficient multi-pattern matching.

    Usage:
        index = EntityIndex()
        index.load_from_databases("/path/to/instance/localdb")

        # Find entities in text
        matches = index.find_entities("Mahomes leads Chiefs to victory", sport=Sport.NFL)
    """

    def __init__(self):
        self._automaton: Optional[ahocorasick.Automaton] = None
        self._patterns: dict[str, list[EntityPattern]] = {}  # pattern -> metadata list
        self._entities_by_id: dict[tuple[EntityType, int, Sport], EntityPattern] = {}
        self._teams_by_id: dict[tuple[int, Sport], EntityPattern] = {}
        self._loaded = False

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    def load_from_databases(self, db_dir: str | Path) -> None:
        """
        Load all entities from the sport-specific SQLite databases.

        Expected database files:
        - nfl.sqlite
        - nba.sqlite
        - football.sqlite
        """
        db_dir = Path(db_dir)

        sport_dbs = [
            (Sport.NFL, db_dir / "nfl.sqlite"),
            (Sport.NBA, db_dir / "nba.sqlite"),
            (Sport.FOOTBALL, db_dir / "football.sqlite"),
        ]

        self._automaton = ahocorasick.Automaton()
        self._patterns = {}
        self._entities_by_id = {}
        self._teams_by_id = {}

        total_patterns = 0

        for sport, db_path in sport_dbs:
            if not db_path.exists():
                logger.warning(f"Database not found: {db_path}")
                continue

            try:
                conn = sqlite3.connect(str(db_path))
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                # Load teams first (needed for player context)
                team_count = self._load_teams(cursor, sport)
                logger.info(f"Loaded {team_count} teams for {sport.value}")

                # Load players
                player_count = self._load_players(cursor, sport)
                logger.info(f"Loaded {player_count} players for {sport.value}")

                total_patterns += team_count + player_count
                conn.close()

            except Exception as e:
                logger.error(f"Failed to load {sport.value} database: {e}")

        # Build the automaton
        self._automaton.make_automaton()
        self._loaded = True
        logger.info(f"Entity index built with {len(self._patterns)} unique patterns from {total_patterns} entities")

    def _add_pattern(self, pattern: str, metadata: EntityPattern) -> None:
        """Add a pattern to the automaton with associated metadata."""
        pattern = normalize_text(pattern)
        if not pattern or len(pattern) < 2:
            return

        if pattern not in self._patterns:
            self._patterns[pattern] = []
            self._automaton.add_word(pattern, pattern)

        self._patterns[pattern].append(metadata)

    def _load_teams(self, cursor: sqlite3.Cursor, sport: Sport) -> int:
        """Load teams and add patterns for team names."""
        cursor.execute("SELECT id, name, current_league FROM teams")
        count = 0

        for row in cursor.fetchall():
            team_id = row["id"]
            team_name = row["name"]

            city, nickname, full_name = extract_team_parts(team_name)

            # Store team info for player context lookups
            base_pattern = EntityPattern(
                entity_type=EntityType.TEAM,
                entity_id=team_id,
                entity_name=team_name,
                sport=sport,
                pattern_type=PatternType.TEAM_FULL,
                requires_context=False,
            )
            self._teams_by_id[(team_id, sport)] = base_pattern

            # Full team name pattern
            self._add_pattern(full_name, base_pattern)

            # Team nickname only (if 4+ chars to avoid false positives)
            if nickname and len(nickname) >= 4:
                nickname_pattern = EntityPattern(
                    entity_type=EntityType.TEAM,
                    entity_id=team_id,
                    entity_name=team_name,
                    sport=sport,
                    pattern_type=PatternType.TEAM_SHORT,
                    requires_context=False,
                )
                self._add_pattern(nickname, nickname_pattern)

            count += 1

        return count

    def _load_players(self, cursor: sqlite3.Cursor, sport: Sport) -> int:
        """Load players and add patterns for player names."""
        cursor.execute("SELECT id, name, current_team FROM players")
        count = 0

        for row in cursor.fetchall():
            player_id = row["id"]
            player_name = row["name"]
            current_team = row["current_team"]  # This might be team name or None

            first_name, last_name, tokens = extract_name_parts(player_name)
            if not tokens:
                continue

            # Determine if this is a common surname requiring context
            is_common_surname = last_name in COMMON_SURNAMES

            # Try to find team context
            context_team_id = None
            context_team_name = None
            if current_team:
                # Look up team by name match
                for (tid, s), tpattern in self._teams_by_id.items():
                    if s == sport and normalize_text(current_team) in normalize_text(tpattern.entity_name):
                        context_team_id = tid
                        context_team_name = tpattern.entity_name
                        break

            # Full name pattern (high confidence)
            full_name = " ".join(tokens)
            full_pattern = EntityPattern(
                entity_type=EntityType.PLAYER,
                entity_id=player_id,
                entity_name=player_name,
                sport=sport,
                pattern_type=PatternType.FULL_NAME,
                requires_context=False,
                context_team_id=context_team_id,
                context_team_name=context_team_name,
            )
            self._add_pattern(full_name, full_pattern)
            self._entities_by_id[(EntityType.PLAYER, player_id, sport)] = full_pattern

            # Last name only pattern (requires context for common names)
            if len(last_name) >= 4:
                last_pattern = EntityPattern(
                    entity_type=EntityType.PLAYER,
                    entity_id=player_id,
                    entity_name=player_name,
                    sport=sport,
                    pattern_type=PatternType.LAST_NAME,
                    requires_context=is_common_surname,
                    context_team_id=context_team_id,
                    context_team_name=context_team_name,
                )
                self._add_pattern(last_name, last_pattern)

            count += 1

        return count

    def find_entities(
        self,
        text: str,
        sport: Optional[Sport] = None,
        entity_id: Optional[int] = None,
        entity_type: Optional[EntityType] = None,
    ) -> list[MatchedEntity]:
        """
        Find all matching entities in the given text.

        Args:
            text: The text to search (e.g., article title + description)
            sport: Optional filter to only match entities from this sport
            entity_id: Optional filter to only match this specific entity
            entity_type: Required if entity_id is specified

        Returns:
            List of MatchedEntity objects with confidence scores
        """
        if not self._loaded or not self._automaton:
            logger.warning("Entity index not loaded")
            return []

        normalized_text = normalize_text(text)
        if not normalized_text:
            return []

        # Collect all raw matches from the automaton
        raw_matches: list[tuple[int, str, EntityPattern]] = []

        for end_pos, pattern in self._automaton.iter(normalized_text):
            start_pos = end_pos - len(pattern) + 1

            # Word boundary check
            if not self._is_word_boundary(normalized_text, start_pos, end_pos + 1):
                continue

            # Get all metadata for this pattern
            for metadata in self._patterns.get(pattern, []):
                # Apply sport filter
                if sport and metadata.sport != sport:
                    continue

                # Apply entity filter
                if entity_id is not None and entity_type is not None:
                    if metadata.entity_id != entity_id or metadata.entity_type != entity_type:
                        continue

                raw_matches.append((start_pos, pattern, metadata))

        # Group matches by entity and apply disambiguation
        return self._disambiguate_matches(raw_matches, normalized_text)

    def _is_word_boundary(self, text: str, start: int, end: int) -> bool:
        """Check if the match is at word boundaries (not a substring)."""
        # Check character before start
        if start > 0 and text[start - 1].isalnum():
            return False
        # Check character after end
        if end < len(text) and text[end].isalnum():
            return False
        return True

    def _disambiguate_matches(
        self,
        raw_matches: list[tuple[int, str, EntityPattern]],
        text: str,
    ) -> list[MatchedEntity]:
        """
        Apply disambiguation rules to raw matches.

        Rules:
        1. Full name matches -> high confidence
        2. Last name + team context nearby -> medium confidence
        3. Last name only (common) without context -> skip
        4. Team mentions -> high confidence (helps with player context)
        """
        # First pass: collect team mentions for context
        team_mentions: set[int] = set()
        for _, _, meta in raw_matches:
            if meta.entity_type == EntityType.TEAM:
                team_mentions.add(meta.entity_id)

        # Group matches by (entity_type, entity_id, sport)
        entity_groups: dict[tuple[EntityType, int, Sport], list[tuple[int, str, EntityPattern]]] = {}
        for match in raw_matches:
            _, _, meta = match
            key = (meta.entity_type, meta.entity_id, meta.sport)
            if key not in entity_groups:
                entity_groups[key] = []
            entity_groups[key].append(match)

        # Evaluate each entity group
        results: list[MatchedEntity] = []

        for (etype, eid, sport), matches in entity_groups.items():
            # Get the best pattern info
            sample_meta = matches[0][2]

            # Determine confidence
            has_full_name = any(m[2].pattern_type == PatternType.FULL_NAME for m in matches)
            has_team_context = sample_meta.context_team_id in team_mentions if sample_meta.context_team_id else False
            requires_context = any(m[2].requires_context for m in matches)

            if has_full_name:
                confidence = "high"
            elif etype == EntityType.TEAM:
                confidence = "high"
            elif has_team_context:
                confidence = "medium"
            elif requires_context:
                # Skip - common surname without team context
                continue
            else:
                confidence = "medium"

            results.append(MatchedEntity(
                entity_type=etype,
                entity_id=eid,
                entity_name=sample_meta.entity_name,
                sport=sport,
                confidence=confidence,
                matched_patterns=[m[1] for m in matches],
                positions=[m[0] for m in matches],
            ))

        return results

    def get_entity_info(
        self,
        entity_type: EntityType,
        entity_id: int,
        sport: Sport,
    ) -> Optional[EntityPattern]:
        """Look up entity information by ID."""
        return self._entities_by_id.get((entity_type, entity_id, sport))

    def get_team_info(self, team_id: int, sport: Sport) -> Optional[EntityPattern]:
        """Look up team information by ID."""
        return self._teams_by_id.get((team_id, sport))


# Global singleton instance
_entity_index: Optional[EntityIndex] = None


def get_entity_index() -> EntityIndex:
    """Get the global entity index instance."""
    global _entity_index
    if _entity_index is None:
        _entity_index = EntityIndex()
    return _entity_index


def initialize_entity_index(db_dir: str | Path) -> EntityIndex:
    """Initialize the global entity index from databases."""
    global _entity_index
    _entity_index = EntityIndex()
    _entity_index.load_from_databases(db_dir)
    return _entity_index
