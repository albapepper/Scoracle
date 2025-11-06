import asyncio
import os
import argparse
from typing import List, Tuple, Sequence

from app.db.local_dbs import upsert_players, upsert_teams, purge_sport
from app.services.apisports import apisports_service
from app.core.config import settings


# League ids (API-Sports) for football umbrella (Top 5 + MLS)
FOOTBALL_LEAGUES = [39, 140, 135, 78, 61, 253]
ALPHA = list("abcdefghijklmnopqrstuvwxyz")


async def seed_football_api():
    # Teams via listing per league
    print("Seeding FOOTBALL teams via API...")
    for league_id in FOOTBALL_LEAGUES:
        try:
            rows = await apisports_service.list_football_teams(league_id, season="2025")
            print(f"FOOTBALL teams raw rows league {league_id}: {len(rows)}")
            teams: List[Tuple[int, str, str]] = []
            for r in rows:
                name = r.get("name") or r.get("abbreviation") or str(r.get("id"))
                if r.get("id") is not None:
                    teams.append((int(r["id"]), name, "football"))
            if teams:
                print(f"FOOTBALL teams upserting {len(teams)} from league {league_id}")
                upsert_teams("FOOTBALL", teams)
            else:
                # Fallback via search if listing returned empty
                rows2 = await apisports_service.search_teams("a", "FOOTBALL", league_override=league_id, season_override="2025")
                print(f"FOOTBALL teams fallback rows league {league_id}: {len(rows2)}")
                teams2 = []
                for r in rows2:
                    name = r.get("name") or r.get("abbreviation") or str(r.get("id"))
                    if r.get("id") is not None:
                        teams2.append((int(r["id"]), name, "football"))
                if teams2:
                    print(f"FOOTBALL teams upserting {len(teams2)} from league {league_id} (fallback)")
                    upsert_teams("FOOTBALL", teams2)
        except Exception as e:
            print(f"football teams seed warn (league {league_id}):", e)
        await asyncio.sleep(0.1)

    print("Seeding FOOTBALL players via API...")
    # For players, loop pages per league
    for league_id in FOOTBALL_LEAGUES:
        page = 1
        while True:
            try:
                rows = await apisports_service.list_football_players(league_id, season="2025", page=page)
                if not rows:
                    break
                players: List[Tuple[int, str, str]] = []
                for r in rows:
                    name = f"{(r.get('first_name') or '').strip()} {(r.get('last_name') or '').strip()}".strip() or str(r.get('id'))
                    team = r.get("team_abbr") or None
                    if r.get("id") is not None:
                        players.append((int(r["id"]), name, team))
                if players:
                    print(f"FOOTBALL players upserting {len(players)} from league {league_id} page {page}")
                    upsert_players("FOOTBALL", players)
                page += 1
            except Exception as e:
                print(f"football players list warn (league {league_id}, page {page}):", e)
                break
            await asyncio.sleep(0.1)


