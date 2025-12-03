"""JSON-based database module for player and team entity data.

This module replaces the SQLite-based local_dbs.py for serverless environments
like Vercel where the filesystem is read-only. It loads JSON files from 
backend/data/ and caches them in memory using @lru_cache.
"""
from __future__ import annotations

import json
import os
import re
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Tuple

_NON_ALNUM = re.compile(r"[^a-z0-9 ]+")


def _get_data_dir() -> Path:
    """Return the path to the backend/data directory."""
    # Try relative to this file first (most reliable)
    here = Path(__file__).resolve()
    backend_root = here.parents[2]  # backend/app/database -> backend
    data_dir = backend_root / "data"
    if data_dir.exists():
        return data_dir

    # Try Vercel serverless paths
    vercel_paths = [
        Path("/var/task/backend/data"),
        Path("/var/task/data"),
    ]
    for p in vercel_paths:
        if p.exists():
            return p

    # Fallback to relative path (may not exist)
    return data_dir


def _sport_to_filename(sport: str) -> str:
    """Map sport name to JSON filename."""
    s = (sport or "").strip().upper()
    mapping = {
        "NBA": "nba.json",
        "NFL": "nfl.json",
        "FOOTBALL": "football.json",
        "EPL": "football.json",  # Alias for European football
    }
    return mapping.get(s, f"{s.lower()}.json")


def _data_file_path(sport: str) -> str:
    """Return the path to the JSON data file for a sport."""
    data_dir = _get_data_dir()
    filename = _sport_to_filename(sport)
    return str(data_dir / filename)


@lru_cache(maxsize=10)
def _load_sport_data(sport: str) -> Dict:
    """Load and cache JSON data for a sport.

    Returns a dict with 'players' and 'teams' keys, each containing
    'count' and 'items' lists.
    """
    data_dir = _get_data_dir()
    filename = _sport_to_filename(sport)
    filepath = data_dir / filename

    if not filepath.exists():
        # Return empty structure if file doesn't exist
        return {"players": {"count": 0, "items": []}, "teams": {"count": 0, "items": []}}

    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def normalize_text(s: Optional[str]) -> str:
    """Normalize text for search: strip accents, lowercase, remove non-alphanum."""
    if not s:
        return ""
    s_norm = unicodedata.normalize("NFKD", s)
    s_ascii = "".join(ch for ch in s_norm if not unicodedata.combining(ch))
    s_lower = s_ascii.lower()
    s_clean = _NON_ALNUM.sub(" ", s_lower)
    return " ".join(s_clean.split())


def _strip_specials_preserve_case(s: Optional[str]) -> str:
    """Remove accents and non-alphanumeric characters while preserving case."""
    if not s:
        return ""
    s_norm = unicodedata.normalize("NFKD", s)
    s_ascii = "".join(ch for ch in s_norm if not unicodedata.combining(ch))
    out = []
    for ch in s_ascii:
        if ch.isalnum() or ch == " ":
            out.append(ch)
    s_clean = "".join(out)
    return " ".join(s_clean.split())


def _first_last_only(name: Optional[str]) -> str:
    """Reduce a display name to only first and last tokens."""
    if not name:
        return ""
    parts = str(name).split()
    if len(parts) <= 1:
        return parts[0] if parts else ""
    first = parts[0]
    last = parts[-1]
    suffixes = {"jr", "jr.", "sr", "sr.", "ii", "iii", "iv", "v"}
    if last.lower().strip(". ") in suffixes and len(parts) >= 3:
        last = parts[-2]
    return f"{first} {last}".strip()


def _build_player_name(player: Dict) -> str:
    """Build display name from player dict (firstName + lastName)."""
    fn = (player.get("firstName") or "").strip()
    ln = (player.get("lastName") or "").strip()
    full_name = f"{fn} {ln}".strip()
    # Clean and reduce to first/last
    display_raw = _strip_specials_preserve_case(full_name)
    return _first_last_only(display_raw) or full_name


def get_player_by_id(sport: str, player_id: int) -> Optional[Dict[str, Optional[str]]]:
    """Get a player by ID from the JSON data."""
    data = _load_sport_data(sport)
    players = data.get("players", {}).get("items", [])

    for p in players:
        if p.get("id") == player_id:
            name = _build_player_name(p)
            return {
                "id": p.get("id"),
                "name": name,
                "current_team": p.get("currentTeam"),
            }
    return None


def get_team_by_id(sport: str, team_id: int) -> Optional[Dict[str, Optional[str]]]:
    """Get a team by ID from the JSON data."""
    data = _load_sport_data(sport)
    teams = data.get("teams", {}).get("items", [])

    for t in teams:
        if t.get("id") == team_id:
            return {
                "id": t.get("id"),
                "name": t.get("name"),
                "current_league": t.get("league"),
            }
    return None


