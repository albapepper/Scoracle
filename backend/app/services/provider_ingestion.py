"""Unified provider ingestion service.

Replaces legacy registry-based ingestion with direct local DB seeding logic.
Future expansion: schedule background refreshes, upstream diffs, etc.
"""
from typing import List, Dict, Any
import logging
from app.database import local_dbs
from app.services.apisports import apisports_service
from app.config import settings

logger = logging.getLogger(__name__)


async def ingest_sport_entities(sport: str) -> Dict[str, Any]:
    """Ingest players and teams for a sport into local SQLite.

    Lean mode or missing API key: skip upstream calls.
    Returns counts of entities ingested.
    """
    s = sport.upper()
    if settings.LEAN_BACKEND or not settings.API_SPORTS_KEY:
        logger.info("Skipping ingestion for %s (lean or no API key)", s)
        return {"sport": s, "players": 0, "teams": 0, "skipped": True}
    players_ingested = 0
    teams_ingested = 0
    try:
        if s == "NBA":
            rows = await apisports_service.list_nba_teams(league="standard")
            teams = []
            for r in rows:
                name = r.get("name") or r.get("abbreviation") or str(r.get("id"))
                if r.get("id") is not None:
                    teams.append((int(r["id"]), name, "NBA"))
            if teams:
                local_dbs.upsert_teams("NBA", teams)
                teams_ingested = len(teams)
            # Players basic listing
            for page in range(1, 4):
                plist = await apisports_service.list_nba_players(season="2024", page=page, league="standard")
                if not plist:
                    break
                rows_p = []
                for r in plist:
                    if r.get("id") is not None:
                        name = f"{(r.get('first_name') or '').strip()} {(r.get('last_name') or '').strip()}".strip() or str(r.get('id'))
                        rows_p.append((int(r["id"]), name, r.get("team_abbr") or None))
                if rows_p:
                    local_dbs.upsert_players("NBA", rows_p)
                    players_ingested += len(rows_p)
        elif s == "FOOTBALL":
            # Minimal ingestion (skip full pagination for now)
            from app.services.apisports import FOOTBALL_TOP_LEAGUES as leagues
            for lg in leagues[:2]:  # limit for now
                trows = await apisports_service.list_football_teams(lg, season="2025")
                teams = []
                for r in trows:
                    if r.get("id") is not None:
                        name = r.get("name") or r.get("abbreviation") or str(r.get("id"))
                        teams.append((int(r["id"]), name, "football"))
                if teams:
                    local_dbs.upsert_teams("FOOTBALL", teams)
                    teams_ingested += len(teams)
        elif s == "NFL":
            trows = await apisports_service.list_nfl_teams(league=None)
            teams = []
            for r in trows:
                if r.get("id") is not None:
                    name = r.get("name") or r.get("abbreviation") or str(r.get("id"))
                    teams.append((int(r["id"]), name, "NFL"))
            if teams:
                local_dbs.upsert_teams("NFL", teams)
                teams_ingested = len(teams)
        else:
            logger.info("Ingestion not implemented for sport %s", s)
    except Exception as e:
        logger.warning("Ingestion failed for %s: %s", s, e)
    return {"sport": s, "players": players_ingested, "teams": teams_ingested, "skipped": False}