async def seed_nba_api():
    print("Seeding NBA teams via API...")
    try:
        rows = await apisports_service.list_nba_teams(league='standard')
        teams: List[Tuple[int, str, str]] = []
        for r in rows:
            name = r.get("name") or r.get("abbreviation") or str(r.get("id"))
            if r.get("id") is not None:
                teams.append((int(r["id"]), name, "NBA"))
        print(f"NBA teams raw rows: {len(rows)}; filtered: {len(teams)}")
        if teams:
            print(f"NBA teams upserting {len(teams)}")
            upsert_teams("NBA", teams)
        else:
            # Fallback: search across alphabet, dedupe by id
            from string import ascii_lowercase
            seen = set()
            teams2: List[Tuple[int, str, str]] = []
            for ch in ascii_lowercase:
                try:
                    rows2 = await apisports_service.search_teams(ch, "NBA")
                except Exception as e:
                    print(f"nba teams search warn ({ch}):", e)
                    continue
                for r in rows2:
                    tid = r.get("id")
                    name = r.get("name") or r.get("abbreviation") or str(tid)
                    if tid is not None and tid not in seen:
                        seen.add(tid)
                        teams2.append((int(tid), name, "NBA"))
                await asyncio.sleep(0.05)
            if teams2:
                print(f"NBA teams upserting {len(teams2)} via search fallback")
                upsert_teams("NBA", teams2)
    except Exception as e:
        print("nba teams seed warn:", e)

    print("Seeding NBA players via API...")
    # Paginate NBA players
    # Try listing; if empty, fallback to alpha search
    got_any = False
    for page in range(1, 6):
        try:
            rows = await apisports_service.list_nba_players(season="2024", page=page, league='standard')
            if not rows:
                break
            players: List[Tuple[int, str, str]] = []
            for r in rows:
                name = f"{(r.get('first_name') or '').strip()} {(r.get('last_name') or '').strip()}".strip() or str(r.get('id'))
                team = r.get("team_abbr") or None
                if r.get("id") is not None:
                    players.append((int(r["id"]), name, team))
            if players:
                got_any = True
                print(f"NBA players upserting {len(players)} page {page}")
                upsert_players("NBA", players)
        except Exception as e:
            print(f"nba players list warn (page {page}):", e)
            break
        await asyncio.sleep(0.1)
    if not got_any:
        # Fallback 1: roster by team (iterate NBA teams and fetch roster for the season)
        try:
            team_rows = await apisports_service.list_nba_teams(league='standard')
        except Exception as e:
            print("nba roster fallback teams warn:", e)
            team_rows = []
        for t in team_rows:
            tid = t.get("id")
            if not tid:
                continue
            try:
                page = 1
                while True:
                    roster = await apisports_service.list_nba_team_players(team_id=int(tid), season="2024", league='standard', page=page)
                    if not roster:
                        # Try statistics-based fallback once
                        if page == 1:
                            roster = await apisports_service.list_nba_team_statistics_players(team_id=int(tid), season="2024")
                            if not roster:
                                break
                            # else proceed to upsert this one-shot list
                        else:
                            break
                    players: List[Tuple[int, str, str]] = []
                    for r in roster:
                        name = f"{(r.get('first_name') or '').strip()} {(r.get('last_name') or '').strip()}".strip() or str(r.get('id'))
                        team = r.get("team_abbr") or None
                        if r.get("id") is not None:
                            players.append((int(r["id"]), name, team))
                    if players:
                        print(f"NBA players upserting {len(players)} via {'stats' if page==1 and not await apisports_service.list_nba_team_players(team_id=int(tid), season='2024', league='standard', page=1) else 'roster'} team {tid} page {page}")
                        upsert_players("NBA", players)
                    page += 1
            except Exception as e:
                print(f"nba roster fallback warn (team {tid}):", e)
            await asyncio.sleep(0.05)
    if not got_any:
        from string import ascii_lowercase
        for ch in ascii_lowercase:
            try:
                rows = await apisports_service.search_players(ch, "NBA", season_override="2024")
                players: List[Tuple[int, str, str]] = []
                for r in rows:
                    name = f"{(r.get('first_name') or '').strip()} {(r.get('last_name') or '').strip()}".strip() or str(r.get('id'))
                    team = r.get("team_abbr") or None
                    if r.get("id") is not None:
                        players.append((int(r["id"]), name, team))
                if players:
                    print(f"NBA players upserting {len(players)} via search {ch}")
                    upsert_players("NBA", players)
            except Exception as e:
                print(f"nba players search warn ({ch}):", e)
            await asyncio.sleep(0.1)
    await asyncio.sleep(0.1)


