from __future__ import annotations

from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import time
import unicodedata
import re
import feedparser  # faster and robust RSS parser

from app.database.json_db import list_all_players, list_all_teams, get_player_by_id as local_get_player_by_id, get_team_by_id as local_get_team_by_id
from app.services.cache import widget_cache
from app.services.apisports import apisports_service


@dataclass(frozen=True)
class AliasMatcher:
    alias_map: Dict[str, str]
    alias_entries: List[Tuple[str, str, int]]  # (alias, canonical, length)

    @property
    def empty(self) -> bool:
        return not self.alias_entries


_PLAYER_MATCHERS: dict[str, AliasMatcher] = {}
_CLUB_MATCHERS: dict[str, AliasMatcher] = {}

_NON_ALNUM = re.compile(r"[^a-z0-9 ]+")


def _normalize_name(s: str) -> str:
    s_norm = unicodedata.normalize("NFKD", s)
    s_ascii = "".join(ch for ch in s_norm if not unicodedata.combining(ch))
    s_lower = s_ascii.lower()
    s_clean = _NON_ALNUM.sub(" ", s_lower)
    return " ".join(s_clean.split())


def _first_last_only(name: str) -> str:
    parts = name.split()
    if len(parts) <= 1:
        return parts[0] if parts else ""
    first = parts[0]
    last = parts[-1]
    suffixes = {"jr", "jr.", "sr", "sr.", "ii", "iii", "iv", "v"}
    if last.lower().strip(". ") in suffixes and len(parts) >= 3:
        last = parts[-2]
    return f"{first} {last}".strip()


def _add_aliases(aliases: Dict[str, List[str]], replacements: List[Tuple[str, str]]) -> Dict[str, List[str]]:
    new_aliases: Dict[str, List[str]] = {}
    for norm_alias, canon_list in list(aliases.items()):
        for old, new in replacements:
            if old in norm_alias:
                alt_alias = norm_alias.replace(old, new)
                if alt_alias not in aliases:
                    new_aliases[alt_alias] = canon_list
    aliases.update(new_aliases)
    return aliases


def _build_matcher(aliases: Dict[str, List[str]]) -> AliasMatcher:
    alias_map: Dict[str, str] = {}
    alias_entries: List[Tuple[str, str, int]] = []
    for norm_alias, name_list in aliases.items():
        if not norm_alias or not name_list:
            continue
        canonical = name_list[0]
        alias_map[norm_alias] = canonical
        alias_entries.append((norm_alias, canonical, len(norm_alias)))
    alias_entries.sort(key=lambda item: item[2], reverse=True)
    return AliasMatcher(alias_map=alias_map, alias_entries=alias_entries)


def _load_aliases_for_sport(sport: str) -> Tuple[Dict[str, List[str]], Dict[str, List[str]]]:
    """Build alias dictionaries from local DB lists with light normalization.

    Returns (player_aliases, club_aliases) mapping normalized alias -> [canonicalDisplay]
    """
    players = list_all_players(sport)
    teams = list_all_teams(sport)
    p_aliases: Dict[str, List[str]] = {}
    c_aliases: Dict[str, List[str]] = {}

    for _pid, name in players:
        disp = _first_last_only(name)
        norm = _normalize_name(disp or name)
        if not norm:
            continue
        p_aliases.setdefault(norm, []).append(disp or name)

    for _tid, name in teams:
        disp = name  # keep team full name
        norm = _normalize_name(disp)
        if not norm:
            continue
        c_aliases.setdefault(norm, []).append(disp)

    s = sport.upper()
    if s in ("EPL", "FOOTBALL"):
        # Common football alias expansions
        c_aliases = _add_aliases(c_aliases, [
            ("utd", "united"), ("united", "utd"),
            ("manchester united", "man united"), ("man united", "manchester united"),
            ("manchester city", "man city"), ("man city", "manchester city"),
            ("man united", "man u"), ("man u", "man united"),
            ("nott ham forest", "nottingham forest"), ("nottingham forest", "nott ham forest"),
        ])

    return p_aliases, c_aliases


def _get_matchers(sport: str) -> Tuple[AliasMatcher, AliasMatcher]:
    s = (sport or "NBA").upper()
    cache_key = f"news_fast:automata:{s}"
    cached = widget_cache.get(cache_key)
    if cached is not None:
        return cached[0], cached[1]

    p_aliases, c_aliases = _load_aliases_for_sport(s)
    P = _build_matcher(p_aliases)
    C = _build_matcher(c_aliases)
    widget_cache.set(cache_key, (P, C), ttl=3600)
    _PLAYER_MATCHERS[s] = P
    _CLUB_MATCHERS[s] = C
    return P, C


def _filter_recent(entries: List[Any], hours: int = 48) -> List[Any]:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    out: List[Any] = []
    for e in entries:
        try:
            if getattr(e, "published_parsed", None):
                dt = datetime.fromtimestamp(time.mktime(e.published_parsed)).replace(tzinfo=timezone.utc)
                if dt > cutoff:
                    out.append(e)
        except Exception:
            continue
    return out


