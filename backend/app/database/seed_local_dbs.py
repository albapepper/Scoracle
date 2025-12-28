import asyncio
import os
import argparse
from typing import Dict, List, Tuple, Sequence

from app.database.local_dbs import upsert_players, upsert_teams, purge_sport
from app.services.apisports import apisports_service
from app.config import settings


# League ids (API-Sports) for football umbrella (Top 5 + MLS + additional leagues)
FOOTBALL_LEAGUES = [39, 40, 140, 135, 78, 61, 253, 94, 203, 88, 144, 71, 129]
# League name mapping for football
LEAGUE_NAMES = {
    39: "Premier League",
    40: "Championship",       # England 2nd tier
    140: "La Liga",
    135: "Serie A",
    78: "Bundesliga",
    61: "Ligue 1",
    253: "MLS",
    94: "Primeira Liga",      # Portugal
    203: "Süper Lig",         # Turkey
    88: "Eredivisie",         # Netherlands
    144: "Jupiler Pro League", # Belgium
    71: "Brasileirão",        # Brazil
    129: "Liga MX",           # Mexico
}
ALPHA = list("abcdefghijklmnopqrstuvwxyz")


async def seed_football_api():
	# Teams via listing per league - fetch both seasons to capture all teams
	print("Seeding FOOTBALL teams via API...")
	all_teams: Dict[int, Tuple[int, str, str, int]] = {}
	seasons = ["2024", "2025"]

	for season in seasons:
		for league_id in FOOTBALL_LEAGUES:
			try:
				rows = await apisports_service.list_teams("FOOTBALL", league=league_id, season=season)
				league_name = LEAGUE_NAMES.get(league_id, f"League {league_id}")
				for r in rows:
					tid = r.get("id")
					if tid is not None:
						name = r.get("name") or r.get("abbreviation") or str(tid)
						# 2025 data overwrites 2024 data (newer takes precedence)
						all_teams[int(tid)] = (int(tid), name, league_name, league_id)
			except Exception as e:
				print(f"football teams seed warn (league {league_id}, season {season}):", e)
			await asyncio.sleep(0.05)

	# Upsert all collected teams
	if all_teams:
		teams_list = list(all_teams.values())
		print(f"FOOTBALL teams upserting {len(teams_list)} total (deduplicated from seasons {seasons})")
		upsert_teams("FOOTBALL", teams_list)

	print("Seeding FOOTBALL players via API...")
	# Track all players by ID to avoid duplicates (newer season data takes precedence)
	all_players: Dict[int, Tuple[int, str, str]] = {}
	seasons = ["2024", "2025"]  # Fetch both seasons

	# For players, loop pages per league per season
	for season in seasons:
		for league_id in FOOTBALL_LEAGUES:
			page = 1
			while True:
				try:
					rows = await apisports_service.list_players("FOOTBALL", season=season, page=page, league=league_id)
					if not rows:
						break
					for r in rows:
						pid = r.get("id")
						if pid is None:
							continue
						# Prefer firstname + lastname (full name) over abbreviated 'name' field
						# API returns name like "M. Mudryk" but firstname/lastname as "Mykhailo"/"Mudryk"
						first = (r.get('first_name') or '').strip()
						last = (r.get('last_name') or '').strip()
						if first and last:
							name = f"{first} {last}"
						elif first:
							name = first
						elif last:
							name = last
						else:
							name = r.get('name') or str(pid)
						team = r.get("team_abbr") or None
						# 2025 data overwrites 2024 data (newer takes precedence)
						all_players[int(pid)] = (int(pid), name, team)
					page += 1
				except Exception as e:
					print(f"football players list warn (league {league_id}, season {season}, page {page}):", e)
					break
				await asyncio.sleep(0.05)
			print(f"FOOTBALL players: league {league_id} season {season} complete ({len(all_players)} total so far)")

	# Upsert all collected players
	if all_players:
		players_list = list(all_players.values())
		print(f"FOOTBALL players upserting {len(players_list)} total (deduplicated from seasons {seasons})")
		upsert_players("FOOTBALL", players_list)


async def seed_nba_api():
	print("Seeding NBA teams via API...")
	try:
		rows = await apisports_service.list_teams("NBA", league="standard")
		teams: List[Tuple[int, str, str]] = []
		# Fetch division info for each team
		for r in rows:
			name = r.get("name") or r.get("abbreviation") or str(r.get("id"))
			team_id = r.get("id")
			if team_id is not None:
				# Fetch team details to get division
				division = None
				try:
					team_details = await apisports_service.get_team_basic(str(team_id), "NBA")
					division = team_details.get("division")
					if division:
						# Format: "Atlantic" -> "Atlantic Division"
						if "Division" not in division:
							division = f"{division} Division"
				except Exception as e:
					print(f"Warning: Could not fetch division for NBA team {team_id}: {e}")
					division = None
				teams.append((int(team_id), name, division or "NBA"))
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
	# NBA players endpoint requires team parameter - iterate through all teams
	# Fetch both 2024 and 2025 seasons to include injured/suspended/moved players
	try:
		team_rows = await apisports_service.list_teams("NBA", league="standard")
		print(f"NBA players: got {len(team_rows)} teams to iterate")
	except Exception as e:
		print("nba players teams fetch warn:", e)
		team_rows = []

	# Track all players by ID to avoid duplicates (newer season data takes precedence)
	all_players: Dict[int, Tuple[int, str, str]] = {}
	seasons = ["2024", "2025"]  # Fetch both seasons

	for season in seasons:
		for t in team_rows:
			tid = t.get("id")
			if not tid:
				continue
			try:
				# Fetch players for this team (season + team, no league/page parameter)
				roster = await apisports_service.list_players("NBA", season=season, team_id=int(tid))
				if not roster:
					continue
				for r in roster:
					pid = r.get("id")
					if pid is None:
						continue
					# Prefer firstname + lastname (full name) over abbreviated 'name' field
					first = (r.get('first_name') or '').strip()
					last = (r.get('last_name') or '').strip()
					if first and last:
						name = f"{first} {last}"
					elif first:
						name = first
					elif last:
						name = last
					else:
						name = r.get('name') or str(pid)
					team_abbr = r.get("team_abbr") or None
					# 2025 data overwrites 2024 data (newer takes precedence)
					all_players[int(pid)] = (int(pid), name, team_abbr)
			except Exception as e:
				print(f"nba players warn (team {tid}, season {season}):", e)
			await asyncio.sleep(0.02)

	# Upsert all collected players
	if all_players:
		players_list = list(all_players.values())
		print(f"NBA players upserting {len(players_list)} total (deduplicated from seasons {seasons})")
		upsert_players("NBA", players_list)
	await asyncio.sleep(0.1)