async def seed_nfl_api():
    print("Seeding NFL teams via API...")
    teams_upserted = False
    team_rows: List[dict] = []
    # 1) Try listing
    try:
        rows = await apisports_service.list_nfl_teams(league=None)
    except Exception as e:
        print("nfl teams list warn:", e)
        rows = []
    teams: List[Tuple[int, str, str]] = []
    for r in rows:
        name = r.get("name") or r.get("abbreviation") or str(r.get("id"))
        if r.get("id") is not None:
            teams.append((int(r["id"]), name, "NFL"))
    print(f"NFL teams raw rows: {len(rows)}; filtered: {len(teams)}")
    if teams:
        print(f"NFL teams upserting {len(teams)}")
        upsert_teams("NFL", teams)
        teams_upserted = True
        team_rows = rows
    # 2) Fallback: search across alphabet
    if not teams_upserted:
        from string import ascii_lowercase
        seen = set()
        teams2: List[Tuple[int, str, str]] = []
        found_dicts: List[dict] = []
        for ch in ascii_lowercase:
            try:
                rows2 = await apisports_service.search_teams(ch, "NFL")
            except Exception as e:
                print(f"nfl teams search warn ({ch}):", e)
                continue
            for r in rows2:
                tid = r.get("id")
                name = r.get("name") or r.get("abbreviation") or str(tid)
                if tid is not None and tid not in seen:
                    seen.add(tid)
                    teams2.append((int(tid), name, "NFL"))
                    found_dicts.append({"id": tid, "name": name})
            await asyncio.sleep(0.05)
        if teams2:
            print(f"NFL teams upserting {len(teams2)} (fallback)")
            upsert_teams("NFL", teams2)
            teams_upserted = True
            team_rows = found_dicts
    # 3) Fallback: brute-force team ids
    if not teams_upserted:
        brute: List[Tuple[int, str, str]] = []
        found_dicts: List[dict] = []
        for tid in range(1, 65):
            try:
                t = await apisports_service.get_nfl_team_by_id(tid)
            except Exception as e:
                print(f"nfl team id probe warn ({tid}):", e)
                continue
            if t and t.get("id") is not None:
                name = t.get("name") or t.get("abbreviation") or str(t.get("id"))
                brute.append((int(t["id"]) if isinstance(t.get("id"), int) else int(t.get("id")), name, "NFL"))
                found_dicts.append({"id": t.get("id"), "name": name})
            await asyncio.sleep(0.03)
        if brute:
            print(f"NFL teams upserting {len(brute)} via id-probe fallback")
            upsert_teams("NFL", brute)
            teams_upserted = True
            team_rows = found_dicts

    print("Seeding NFL players via API...")
    page = 1
    got_any = False
    while True:
        try:
            rows = await apisports_service.list_nfl_players(season="2025", page=page, league=int(os.getenv("API_SPORTS_NFL_LEAGUE", "1")))
            if not rows:
                break
            players: List[Tuple[int, str, str]] = []
            for r in rows:
                name = f"{(r.get('first_name') or '').strip()} {(r.get('last_name') or '').strip()}".strip() or str(r.get('id'))
                team = r.get("team_abbr") or None
                if r.get("id") is not None:
                    players.append((int(r["id"]), name, team))
            if players:
                got_any = True
                print(f"NFL players upserting {len(players)} page {page}")
                upsert_players("NFL", players)
            page += 1
        except Exception as e:
            print(f"nfl players list warn (page {page}):", e)
            break
        await asyncio.sleep(0.1)
    if not got_any:
        # Team-by-team fallback: try roster, then statistics
        if not team_rows:
            try:
                team_rows = await apisports_service.list_nfl_teams(league=None)
            except Exception as e:
                print("nfl roster fallback teams warn:", e)
                team_rows = []
        for t in team_rows:
            tid = t.get("id")
            if not tid:
                continue
            try:
                page = 1
                while True:
                    roster = await apisports_service.list_nfl_team_players(team_id=int(tid), season="2025", page=page)
                    if not roster:
                        if page == 1:
                            roster = await apisports_service.list_nfl_team_statistics_players(team_id=int(tid), season="2025")
                            if not roster:
                                break
                        else:
                            break
                    players: List[Tuple[int, str, str]] = []
                    for r in roster:
                        name = f"{(r.get('first_name') or '').strip()} {(r.get('last_name') or '').strip()}".strip() or str(r.get('id'))
                        team = r.get("team_abbr") or None
                        if r.get("id") is not None:
                            players.append((int(r["id"]), name, team))
                    if players:
                        print(f"NFL players upserting {len(players)} via {'stats' if page==1 else 'roster'} team {tid} page {page}")
                        upsert_players("NFL", players)
                    page += 1
            except Exception as e:
                print(f"nfl roster/statistics fallback warn (team {tid}):", e)
            await asyncio.sleep(0.05)
    if not got_any:
        # League-level statistics fallback (paged)
        for page in range(1, 6):
            try:
                rows = await apisports_service.list_nfl_statistics_players(season="2025", league=int(os.getenv("API_SPORTS_NFL_LEAGUE", "1")), page=page)
                if not rows:
                    break
                players: List[Tuple[int, str, str]] = []
                for r in rows:
                    name = f"{(r.get('first_name') or '').strip()} {(r.get('last_name') or '').strip()}".strip() or str(r.get('id'))
                    team = r.get("team_abbr") or None
                    if r.get("id") is not None:
                        players.append((int(r["id"]), name, team))
                if players:
                    print(f"NFL players upserting {len(players)} via league stats page {page}")
                    upsert_players("NFL", players)
            except Exception as e:
                print(f"nfl league statistics fallback warn (page {page}):", e)
                break
            await asyncio.sleep(0.05)
    # Last-resort: if nothing was upserted for teams and players, seed static NFL subset
    if not teams_upserted and not got_any:
        print("NFL API returned no data; seeding static NFL subset as fallback...")
        seed_nfl_static_minimal()