def list_all_players(sport: str) -> List[Tuple[int, str]]:
    """Return all players (id, name) for a sport.

    Intended for building in-memory indexes (e.g., Aho-Corasick).
    """
    data = _load_sport_data(sport)
    players = data.get("players", {}).get("items", [])

    result = []
    for p in players:
        pid = p.get("id")
        name = _build_player_name(p)
        if pid is not None and name:
            result.append((int(pid), name))
    return result


def list_all_teams(sport: str) -> List[Tuple[int, str]]:
    """Return all teams (id, name) for a sport.

    Intended for building in-memory indexes (e.g., Aho-Corasick).
    """
    data = _load_sport_data(sport)
    teams = data.get("teams", {}).get("items", [])

    result = []
    for t in teams:
        tid = t.get("id")
        name = t.get("name", "")
        if tid is not None and name:
            result.append((int(tid), str(name)))
    return result


def search_players(sport: str, q: str, limit: int = 10) -> List[Dict[str, Optional[str]]]:
    """Search for players matching a query string."""
    data = _load_sport_data(sport)
    players = data.get("players", {}).get("items", [])

    nq = normalize_text(q)
    if not nq:
        return []

    # Build candidate list with scores
    candidates = []
    tokens = nq.split()

    for p in players:
        name = _build_player_name(p)
        norm_name = normalize_text(name)

        # Check if query matches (substring or all tokens present)
        if nq in norm_name:
            match_quality = 2  # Direct substring match
        elif all(t in norm_name for t in tokens):
            match_quality = 1  # All tokens present
        else:
            continue

        candidates.append({
            "id": p.get("id"),
            "name": name,
            "current_team": p.get("currentTeam"),
            "norm_name": norm_name,
            "match_quality": match_quality,
        })

    # Try fuzzy matching if no exact matches found
    if not candidates:
        try:
            from rapidfuzz import fuzz

            for p in players:
                name = _build_player_name(p)
                norm_name = normalize_text(name)
                score = fuzz.WRatio(nq, norm_name)
                if score >= 60:  # Minimum threshold
                    candidates.append({
                        "id": p.get("id"),
                        "name": name,
                        "current_team": p.get("currentTeam"),
                        "norm_name": norm_name,
                        "score": score,
                    })
        except ImportError:
            pass

    # Sort candidates
    if candidates and "score" in candidates[0]:
        # Fuzzy match - sort by score descending
        candidates.sort(key=lambda x: x.get("score", 0), reverse=True)
    else:
        # Exact match - sort by match quality, then name length (prefer shorter)
        candidates.sort(key=lambda x: (-x.get("match_quality", 0), len(x.get("norm_name", ""))))

    # Return results
    result = []
    for c in candidates[:limit]:
        result.append({
            "id": c.get("id"),
            "name": c.get("name"),
            "current_team": c.get("current_team"),
        })
    return result


def search_teams(sport: str, q: str, limit: int = 10) -> List[Dict[str, Optional[str]]]:
    """Search for teams matching a query string."""
    data = _load_sport_data(sport)
    teams = data.get("teams", {}).get("items", [])

    nq = normalize_text(q)
    if not nq:
        return []

    # Build candidate list with scores
    candidates = []
    tokens = nq.split()

    for t in teams:
        name = t.get("name", "")
        norm_name = normalize_text(name)

        # Check if query matches (substring or all tokens present)
        if nq in norm_name:
            match_quality = 2  # Direct substring match
        elif all(tok in norm_name for tok in tokens):
            match_quality = 1  # All tokens present
        else:
            continue

        candidates.append({
            "id": t.get("id"),
            "name": name,
            "current_league": t.get("league"),
            "norm_name": norm_name,
            "match_quality": match_quality,
        })

    # Try fuzzy matching if no exact matches found
    if not candidates:
        try:
            from rapidfuzz import fuzz

            for t in teams:
                name = t.get("name", "")
                norm_name = normalize_text(name)
                score = fuzz.WRatio(nq, norm_name)
                if score >= 60:  # Minimum threshold
                    candidates.append({
                        "id": t.get("id"),
                        "name": name,
                        "current_league": t.get("league"),
                        "norm_name": norm_name,
                        "score": score,
                    })
        except ImportError:
            pass

    # Sort candidates
    if candidates and "score" in candidates[0]:
        # Fuzzy match - sort by score descending
        candidates.sort(key=lambda x: x.get("score", 0), reverse=True)
    else:
        # Exact match - sort by match quality, then name length (prefer shorter)
        candidates.sort(key=lambda x: (-x.get("match_quality", 0), len(x.get("norm_name", ""))))

    # Return results
    result = []
    for c in candidates[:limit]:
        result.append({
            "id": c.get("id"),
            "name": c.get("name"),
            "current_league": c.get("current_league"),
        })
    return result