def fetch_recent_articles(query: str, hours: int = 48) -> List[Any]:
    rss_url = f"https://news.google.com/rss/search?q={query.replace(' ', '+')}"
    feed = feedparser.parse(rss_url)
    return _filter_recent(getattr(feed, "entries", []) or [], hours=hours)


def _find_entities(text: str, matcher: AliasMatcher) -> Set[str]:
    if matcher.empty:
        return set()
    norm_text = _normalize_name(text)
    raw: List[Tuple[int, int, str, int]] = []  # (start, end, canon, length)
    for alias, canon, alias_len in matcher.alias_entries:
        start_idx = 0
        while True:
            found_at = norm_text.find(alias, start_idx)
            if found_at == -1:
                break
            end_idx = found_at + alias_len - 1
            is_start_boundary = found_at == 0 or not norm_text[found_at - 1].isalnum()
            is_end_boundary = end_idx == len(norm_text) - 1 or not norm_text[end_idx + 1].isalnum()
            if is_start_boundary and is_end_boundary:
                raw.append((found_at, end_idx, canon, alias_len))
            start_idx = found_at + 1
    if not raw:
        return set()
    raw.sort(key=lambda x: (x[0], -x[3]))
    accepted: List[Tuple[int, int, str, int]] = []
    for s, e, canon, length in raw:
        skip = False
        for as_, ae_, acanon, alen in accepted:
            if as_ <= s and e <= ae_ and (alen >= length) and acanon != canon:
                skip = True
                break
        if not skip:
            accepted.append((s, e, canon, length))
    return {canon for _, _, canon, _ in accepted}


def extract_entities_from_entry(entry: Any, P: AliasMatcher, C: AliasMatcher) -> Tuple[Set[str], Set[str]]:
    title = getattr(entry, "title", "") or ""
    desc = getattr(entry, "summary", None) or getattr(entry, "description", "") or ""
    text = f"{title} {desc}"
    found_players = _find_entities(text, P)
    found_teams = _find_entities(text, C)
    return found_players, found_teams


def rank_mentions_for_team(articles: List[Any], team: str, P: AliasMatcher, C: AliasMatcher) -> List[Tuple[str, int, List[str]]]:
    links_by_player: Dict[str, Set[str]] = {}
    for e in articles:
        players, teams = extract_entities_from_entry(e, P, C)
        if team in teams:
            for p in players:
                if p != team:
                    links_by_player.setdefault(p, set()).add(getattr(e, "link", ""))
    ranked = [(p, len(links), sorted(list(links))) for p, links in links_by_player.items()]
    ranked.sort(key=lambda x: x[1], reverse=True)
    return ranked


def rank_mentions_for_player(articles: List[Any], player: str, P: AliasMatcher, C: AliasMatcher, exclude_team: Optional[str] = None) -> List[Tuple[str, int, List[str]]]:
    links_by_team: Dict[str, Set[str]] = {}
    for e in articles:
        players, teams = extract_entities_from_entry(e, P, C)
        if player in players:
            for t in teams:
                if (exclude_team is None) or (t != exclude_team):
                    links_by_team.setdefault(t, set()).add(getattr(e, "link", ""))
    ranked = [(t, len(links), sorted(list(links))) for t, links in links_by_team.items()]
    ranked.sort(key=lambda x: x[1], reverse=True)
    return ranked


def summarize_entry(entry: Any) -> Dict[str, Any]:
    """Optimized to return only essential fields: title, link, source, pub_date."""
    title = getattr(entry, "title", "") or ""
    link = getattr(entry, "link", "") or ""
    pub_iso = None
    try:
        if getattr(entry, "published_parsed", None):
            dt = datetime.fromtimestamp(time.mktime(entry.published_parsed)).replace(tzinfo=timezone.utc)
            pub_iso = dt.isoformat()
    except Exception:
        pass
    source = getattr(entry, "source", {}).get("title") if isinstance(getattr(entry, "source", None), dict) else ""
    return {"title": title, "link": link, "pub_date": pub_iso, "source": source}


def _cascading_entries(resolved_query: str, hours: int) -> List[Any]:
    """Perform cascading RSS queries efficiently:

    1) quoted with given hours (default 48)
    2) quoted broadened to 7 days (only if step 1 empty)
    3) unquoted 7 days
    """
    q_quoted = f'"{resolved_query}"'
    q_unquoted = resolved_query

    # First attempt: quoted within the requested window
    entries = fetch_recent_articles(q_quoted, hours=hours)
    if entries:
        return entries

    # Second attempt: same quoted term but broaden time window to up to 7 days
    broader_hours = 168 if hours < 168 else hours
    if broader_hours != hours:
        entries = fetch_recent_articles(q_quoted, hours=broader_hours)
        if entries:
            return entries

    # Third attempt: unquoted broader search (7 days minimum)
    entries = fetch_recent_articles(q_unquoted, hours=max(48, min(168, broader_hours)))
    return entries