async def seed_nfl_api():
	print("Seeding NFL teams via API...")
	teams_upserted = False
	team_rows: List[dict] = []
	# NFL league ID is always 1
	NFL_LEAGUE_ID = 1
	# 1) Try listing
	try:
		rows = await apisports_service.list_teams("NFL", league=NFL_LEAGUE_ID)
	except Exception as e:
		print("nfl teams list warn:", e)
		rows = []
	teams: List[Tuple[int, str, str, int]] = []
	# Fetch division info for each team
	for r in rows:
		name = r.get("name") or r.get("abbreviation") or str(r.get("id"))
		team_id = r.get("id")
		if team_id is not None:
			# Fetch team details to get division
			division = None
			try:
				team_details = await apisports_service.get_team_basic(str(team_id), "NFL")
				division = team_details.get("division")
				if division:
					# Format: "AFC North" -> "AFC North Division" or keep as is
					if "Division" not in division and division:
						division = f"{division} Division"
			except Exception as e:
				print(f"Warning: Could not fetch division for NFL team {team_id}: {e}")
				division = None
			teams.append((int(team_id), name, division or "NFL", NFL_LEAGUE_ID))
			team_rows.append(r)  # Keep original row for player seeding
	print(f"NFL teams raw rows: {len(rows)}; filtered: {len(teams)}")
	if teams:
		print(f"NFL teams upserting {len(teams)}")
		upsert_teams("NFL", teams)
		teams_upserted = True
	# 2) Fallback: search across alphabet
	if not teams_upserted:
		from string import ascii_lowercase
		seen = set()
		teams2: List[Tuple[int, str, str, int]] = []
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
					# Try to get division
					division = None
					try:
						team_details = await apisports_service.get_team_basic(str(tid), "NFL")
						division = team_details.get("division")
						if division and "Division" not in division:
							division = f"{division} Division"
					except Exception:
						division = None
					teams2.append((int(tid), name, division or "NFL", NFL_LEAGUE_ID))
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
				t = await apisports_service.get_team_basic(str(tid), "NFL")
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
	# NFL players endpoint requires team parameter - iterate through all teams
	# Use team_rows from teams seeding if available, otherwise fetch again
	if not team_rows:
		try:
			team_rows = await apisports_service.list_teams("NFL", league=NFL_LEAGUE_ID)
		except Exception as e:
			print("nfl players teams fetch warn:", e)
			team_rows = []

	# Track all players by ID to avoid duplicates (newer season data takes precedence)
	all_players: Dict[int, Tuple[int, str, str]] = {}
	seasons = ["2024", "2025"]  # Fetch both seasons

	for season in seasons:
		for t in team_rows:
			tid = t.get("id")
			if not tid:
				continue
			try:
				# Fetch players for this team (season + team, no league/page parameter)
				roster = await apisports_service.list_players("NFL", season=season, team_id=int(tid))
				if not roster:
					continue
				for r in roster:
					pid = r.get("id")
					if pid is None:
						continue
					# Prefer firstname + lastname (full name) over abbreviated 'name' field
					first = (r.get('first_name') or '').strip()
					last = (r.get('last_name') or '').strip()
					if first and last:
						name = f"{first} {last}"
					elif first:
						name = first
					elif last:
						name = last
					else:
						name = r.get('name') or str(pid)
					team_abbr = r.get("team_abbr") or None
					# 2025 data overwrites 2024 data (newer takes precedence)
					all_players[int(pid)] = (int(pid), name, team_abbr)
			except Exception as e:
				print(f"nfl players warn (team {tid}, season {season}):", e)
			await asyncio.sleep(0.02)

	# Upsert all collected players
	if all_players:
		players_list = list(all_players.values())
		print(f"NFL players upserting {len(players_list)} total (deduplicated from seasons {seasons})")
		upsert_players("NFL", players_list)

	# Last-resort: if nothing was upserted for teams, seed static NFL subset
	if not teams_upserted:
		print("NFL API returned no teams; seeding static NFL subset as fallback...")
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

	# Use settings (reads .env) to decide if API mode is enabled
	if settings.API_SPORTS_KEY:
		# Force RapidAPI mode if not explicitly set, using the same key when RAPIDAPI_KEY is absent.
		if not os.getenv("API_SPORTS_MODE"):
			os.environ["API_SPORTS_MODE"] = "rapidapi"
		if not os.getenv("RAPIDAPI_KEY"):
			os.environ["RAPIDAPI_KEY"] = settings.API_SPORTS_KEY
		# Set default seasons via env for providers that rely on defaults
		os.environ["API_SPORTS_NBA_SEASON"] = "2025"  # 2025-26
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