import sqlite3
import unicodedata
import re
from pathlib import Path


def _normalize_text(s: str | None) -> str:
    if not s:
        return ""
    s_norm = unicodedata.normalize("NFKD", s)
    s_ascii = "".join(ch for ch in s_norm if not unicodedata.combining(ch))
    s_lower = s_ascii.lower()
    s_clean = re.sub(r"[^a-z0-9 ]+", " ", s_lower)
    return " ".join(s_clean.split())


def _repo_root() -> Path:
    # backend/app/scripts -> parents[3] is repo root
    return Path(__file__).resolve().parents[3]


def _db_paths() -> list[Path]:
    base = _repo_root() / "instance" / "localdb"
    return [base / "nba.sqlite", base / "nfl.sqlite", base / "football.sqlite"]


def _dedupe_table(conn: sqlite3.Connection, table: str, assoc_col: str):
    cur = conn.cursor()
    cols = ("id", "name", assoc_col, "normalized_name")
    cur.execute(f"SELECT {', '.join(cols)} FROM {table}")
    rows = cur.fetchall()
    before = len(rows)
    keep_by_key: dict[tuple[str, str | None], int] = {}
    delete_ids: list[int] = []
    for rid, name, assoc, norm in rows:
        key_norm = norm or _normalize_text(name)
        key = (key_norm, assoc) if table == "players" else (key_norm, None)
        prev = keep_by_key.get(key)
        if prev is None or int(rid) < int(prev):
            if prev is not None and prev != rid:
                delete_ids.append(int(prev))
            keep_by_key[key] = int(rid)
        else:
            delete_ids.append(int(rid))
    removed = 0
    if delete_ids:
        unique_ids = sorted(set(delete_ids))
        for i in range(0, len(unique_ids), 500):
            chunk = unique_ids[i : i + 500]
            qmarks = ",".join(["?"] * len(chunk))
            cur.execute(f"DELETE FROM {table} WHERE id IN ({qmarks})", chunk)
        conn.commit()
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        after = int(cur.fetchone()[0])
        removed = before - after
    else:
        after = before
    return before, after, removed


def dedupe_all():
    for path in _db_paths():
        if not path.exists():
            continue
        conn = sqlite3.connect(str(path))
        try:
            print(f"DB: {path.name}")
            # Safeguard schemas (no-ops if present)
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS teams (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    current_league TEXT,
                    updated_at INTEGER,
                    normalized_name TEXT,
                    tokens TEXT
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS players (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    current_team TEXT,
                    updated_at INTEGER,
                    normalized_name TEXT,
                    tokens TEXT
                );
                """
            )
            b, a, r = _dedupe_table(conn, "teams", "current_league")
            print(f"  teams: before={b} after={a} removed={r}")
            b, a, r = _dedupe_table(conn, "players", "current_team")
            print(f"  players: before={b} after={a} removed={r}")
            try:
                conn.execute("VACUUM;")
            except Exception:
                pass
        finally:
            conn.close()


if __name__ == "__main__":
    dedupe_all()


