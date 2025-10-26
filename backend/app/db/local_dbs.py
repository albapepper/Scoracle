import os
import re
import sqlite3
import threading
import time
import unicodedata
from typing import List, Dict, Tuple, Optional
from pathlib import Path

# Lightweight per-sport SQLite management for autocomplete data

_INIT_LOCK = threading.Lock()
_INITIALIZED: set[str] = set()


def _candidate_db_dirs() -> list[str]:
    """Return candidate directories that may contain local SQLite files.

    Order of preference:
    1) LOCAL_DB_DIR env var (if set)
    2) <repo_root>/instance/localdb
    3) <backend_root>/instance/localdb (for older layouts)
    """
    dirs: list[str] = []
    override = os.getenv("LOCAL_DB_DIR")
    if override:
        dirs.append(override)
    here = Path(__file__).resolve()
    # backend root: .../backend
    backend_root = here.parents[2]
    # repo root assumed one level above backend
    repo_root = backend_root.parent
    dirs.append(str(repo_root / "instance" / "localdb"))
    dirs.append(str(backend_root / "instance" / "localdb"))
    # Deduplicate preserving order
    out: list[str] = []
    seen = set()
    for d in dirs:
        if d not in seen:
            seen.add(d)
            out.append(d)
    return out


def _db_path_for_sport(sport: str) -> str:
    s = (sport or "").strip().upper()
    fname = {
        "NBA": "nba.sqlite",
        "NFL": "nfl.sqlite",
        "FOOTBALL": "football.sqlite",
        "EPL": "football.sqlite",  # alias for backward compatibility
    }.get(s, f"{s.lower()}.sqlite")
    candidates = _candidate_db_dirs()
    # Prefer a directory that already has the file
    for d in candidates:
        path = os.path.join(d, fname)
        if os.path.exists(path):
            return path
    # Otherwise, use the first candidate as the place to create it
    return os.path.join(candidates[0], fname)


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


def _first_last_only(name: Optional[str]) -> str:
    """Reduce a display name to only first and last tokens.

    Examples:
    - "Kevin Wayne Durant Jr." -> "Kevin Durant"
    - "Kylian Mbappé" -> "Kylian Mbappe" (diacritics stripped upstream by _strip_specials_preserve_case)
    - "LeBron Raymone James Sr" -> "LeBron James"

    Teams and single-word names are returned as-is.
    """
    if not name:
        return ""
    parts = str(name).split()
    if len(parts) <= 1:
        return parts[0] if parts else ""
    first = parts[0]
    last = parts[-1]
    # Handle suffixes commonly seen; if last is a suffix, take the previous token
    suffixes = {"jr", "jr.", "sr", "sr.", "ii", "iii", "iv", "v"}
    if last.lower().strip(". ") in suffixes and len(parts) >= 3:
        last = parts[-2]
    return f"{first} {last}".strip()


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
            # Clean display name, reduce to First Last, and normalize tokens
            display_raw = _strip_specials_preserve_case(name)
            display = _first_last_only(display_raw)
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


def list_all_players(sport: str) -> List[Tuple[int, str]]:
    """Return all players (id, name) for a sport from the local DB.

    Intended for building in-memory indexes (e.g., Aho-Corasick)."""
    _init_if_needed(sport)
    path = _db_path_for_sport(sport)
    conn = _connect(path)
    try:
        cur = conn.execute("SELECT id, name FROM players")
        return [(int(r[0]), str(r[1] or "")) for r in cur.fetchall()]
    finally:
        conn.close()


def list_all_teams(sport: str) -> List[Tuple[int, str]]:
    """Return all teams (id, name) for a sport from the local DB.

    Intended for building in-memory indexes (e.g., Aho-Corasick)."""
    _init_if_needed(sport)
    path = _db_path_for_sport(sport)
    conn = _connect(path)
    try:
        cur = conn.execute("SELECT id, name FROM teams")
        return [(int(r[0]), str(r[1] or "")) for r in cur.fetchall()]
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
                base = norm or normalize_text(name)
                score = fuzz.WRatio(nq, base)
                # Heuristics: prefer first-token match and prefix matches; then shorter names
                tokens_q = [t for t in nq.split(' ') if t]
                first_tok = tokens_q[0] if tokens_q else ''
                name_tokens = base.split(' ')
                first_token_match = 1 if (first_tok and name_tokens and name_tokens[0] == first_tok) else 0
                prefix_match = 1 if (first_tok and base.startswith(first_tok)) else 0
                length_penalty = -len(base)
                scored.append((score, first_token_match, prefix_match, length_penalty, pid, name, team))
            # Add a fallback: if no candidates, consider broader scan (bounded)
            if not scored:
                cur2 = conn.execute("SELECT id, name, current_team, normalized_name FROM players LIMIT ?", (int(limit) * 30,))
                for pid, name, team, norm in cur2.fetchall():
                    base = norm or normalize_text(name)
                    score = fuzz.WRatio(nq, base)
                    tokens_q = [t for t in nq.split(' ') if t]
                    first_tok = tokens_q[0] if tokens_q else ''
                    name_tokens = base.split(' ')
                    first_token_match = 1 if (first_tok and name_tokens and name_tokens[0] == first_tok) else 0
                    prefix_match = 1 if (first_tok and base.startswith(first_tok)) else 0
                    length_penalty = -len(base)
                    scored.append((score, first_token_match, prefix_match, length_penalty, pid, name, team))
            scored.sort(reverse=True)
            out = []
            for _score, _ftm, _pm, _lp, pid, name, team in scored[:limit]:
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
    LOCAL-ONLY autocomplete.

    Returns suggestions strictly from the local SQLite DB for the given sport.
    No external API calls are performed here. If no local matches are found,
    an empty list is returned. This function keeps the historical name so
    existing routers don't need to change their imports.
    """
    et = (entity_type or "").strip().lower()
    s = (sport or "").strip().upper()
    out: List[Dict] = []
    if et == "player":
        loc = search_players(s, q, limit)
        for p in loc:
            label = p["name"] if not p.get("current_team") else f"{p['name']} — {p['current_team']}"
            out.append({
                "id": p["id"],
                "label": label,
                "entity_type": "player",
                "sport": s,
                "team_abbr": p.get("current_team"),
            })
        return out[:limit]
    if et == "team":
        loc = search_teams(s, q, limit)
        for t in loc:
            label = t["name"] if not t.get("current_league") else f"{t['name']} — {t['current_league']}"
            out.append({
                "id": t["id"],
                "label": label,
                "entity_type": "team",
                "sport": s,
                "team_abbr": None,
            })
        return out[:limit]
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
