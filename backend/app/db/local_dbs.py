import os
import re
import sqlite3
import threading
import time
import unicodedata
from typing import List, Dict, Tuple, Optional

# Lightweight per-sport SQLite management for autocomplete data

_INIT_LOCK = threading.Lock()
_INITIALIZED: set[str] = set()


def _db_dir() -> str:
    # Default under project instance folder
    return os.getenv("LOCAL_DB_DIR", os.path.join(os.getcwd(), "instance", "localdb"))


def _db_path_for_sport(sport: str) -> str:
    s = (sport or "").strip().upper()
    fname = {
        "NBA": "nba.sqlite",
        "NFL": "nfl.sqlite",
        "FOOTBALL": "football.sqlite",
        "EPL": "football.sqlite",  # alias for backward compatibility
    }.get(s, f"{s.lower()}.sqlite")
    return os.path.join(_db_dir(), fname)


def _connect(path: str) -> sqlite3.Connection:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    conn = sqlite3.connect(path, isolation_level=None, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA temp_store=MEMORY;")
    return conn


def _ensure_schema(conn: sqlite3.Connection):
    # Base tables
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            current_team TEXT,
            updated_at INTEGER NOT NULL,
            normalized_name TEXT,
            tokens TEXT
        );
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS teams (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            current_league TEXT,
            updated_at INTEGER NOT NULL,
            normalized_name TEXT,
            tokens TEXT
        );
        """
    )

    # Migrate if columns missing (ALTER TABLE ADD COLUMN)
    def _has_col(table: str, col: str) -> bool:
        cur = conn.execute(f"PRAGMA table_info({table});")
        return any(row[1] == col for row in cur.fetchall())

    for tbl in ("players", "teams"):
        if not _has_col(tbl, "normalized_name"):
            conn.execute(f"ALTER TABLE {tbl} ADD COLUMN normalized_name TEXT;")
        if not _has_col(tbl, "tokens"):
            conn.execute(f"ALTER TABLE {tbl} ADD COLUMN tokens TEXT;")

    # Indexes
    conn.execute("CREATE INDEX IF NOT EXISTS idx_players_name ON players(name);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_players_norm ON players(normalized_name);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_players_tokens ON players(tokens);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_teams_name ON teams(name);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_teams_norm ON teams(normalized_name);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_teams_tokens ON teams(tokens);")


_NON_ALNUM = re.compile(r"[^a-z0-9 ]+")

def normalize_text(s: Optional[str]) -> str:
    if not s:
        return ""
    # strip accents, lower, remove non-alphanum, collapse spaces
    s_norm = unicodedata.normalize("NFKD", s)
    s_ascii = "".join(ch for ch in s_norm if not unicodedata.combining(ch))
    s_lower = s_ascii.lower()
    s_clean = _NON_ALNUM.sub(" ", s_lower)
    s_sp = " ".join(s_clean.split())
    return s_sp

def tokenize(s: str) -> str:
    # Space-separated tokens used for LIKE queries (e.g., "% token %")
    return " ".join(s.split())


def _strip_specials_preserve_case(s: Optional[str]) -> str:
    """Remove accents and non-alphanumeric characters while preserving case for display.

    - Strips diacritics
    - Removes any character not in [A-Za-z0-9 ]
    - Collapses multiple spaces
    """
    if not s:
        return ""
    s_norm = unicodedata.normalize("NFKD", s)
    s_ascii = "".join(ch for ch in s_norm if not unicodedata.combining(ch))
    # Keep alnum and spaces only
    out = []
    for ch in s_ascii:
        if ch.isalnum() or ch == " ":
            out.append(ch)
        else:
            # drop punctuation and symbols
            continue
    s_clean = "".join(out)
    return " ".join(s_clean.split())


def _init_if_needed(sport: str):
    s = (sport or "").upper()
    if s in _INITIALIZED:
        return
    with _INIT_LOCK:
        if s in _INITIALIZED:
            return
        path = _db_path_for_sport(s)
        conn = _connect(path)
        try:
            _ensure_schema(conn)
        finally:
            conn.close()
        _INITIALIZED.add(s)


def upsert_players(sport: str, rows: List[Tuple[int, str, Optional[str]]]):
    """
    Upsert players minimal data.
    rows: list of (id, name, current_team)
    """
    _init_if_needed(sport)
    path = _db_path_for_sport(sport)
    conn = _connect(path)
    try:
        now = int(time.time())
        payload = []
        for (pid, name, team) in rows:
            # Clean display name and normalized tokens
            display = _strip_specials_preserve_case(name)
            norm = normalize_text(display or name)
            toks = tokenize(norm)
            payload.append((pid, display or name, team, now, norm, toks))
        conn.executemany(
            "INSERT INTO players(id, name, current_team, updated_at, normalized_name, tokens) VALUES(?, ?, ?, ?, ?, ?)\n"
            "ON CONFLICT(id) DO UPDATE SET name=excluded.name, current_team=excluded.current_team, updated_at=excluded.updated_at, normalized_name=excluded.normalized_name, tokens=excluded.tokens",
            payload,
        )
    finally:
        conn.close()


def upsert_teams(sport: str, rows: List[Tuple[int, str, Optional[str]]]):
    """
    Upsert teams minimal data.
    rows: list of (id, name, current_league)
    """
    _init_if_needed(sport)
    path = _db_path_for_sport(sport)
    conn = _connect(path)
    try:
        now = int(time.time())
        payload = []
        for (tid, name, league) in rows:
            display = _strip_specials_preserve_case(name)
            norm = normalize_text(display or name)
            toks = tokenize(norm)
            payload.append((tid, display or name, league, now, norm, toks))
        conn.executemany(
            "INSERT INTO teams(id, name, current_league, updated_at, normalized_name, tokens) VALUES(?, ?, ?, ?, ?, ?)\n"
            "ON CONFLICT(id) DO UPDATE SET name=excluded.name, current_league=excluded.current_league, updated_at=excluded.updated_at, normalized_name=excluded.normalized_name, tokens=excluded.tokens",
            payload,
        )
    finally:
        conn.close()


def search_players(sport: str, q: str, limit: int) -> List[Dict[str, Optional[str]]]:
    _init_if_needed(sport)
    path = _db_path_for_sport(sport)
    conn = _connect(path)
    try:
        nq = normalize_text(q)
        # Get a candidate pool larger than limit
        # Build token-AND match for subset queries (e.g., search 'cole palmer' matches 'cole jermaine palmer')
        tokens = [t for t in tokenize(nq).split(" ") if t]
        where = "(name LIKE ? OR normalized_name LIKE ?)"
        params: List[object] = [f"%{q}%", f"%{nq}%"]
        if tokens:
            and_clauses = " AND ".join(["tokens LIKE ?" for _ in tokens])
            where = f"({where} OR ({and_clauses}))"
            params.extend([f"%{t}%" for t in tokens])
        sql = f"SELECT id, name, current_team, normalized_name FROM players WHERE {where} ORDER BY name LIMIT ?"
        params.append(int(limit) * 8)
        cur = conn.execute(sql, params)
        candidates = cur.fetchall()
        try:
            from rapidfuzz import fuzz
            scored = []
            for pid, name, team, norm in candidates:
                score = fuzz.WRatio(nq, norm or normalize_text(name))
                scored.append((score, pid, name, team))
            # Add a fallback: if no candidates, consider broader scan (bounded)
            if not scored:
                cur2 = conn.execute("SELECT id, name, current_team, normalized_name FROM players LIMIT ?", (int(limit) * 30,))
                for pid, name, team, norm in cur2.fetchall():
                    score = fuzz.WRatio(nq, norm or normalize_text(name))
                    scored.append((score, pid, name, team))
            scored.sort(reverse=True)
            out = []
            for score, pid, name, team in scored[:limit]:
                out.append({"id": pid, "name": name, "current_team": team})
            return out
        except Exception:
            # No rapidfuzz; return simple LIKE candidates
            return [{"id": r[0], "name": r[1], "current_team": r[2]} for r in candidates[:limit]]
    finally:
        conn.close()


def search_teams(sport: str, q: str, limit: int) -> List[Dict[str, Optional[str]]]:
    _init_if_needed(sport)
    path = _db_path_for_sport(sport)
    conn = _connect(path)
    try:
        nq = normalize_text(q)
        tokens = [t for t in tokenize(nq).split(" ") if t]
        where = "(name LIKE ? OR normalized_name LIKE ?)"
        params: List[object] = [f"%{q}%", f"%{nq}%"]
        if tokens:
            and_clauses = " AND ".join(["tokens LIKE ?" for _ in tokens])
            where = f"({where} OR ({and_clauses}))"
            params.extend([f"%{t}%" for t in tokens])
        sql = f"SELECT id, name, current_league, normalized_name FROM teams WHERE {where} ORDER BY name LIMIT ?"
        params.append(int(limit) * 8)
        cur = conn.execute(sql, params)
        candidates = cur.fetchall()
        try:
            from rapidfuzz import fuzz
            scored = []
            for tid, name, league, norm in candidates:
                score = fuzz.WRatio(nq, norm or normalize_text(name))
                scored.append((score, tid, name, league))
            if not scored:
                cur2 = conn.execute("SELECT id, name, current_league, normalized_name FROM teams LIMIT ?", (int(limit) * 30,))
                for tid, name, league, norm in cur2.fetchall():
                    score = fuzz.WRatio(nq, norm or normalize_text(name))
                    scored.append((score, tid, name, league))
            scored.sort(reverse=True)
            out = []
            for score, tid, name, league in scored[:limit]:
                out.append({"id": tid, "name": name, "current_league": league})
            return out
        except Exception:
            return [{"id": r[0], "name": r[1], "current_league": r[2]} for r in candidates[:limit]]
    finally:
        conn.close()


async def suggestions_from_local_or_upstream(entity_type: str, sport: str, q: str, limit: int):
    """
    Attempt to serve suggestions from local DB, otherwise query upstream provider
    and warm the DB with results.
    Returns a list of dicts matching AutocompleteSuggestion shape used by routers.
    """
    et = (entity_type or "").strip().lower()
    s = (sport or "").strip().upper()
    out: List[Dict] = []
    local_only = os.getenv("LOCAL_AUTOCOMPLETE_LOCAL_ONLY", "false").lower() in ("1", "true", "yes")
    if et == "player":
        loc = search_players(s, q, limit)
        if loc:
            for p in loc:
                label = p["name"] if not p.get("current_team") else f"{p['name']} — {p['current_team']}"
                out.append({
                    "id": p["id"],
                    "label": label,
                    "entity_type": "player",
                    "sport": s,
                    "team_abbr": p.get("current_team"),
                })
            return out
        # If local-only is enabled, do not query upstream
        if local_only:
            return out  # empty when no local results
        # Fallback to upstream
        from app.services.apisports import apisports_service
        rows = await apisports_service.search_players(q, s)
        # Warm DB
        to_upsert = []
        for r in rows:
            name = f"{(r.get('first_name') or '').strip()} {(r.get('last_name') or '').strip()}".strip() or str(r.get('id'))
            team = r.get("team_abbr") or None
            if r.get("id") is not None:
                to_upsert.append((int(r["id"]), name, team))
            label = name if not team else f"{name} — {team}"
            out.append({
                "id": r.get("id"),
                "label": label,
                "entity_type": "player",
                "sport": s,
                "team_abbr": team,
            })
        if to_upsert:
            upsert_players(s, to_upsert)
        return out[:limit]
    elif et == "team":
        loc = search_teams(s, q, limit)
        if loc:
            for t in loc:
                label = t["name"] if not t.get("current_league") else f"{t['name']} — {t['current_league']}"
                out.append({
                    "id": t["id"],
                    "label": label,
                    "entity_type": "team",
                    "sport": s,
                    "team_abbr": None,
                })
            return out
        if local_only:
            return out
        # Fallback to upstream
        from app.services.apisports import apisports_service
        rows = await apisports_service.search_teams(q, s)
        to_upsert = []
        for r in rows:
            name = r.get("name") or r.get("abbreviation") or str(r.get("id"))
            league = None
            if s in ("FOOTBALL", "EPL"):
                league = "football"
            elif s == "NBA":
                league = "NBA"
            elif s == "NFL":
                league = "NFL"
            if r.get("id") is not None:
                to_upsert.append((int(r["id"]), name, league))
            label = name if not league else f"{name} — {league}"
            out.append({
                "id": r.get("id"),
                "label": label,
                "entity_type": "team",
                "sport": s,
                "team_abbr": r.get("abbreviation"),
            })
        if to_upsert:
            upsert_teams(s, to_upsert)
        return out[:limit]
    else:
        return []


def purge_sport(sport: str):
    """Delete all rows for the sport's local DB (players and teams)."""
    _init_if_needed(sport)
    path = _db_path_for_sport(sport)
    conn = _connect(path)
    try:
        conn.execute("DELETE FROM players;")
        conn.execute("DELETE FROM teams;")
        try:
            conn.execute("VACUUM;")
        except Exception:
            pass
    finally:
        conn.close()


def get_player_by_id(sport: str, player_id: int) -> Optional[Dict[str, Optional[str]]]:
    _init_if_needed(sport)
    path = _db_path_for_sport(sport)
    conn = _connect(path)
    try:
        cur = conn.execute("SELECT id, name, current_team FROM players WHERE id = ?", (int(player_id),))
        row = cur.fetchone()
        if not row:
            return None
        return {"id": row[0], "name": row[1], "current_team": row[2]}
    finally:
        conn.close()


def get_team_by_id(sport: str, team_id: int) -> Optional[Dict[str, Optional[str]]]:
    _init_if_needed(sport)
    path = _db_path_for_sport(sport)
    conn = _connect(path)
    try:
        cur = conn.execute("SELECT id, name, current_league FROM teams WHERE id = ?", (int(team_id),))
        row = cur.fetchone()
        if not row:
            return None
        return {"id": row[0], "name": row[1], "current_league": row[2]}
    finally:
        conn.close()
