import os
import sqlite3
from app.database.local_dbs import _db_path_for_sport

SPORTS = ("NBA", "NFL", "FOOTBALL")

def inspect_sport(s):
    path = _db_path_for_sport(s)
    exists = os.path.exists(path)
    size = os.path.getsize(path) if exists else 0
    print(f"Sport={s} path={path} exists={exists} size={size}")
    if not exists:
        return
    try:
        conn = sqlite3.connect(path)
        cur = conn.cursor()
        # Ensure tables exist before counting
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in cur.fetchall()]
        print(f"  tables: {tables}")
        for tbl in ("teams", "players"):
            if tbl in tables:
                cur.execute(f"SELECT COUNT(*) FROM {tbl}")
                cnt = cur.fetchone()[0]
                print(f"  {tbl} count: {cnt}")
                # show a couple sample rows
                cur.execute(f"SELECT id, name FROM {tbl} LIMIT 5")
                rows = cur.fetchall()
                print(f"  {tbl} sample: {rows}")
            else:
                print(f"  {tbl} table not found")
    except Exception as e:
        print(f"  error reading {path}: {e}")
    finally:
        try:
            conn.close()
        except Exception:
            pass

if __name__ == "__main__":
    print(f"cwd={os.getcwd()}")
    print(f"LOCAL_DB_DIR={os.getenv('LOCAL_DB_DIR')}")
    for s in SPORTS:
        inspect_sport(s)