def seed_nfl_static_minimal():
    nfl_teams = [
        (1, "Arizona Cardinals", "NFL"),
        (2, "Atlanta Falcons", "NFL"),
        (3, "Baltimore Ravens", "NFL"),
        (4, "Buffalo Bills", "NFL"),
        (5, "Carolina Panthers", "NFL"),
        (6, "Chicago Bears", "NFL"),
        (7, "Cincinnati Bengals", "NFL"),
        (8, "Cleveland Browns", "NFL"),
        (9, "Dallas Cowboys", "NFL"),
        (10, "Denver Broncos", "NFL"),
        (11, "Detroit Lions", "NFL"),
        (12, "Green Bay Packers", "NFL"),
    ]
    upsert_teams("NFL", nfl_teams)
    nfl_players = [
        (10001, "Patrick Mahomes", "KC"),
        (10002, "Josh Allen", "BUF"),
        (10003, "Lamar Jackson", "BAL"),
        (10004, "Jalen Hurts", "PHI"),
        (10005, "Joe Burrow", "CIN"),
        (10006, "Justin Jefferson", "MIN"),
        (10007, "Tyreek Hill", "MIA"),
        (10008, "Christian McCaffrey", "SF"),
        (10009, "Micah Parsons", "DAL"),
        (10010, "Myles Garrett", "CLE"),
    ]
    upsert_players("NFL", nfl_players)