def _detect_longest_match(norm_query: str, matcher: AliasMatcher) -> Tuple[Optional[str], int]:
    """Return (canonical, longest_alias_len) matched in normalized query using matcher."""
    if matcher.empty or not norm_query:
        return None, 0
    best_canon: Optional[str] = None
    best_len = 0
    for alias, canon, alias_len in matcher.alias_entries:
        if alias_len < best_len:
            break
        if norm_query.find(alias) != -1:
            best_len = alias_len
            best_canon = canon
    return best_canon, best_len


async def resolve_entity_name(entity_type: str, entity_id: str, sport: Optional[str]) -> str:
    """Resolve a human-friendly entity name for RSS queries.
    Order: upstream basic info -> local DB -> raw id fallback.
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


def fast_mentions(query: str, sport: str, hours: int = 48, mode: str = "auto") -> Dict[str, Any]:
    """High-performance mentions pipeline with entity-mode logic and cascading queries.

    mode:
      - player: treat query primarily as a player, rank teams they appear with
      - team: treat query as a team, rank players appearing with team
      - auto: decide by presence in automata (prefer player match > team match)
    """
    P, C = _get_matchers(sport)
    q_norm = _normalize_name(query)
    # Auto-detect with confidence based on longest alias proportion of normalized query
    detected_player, player_match_len = _detect_longest_match(q_norm, P)
    detected_team, team_match_len = _detect_longest_match(q_norm, C)
    norm_len = max(1, len(q_norm))
    player_conf = round(min(1.0, player_match_len / norm_len), 3) if detected_player else 0.0
    team_conf = round(min(1.0, team_match_len / norm_len), 3) if detected_team else 0.0
    resolved_mode = mode
    if mode == "auto":
        if detected_player and (player_conf >= team_conf):
            resolved_mode = "player"
        elif detected_team:
            resolved_mode = "team"
        else:
            resolved_mode = "player"  # default bias toward player

    entries = _cascading_entries(query.strip(), hours=hours)
    articles = [summarize_entry(e) for e in entries]

    # Aggregate
    players_acc: Dict[str, int] = {}
    teams_acc: Dict[str, int] = {}
    links_by_player: Dict[str, Set[str]] = {}
    links_by_team: Dict[str, Set[str]] = {}
    for e in entries:
        players, teams = extract_entities_from_entry(e, P, C)
        for p in players:
            players_acc[p] = players_acc.get(p, 0) + 1
            links_by_player.setdefault(p, set()).add(getattr(e, "link", ""))
        for t in teams:
            teams_acc[t] = teams_acc.get(t, 0) + 1
            links_by_team.setdefault(t, set()).add(getattr(e, "link", ""))

    # Exclusion logic: if player mode and we can infer current club from co-occurrence highest frequency
    exclude_club: Optional[str] = None
    if resolved_mode == "player" and detected_player:
        # heuristic: choose team with highest count in entries where player is present as 'current'
        team_counts: Dict[str, int] = {}
        for e in entries:
            players, teams = extract_entities_from_entry(e, P, C)
            if detected_player in players:
                for t in teams:
                    team_counts[t] = team_counts.get(t, 0) + 1
        if team_counts:
            exclude_club = max(team_counts.items(), key=lambda x: x[1])[0]

    ranked_players = [(p, cnt, sorted(list(links_by_player.get(p, set())))) for p, cnt in sorted(players_acc.items(), key=lambda x: x[1], reverse=True)]
    ranked_teams = [(t, cnt, sorted(list(links_by_team.get(t, set())))) for t, cnt in sorted(teams_acc.items(), key=lambda x: x[1], reverse=True)]

    if resolved_mode == "player" and detected_player:
        # For player mode: rank teams excluding inferred current club
        filtered_team = [(t, c, lnks) for (t, c, lnks) in ranked_teams if t != exclude_club]
        return {
            "mode": resolved_mode,
            "query": query,
            "detected_player": detected_player,
            "detected_player_confidence": player_conf,
            "exclude_club": exclude_club,
            "articles": articles,
            "linked_teams": filtered_team,
            "raw_team_rank": ranked_teams,
        }
    if resolved_mode == "team" and detected_team:
        # For team mode: rank players appearing with team (already aggregated); exclude the team itself from players list obviously
        linked_players = [(p, c, lnks) for (p, c, lnks) in ranked_players if p != detected_team]
        return {
            "mode": resolved_mode,
            "query": query,
            "detected_team": detected_team,
            "detected_team_confidence": team_conf,
            "articles": articles,
            "linked_players": linked_players,
            "raw_player_rank": ranked_players,
        }
    # Fallback generic
    return {
        "mode": resolved_mode,
        "query": query,
        "detected_player": detected_player,
        "detected_player_confidence": player_conf,
        "detected_team": detected_team,
        "detected_team_confidence": team_conf,
        "articles": articles,
        "players": ranked_players,
        "teams": ranked_teams,
    }
