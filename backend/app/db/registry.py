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
        # Ingestion state
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
        # Currently only NBA is truly supported via balldontlie; placeholder for NFL/EPL.
        sport_upper = sport.upper()
        if self.ingesting:
            logger.info("Ingestion already in progress; skipping duplicate request")
            return
        self.ingesting = True
        self.players_ingested = 0
        self.teams_ingested = 0
        self.last_error = None
        try:
            if sport_upper == "NBA":
                await self._ingest_nba_players()
                await self._ingest_nba_teams()
            else:
                logger.warning("Ingestion for sport %s not implemented; skipping", sport_upper)
        except Exception as e:
            self.last_error = str(e)
            logger.error("Ingestion error: %s", e)
        finally:
            self.ingesting = False

    async def ensure_ingested_if_empty(self, sport: str):
        # Non-blocking helper: call from background task
        try:
            if await self.count(sport, "player") == 0 or await self.count(sport, "team") == 0:
                logger.info("Registry empty for %s; starting background ingestion", sport)
                await self.ingest_sport(sport)
            else:
                logger.info("Registry already populated for %s; skipping ingestion", sport)
        except Exception as e:
            logger.error("ensure_ingested_if_empty failed: %s", e)

    async def _ingest_nba_players(self):
        logger.info("Ingesting NBA players from upstream API")
        import httpx
        per_page = 100
        page = 1
        total = 0
        headers = {"Authorization": f"Bearer {balldontlie_service.api_key}"}
        base_url = balldontlie_service.get_base_url('NBA')
        async with httpx.AsyncClient(timeout=15.0) as client:
            while True:
                try:
                    resp = await client.get(f"{base_url}/players", params={"per_page": per_page, "page": page}, headers=headers)
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
                    self.players_ingested = total
                    logger.info("Ingested %d NBA players (page %d)", total, page)
                    if data.get("meta", {}).get("next_page") is None:
                        break
                    page += 1
                except Exception as e:
                    self.last_error = str(e)
                    logger.error("Error ingesting NBA players page %d: %s", page, e)
                    break

    async def _ingest_nba_teams(self):
        logger.info("Ingesting NBA teams from upstream API")
        import httpx
        headers = {"Authorization": f"Bearer {balldontlie_service.api_key}"}
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
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
            self.teams_ingested = len(rows)
            logger.info("Ingested %d NBA teams", len(rows))
        except Exception as e:
            self.last_error = str(e)
            logger.error("Error ingesting NBA teams: %s", e)

    def status(self):
        return {
            "ingesting": self.ingesting,
            "players_ingested": self.players_ingested,
            "teams_ingested": self.teams_ingested,
            "last_error": self.last_error,
        }

entity_registry = EntityRegistry()
