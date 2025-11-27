"""Shared utilities for sport-scoped routers."""
from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List

from fastapi import HTTPException

from app.database.local_dbs import (
    get_player_by_id,
    get_team_by_id,
    local_search_players,
    local_search_teams,
)
from app.services.apisports import apisports_service


def local_player_summary_payload(sport: str, player_id: str, *, raise_on_missing: bool = True) -> Dict[str, Any] | None:
    row = get_player_by_id(sport, int(player_id))
    if not row:
        if raise_on_missing:
            raise HTTPException(status_code=404, detail="Player not found")
        return None
    name = row.get("name") or ""
    parts = name.split()
    return {
        "id": row["id"],
        "first_name": parts[0] if parts else None,
        "last_name": " ".join(parts[1:]) if len(parts) > 1 else None,
        "position": None,
        "team": {
            "id": None,
            "name": row.get("current_team"),
            "abbreviation": row.get("current_team"),
        },
    }


def local_team_summary_payload(sport: str, team_id: str, *, raise_on_missing: bool = True) -> Dict[str, Any] | None:
    row = get_team_by_id(sport, int(team_id))
    if not row:
        if raise_on_missing:
            raise HTTPException(status_code=404, detail="Team not found")
        return None
    return {
        "id": row["id"],
        "name": row["name"],
        "abbreviation": row["name"],
        "city": None,
        "conference": None,
        "division": None,
    }


def local_player_profile_payload(sport: str, player_id: str) -> Dict[str, Any]:
    row = get_player_by_id(sport, int(player_id))
    if not row:
        raise HTTPException(status_code=404, detail="Player not found")
    name = row.get("name") or ""
    parts = name.split()
    return {
        "id": row["id"],
        "firstname": parts[0] if parts else None,
        "lastname": " ".join(parts[1:]) if len(parts) > 1 else None,
        "name": name,
    }


def local_team_profile_payload(sport: str, team_id: str) -> Dict[str, Any]:
    row = get_team_by_id(sport, int(team_id))
    if not row:
        raise HTTPException(status_code=404, detail="Team not found")
    return {"id": row["id"], "name": row["name"]}


async def get_player_info(sport: str, player_id: str) -> Dict[str, Any]:
    """Fetch player profile for widget rendering."""
    s = sport.upper()
    if s == "NBA":
        try:
            return await apisports_service.get_nba_player_profile(player_id)
        except Exception:
            return local_player_profile_payload(s, player_id)
    if s == "FOOTBALL":
        try:
            return await apisports_service.get_football_player_profile(player_id)
        except Exception:
            return local_player_profile_payload(s, player_id)
    if s == "NFL":
        try:
            return await apisports_service.get_nfl_player_profile(player_id)
        except Exception:
            return local_player_profile_payload(s, player_id)
    raise HTTPException(status_code=501, detail=f"Player widget not implemented for sport {s}")


async def get_team_info(sport: str, team_id: str) -> Dict[str, Any]:
    """Fetch team profile for widget rendering."""
    s = sport.upper()
    if s == "NBA":
        try:
            return await apisports_service.get_nba_team_profile(team_id)
        except Exception:
            return local_team_profile_payload(s, team_id)
    if s == "FOOTBALL":
        try:
            return await apisports_service.get_football_team_profile(team_id)
        except Exception:
            return local_team_profile_payload(s, team_id)
    if s == "NFL":
        try:
            return await apisports_service.get_nfl_team_profile(team_id)
        except Exception:
            return local_team_profile_payload(s, team_id)
    raise HTTPException(status_code=501, detail=f"Team widget not implemented for sport {s}")


async def get_player_stats(sport: str, player_id: str, season: str | None = None) -> Dict[str, Any]:
    s = sport.upper()
    season_norm = season if (season and season.lower() != "current") else None
    if s == "NBA":
        try:
            return await apisports_service.get_basketball_player_statistics(player_id, season_norm) or {}
        except Exception:
            return {}
    return {}


async def get_team_stats(sport: str, team_id: str, season: str | None = None) -> Dict[str, Any]:
    s = sport.upper()
    season_norm = season if (season and season.lower() != "current") else None
    if s == "NBA":
        try:
            return await apisports_service.get_basketball_team_statistics(team_id, season_norm) or {}
        except Exception:
            return {}
    return {}


def summarize_comentions_for_mentions(
    sport: str,
    mentions: List[Dict[str, Any]],
    target_entity: tuple[str, str],
) -> List[Dict[str, Any]]:
    te_type, te_id = target_entity
    counts: Dict[tuple[str, str], Dict[str, Any]] = {}

    def add_hit(e_type: str, e_id: str, name: str):
        key = (e_type, e_id)
        if key == (te_type, te_id):
            return
        entry = counts.get(key)
        if not entry:
            entry = {"entity_type": e_type, "id": e_id, "name": name, "hits": 0}
            counts[key] = entry
        entry["hits"] += 1

    def extract_phrases(text: str) -> List[str]:
        import re

        words = re.findall(r"[A-Za-z][A-Za-z\-'\.]+", text or "")
        phrases: List[str] = []
        n = len(words)
        for size in (3, 2):
            for i in range(n - size + 1):
                phrase = " ".join(words[i : i + size]).strip()
                if len(phrase) >= 4:
                    phrases.append(phrase)
        for w in words:
            if len(w) >= 5:
                phrases.append(w)
        seen = set()
        uniq: List[str] = []
        for p in phrases:
            pl = p.lower()
            if pl in seen:
                continue
            seen.add(pl)
            uniq.append(p)
        return uniq[:10]

    for item in mentions:
        text = f"{item.get('title') or ''}. {item.get('description') or ''}"
        for phrase in extract_phrases(text):
            try:
                for r in local_search_players(sport, phrase, limit=2):
                    add_hit("player", str(r.get("id")), r.get("name") or "")
                for r in local_search_teams(sport, phrase, limit=2):
                    add_hit("team", str(r.get("id")), r.get("name") or "")
            except Exception:
                continue

    out = list(counts.values())
    out.sort(key=lambda x: x["hits"], reverse=True)
    return out[:20]


def hash_bootstrap_payload(payload: Dict[str, Any]) -> str:
    try:
        data = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    except Exception:
        data = repr(payload).encode("utf-8")
    return hashlib.sha256(data).hexdigest()[:32]
