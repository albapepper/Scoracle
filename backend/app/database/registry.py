import aiosqlite
import asyncio
import logging
from typing import List, Optional, Dict, Any
from app.config import settings
from pathlib import Path

logger = logging.getLogger(__name__)

SCHEMA = """
CREATE TABLE IF NOT EXISTS entities (
    sport TEXT NOT NULL,
    entity_type TEXT NOT NULL, -- 'player' | 'team'
    id INTEGER NOT NULL,
    first_name TEXT,
    last_name TEXT,
    full_name TEXT,
    team_id INTEGER,
    team_abbr TEXT,
    position TEXT,
    search_blob TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (sport, entity_type, id)
);
CREATE INDEX IF NOT EXISTS idx_entities_search ON entities (sport, entity_type, full_name);
"""

class EntityRegistry:
    def __init__(self, db_path: str | None = None):
        if db_path:
            resolved = Path(db_path)
        else:
            project_root = Path(__file__).resolve().parents[3]
            resolved = project_root / settings.REGISTRY_DB_PATH
        resolved.parent.mkdir(parents=True, exist_ok=True)
        self.db_path = str(resolved)
        logger.info("Entity registry path set to %s", self.db_path)
        self._conn: Optional[aiosqlite.Connection] = None
        self.ingesting: bool = False
        self.players_ingested: int = 0
        self.teams_ingested: int = 0
        self.last_error: Optional[str] = None

    async def connect(self):
        if not self._conn:
            self._conn = await aiosqlite.connect(self.db_path)
            await self._conn.execute("PRAGMA journal_mode=WAL;")
            await self._conn.executescript(SCHEMA)
            await self._conn.commit()
            logger.info("Entity registry initialized")

    async def close(self):
        if self._conn:
            await self._conn.close()
            self._conn = None

    async def upsert_entity(self, row: Dict[str, Any]):
        sql = (
            "INSERT OR REPLACE INTO entities (sport, entity_type, id, first_name, last_name, full_name, team_id, team_abbr, position, search_blob) "
            "VALUES (:sport, :entity_type, :id, :first_name, :last_name, :full_name, :team_id, :team_abbr, :position, :search_blob)"
        )
        await self._conn.execute(sql, row)

    async def bulk_upsert(self, rows: List[Dict[str, Any]]):
        if not rows:
            return
        sql = "INSERT OR REPLACE INTO entities (sport, entity_type, id, first_name, last_name, full_name, team_id, team_abbr, position, search_blob) VALUES (?,?,?,?,?,?,?,?,?,?)"
        values = [(
            r.get("sport"), r.get("entity_type"), r.get("id"), r.get("first_name"), r.get("last_name"),
            r.get("full_name"), r.get("team_id"), r.get("team_abbr"), r.get("position"), r.get("search_blob")
        ) for r in rows]
        await self._conn.executemany(sql, values)
        await self._conn.commit()

    async def search(self, sport: str, entity_type: str, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        q_norm = f"%{query.lower()}%"
        cursor = await self._conn.execute(
            "SELECT sport, entity_type, id, first_name, last_name, full_name, team_abbr FROM entities "
            "WHERE sport=? AND entity_type=? AND search_blob LIKE ? ORDER BY full_name LIMIT ?",
            (sport.upper(), entity_type, q_norm, limit)
        )
        cols = [c[0] for c in cursor.description]
        rows = [dict(zip(cols, r)) for r in await cursor.fetchall()]
        return rows

    async def get_basic(self, sport: str, entity_type: str, entity_id: int) -> Optional[Dict[str, Any]]:
        cursor = await self._conn.execute(
            "SELECT sport, entity_type, id, first_name, last_name, full_name, team_abbr, team_id, position FROM entities "
            "WHERE sport=? AND entity_type=? AND id=?",
            (sport.upper(), entity_type, entity_id)
        )
        row = await cursor.fetchone()
        if not row:
            return None
        cols = [c[0] for c in cursor.description]
        return dict(zip(cols, row))

    async def count(self, sport: str, entity_type: str) -> int:
        cursor = await self._conn.execute(
            "SELECT COUNT(*) FROM entities WHERE sport=? AND entity_type=?",
            (sport.upper(), entity_type)
        )
        (cnt,) = await cursor.fetchone()
        return cnt

    async def ingest_sport(self, sport: str):
        logger.info("Registry ingestion skipped for %s (disabled)", sport.upper())
        self.last_error = None
        self.players_ingested = 0
        self.teams_ingested = 0

    async def ensure_ingested_if_empty(self, sport: str):
        try:
            if await self.count(sport, "player") == 0 or await self.count(sport, "team") == 0:
                logger.info("Registry empty for %s; starting background ingestion", sport)
                await self.ingest_sport(sport)
            else:
                logger.info("Registry already populated for %s; skipping ingestion", sport)
        except Exception as e:
            logger.error("ensure_ingested_if_empty failed: %s", e)

    def status(self):
        return {
            "ingesting": self.ingesting,
            "players_ingested": self.players_ingested,
            "teams_ingested": self.teams_ingested,
            "last_error": self.last_error,
        }

entity_registry = EntityRegistry()