def seed_static_minimal():
    """Seed small, static datasets so local autocomplete works without API keys."""
    print("Seeding static fallback datasets (no API key)...")
    # NBA teams (subset)
    nba_teams = [
        (14, "Los Angeles Lakers", "NBA"),
        (2, "Boston Celtics", "NBA"),
        (10, "Golden State Warriors", "NBA"),
        (20, "Miami Heat", "NBA"),
        (24, "Phoenix Suns", "NBA"),
        (15, "Milwaukee Bucks", "NBA"),
        (25, "Portland Trail Blazers", "NBA"),
        (5, "Cleveland Cavaliers", "NBA"),
        (3, "Brooklyn Nets", "NBA"),
        (23, "Philadelphia 76ers", "NBA"),
        (19, "New Orleans Pelicans", "NBA"),
    ]
    upsert_teams("NBA", nba_teams)

    # NBA players (subset)
    nba_players = [
        (237, "LeBron James", "LAL"),
        (145, "Stephen Curry", "GSW"),
        (140, "Kevin Durant", "PHX"),
        (79, "Damian Lillard", "MIL"),
        (172, "Kyrie Irving", "DAL"),
        (63, "Brandon Ingram", "NOP"),
        (60, "Joel Embiid", "PHI"),
        (666, "Jayson Tatum", "BOS"),
        (154, "Anthony Davis", "LAL"),
        (333, "Donovan Mitchell", "CLE"),
        (456, "Jaylen Brown", "BOS"),
        (190, "Jimmy Butler", "MIA"),
    ]
    upsert_players("NBA", nba_players)

    # FOOTBALL teams (subset; umbrella)
    football_teams = [
        (50, "Manchester City", "football"),
        (33, "Manchester United", "football"),
        (541, "Real Madrid", "football"),
        (529, "Barcelona", "football"),
        (157, "Bayern Munich", "football"),
        (85, "Paris Saint-Germain", "football"),
        (108, "Inter Milan", "football"),
        (489, "AC Milan", "football"),
        (1609, "LA Galaxy", "football"),
    ]
    upsert_teams("FOOTBALL", football_teams)

    # FOOTBALL players (subset)
    football_players = [
        (154, "Lionel Messi", "Inter Miami"),
        (874, "Cristiano Ronaldo", "Al Nassr"),
        (278, "Kylian Mbappe", "PSG"),
        (135, "Neymar Jr", "Al Hilal"),
        (363, "Robert Lewandowski", "Barcelona"),
        (8745, "Erling Haaland", "Manchester City"),
        (235, "Kevin De Bruyne", "Manchester City"),
        (192, "Mohamed Salah", "Liverpool"),
    ]
    upsert_players("FOOTBALL", football_players)

    # NFL teams (subset)
    nfl_teams = [
        (1, "Arizona Cardinals", "NFL"),
        (2, "Atlanta Falcons", "NFL"),
        (3, "Baltimore Ravens", "NFL"),
        (4, "Buffalo Bills", "NFL"),
        (5, "Carolina Panthers", "NFL"),
        (6, "Chicago Bears", "NFL"),
        (7, "Cincinnati Bengals", "NFL"),
        (8, "Cleveland Browns", "NFL"),
        (9, "Dallas Cowboys", "NFL"),
        (10, "Denver Broncos", "NFL"),
        (11, "Detroit Lions", "NFL"),
        (12, "Green Bay Packers", "NFL"),
    ]
    upsert_teams("NFL", nfl_teams)

    # NFL players (subset; ids are illustrative placeholders)
    nfl_players = [
        (10001, "Patrick Mahomes", "KC"),
        (10002, "Josh Allen", "BUF"),
        (10003, "Lamar Jackson", "BAL"),
        (10004, "Jalen Hurts", "PHI"),
        (10005, "Joe Burrow", "CIN"),
        (10006, "Justin Jefferson", "MIN"),
        (10007, "Tyreek Hill", "MIA"),
        (10008, "Christian McCaffrey", "SF"),
        (10009, "Micah Parsons", "DAL"),
        (10010, "Myles Garrett", "CLE"),
    ]
    upsert_players("NFL", nfl_players)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed local SQLite DBs from API-Sports")
    parser.add_argument(
        "--sports",
        "-s",
        help="Comma-separated list or space-separated values of sports to seed (NBA, FOOTBALL, NFL)",
        nargs="*",
        default=None,
    )
    parser.add_argument(
        "--purge",
        action="store_true",
        help="Purge existing local rows before seeding (defaults to off)",
    )
    return parser.parse_args()


async def main():
    args = _parse_args()
    # Normalize sports selection
    selected: Sequence[str]
    if args.sports:
        # Support both space-separated and comma-separated usage
        parts: List[str] = []
        for item in args.sports:
            parts.extend([p.strip() for p in item.split(",") if p.strip()])
        selected = tuple(s.upper() for s in parts)
    else:
        selected = ("NBA", "FOOTBALL", "NFL")
    # Optionally purge existing rows when explicitly requested
    if getattr(args, "purge", False):
        for sport in selected:
            try:
                purge_sport(sport)
            except Exception:
                pass

    # Use settings (reads .env) to decide if API mode is enabled; skip API in lean mode
    if settings.API_SPORTS_KEY and not getattr(settings, "LEAN_BACKEND", False):
        # Force RapidAPI mode if not explicitly set, using the same key when RAPIDAPI_KEY is absent.
        if not os.getenv("API_SPORTS_MODE"):
            os.environ["API_SPORTS_MODE"] = "rapidapi"
        if not os.getenv("RAPIDAPI_KEY"):
            os.environ["RAPIDAPI_KEY"] = settings.API_SPORTS_KEY
        # Set default seasons via env for providers that rely on defaults
        os.environ["API_SPORTS_NBA_SEASON"] = "2024"  # 2024-25
        os.environ["API_SPORTS_FOOTBALL_SEASON"] = "2025"  # 2025-26
        os.environ["API_SPORTS_NFL_SEASON"] = "2025"  # 2025-26
        if "FOOTBALL" in selected:
            await seed_football_api()
        if "NBA" in selected:
            await seed_nba_api()
        if "NFL" in selected:
            await seed_nfl_api()
        print("Seeding complete (API).")
    else:
        # Static minimal seed performs upserts; no purge by default
        seed_static_minimal()
        print("Seeding complete (static).")


if __name__ == "__main__":
    asyncio.run(main())
