import aiosqlite
import asyncio
import logging
from typing import List, Optional, Dict, Any
from app.services.balldontlie_api import balldontlie_service

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
    def __init__(self, db_path: str = "./registry.db"):
        self.db_path = db_path
        self._conn: Optional[aiosqlite.Connection] = None

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
        placeholders = (
            "INSERT OR REPLACE INTO entities (sport, entity_type, id, first_name, last_name, full_name, team_id, team_abbr, position, search_blob) "
            "VALUES (:sport, :entity_type, :id, :first_name, :last_name, :full_name, :team_id, :team_abbr, :position, :search_blob)"
        )
        await self._conn.execute(placeholders, row)

    async def bulk_upsert(self, rows: List[Dict[str, Any]]):
        if not rows:
            return
        async with self._conn.execute("BEGIN"):
            for r in rows:
                await self.upsert_entity(r)
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
        # Currently only NBA is truly supported via balldontlie; placeholder for NFL/EPL.
        sport_upper = sport.upper()
        if sport_upper == "NBA":
            await self._ingest_nba_players()
            await self._ingest_nba_teams()
        else:
            logger.warning("Ingestion for sport %s not implemented; skipping", sport_upper)

    async def _ingest_nba_players(self):
        logger.info("Ingesting NBA players from upstream API")
        per_page = 100
        page = 1
        total = 0
        while True:
            try:
                async with aiosqlite.connect(self.db_path):
                    pass
                import httpx
                headers = {"Authorization": f"Bearer {balldontlie_service.api_key}"}
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.get(f"{balldontlie_service.get_base_url('NBA')}/players", params={"per_page": per_page, "page": page}, headers=headers)
                    resp.raise_for_status()
                    data = resp.json()
                players = data.get("data", [])
                if not players:
                    break
                rows = []
                for p in players:
                    team = p.get("team", {}) or {}
                    full_name = f"{p.get('first_name','')} {p.get('last_name','')}".strip()
                    search_blob = " ".join(filter(None, [full_name.lower(), team.get('abbreviation','').lower()]))
                    rows.append({
                        "sport": "NBA",
                        "entity_type": "player",
                        "id": p.get("id"),
                        "first_name": p.get("first_name"),
                        "last_name": p.get("last_name"),
                        "full_name": full_name,
                        "team_id": team.get("id"),
                        "team_abbr": team.get("abbreviation"),
                        "position": p.get("position"),
                        "search_blob": search_blob,
                    })
                await self.bulk_upsert(rows)
                total += len(rows)
                logger.info("Ingested %d NBA players (page %d)", total, page)
                if data.get("meta", {}).get("next_page") is None:
                    break
                page += 1
            except Exception as e:
                logger.error("Error ingesting NBA players page %d: %s", page, e)
                break

    async def _ingest_nba_teams(self):
        logger.info("Ingesting NBA teams from upstream API")
        import httpx
        headers = {"Authorization": f"Bearer {balldontlie_service.api_key}"}
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(f"{balldontlie_service.get_base_url('NBA')}/teams", headers=headers)
                resp.raise_for_status()
                teams = resp.json().get("data", [])
            rows = []
            for t in teams:
                full_name = t.get("full_name") or t.get("name") or "Unknown Team"
                search_blob = " ".join(filter(None, [full_name.lower(), t.get("abbreviation","" ).lower(), t.get("city","" ).lower()]))
                rows.append({
                    "sport": "NBA",
                    "entity_type": "team",
                    "id": t.get("id"),
                    "first_name": None,
                    "last_name": None,
                    "full_name": full_name,
                    "team_id": None,
                    "team_abbr": t.get("abbreviation"),
                    "position": None,
                    "search_blob": search_blob,
                })
            await self.bulk_upsert(rows)
            logger.info("Ingested %d NBA teams", len(rows))
        except Exception as e:
            logger.error("Error ingesting NBA teams: %s", e)

entity_registry = EntityRegistry()
