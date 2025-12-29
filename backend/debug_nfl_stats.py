"""
Debug script to test NFL stats fetching with minimal sample (2 teams, 2 players).

This script directly calls the API to see exactly what data is returned
and where the stats fetching is failing.
"""

import asyncio
import json
import logging
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.apisports import ApiSportsService

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


async def debug_nfl_stats():
    """Test NFL stats fetching with 2 teams and 2 players."""

    api = ApiSportsService()
    season = "2025"  # NFL 2025 season

    print("\n" + "="*80)
    print("NFL STATS DEBUG - Testing with 2 teams, 2 players")
    print("="*80)

    # Step 0: Check raw API response structure
    print("\n[0] CHECKING RAW TEAMS API RESPONSE...")
    try:
        import httpx
        base_url = api._base_url_for("NFL")
        headers = api._headers(base_url)
        params = {"league": 1, "season": int(season)}

        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.get(f"{base_url}/teams", headers=headers, params=params)
            raw_json = r.json()
            print(f"    HTTP Status: {r.status_code}")
            print(f"    API errors: {raw_json.get('errors')}")
            print(f"    API results count: {raw_json.get('results')}")
            response_data = raw_json.get('response', [])
            print(f"    Response length: {len(response_data) if isinstance(response_data, list) else 'N/A'}")
            if response_data and len(response_data) > 0:
                print(f"    First team structure:")
                print(json.dumps(response_data[0], indent=2, default=str)[:500])
    except Exception as e:
        print(f"    ERROR: {e}")

    # Step 1: Fetch teams
    print("\n[1] FETCHING TEAMS VIA API SERVICE...")
    try:
        teams = await api.list_teams("NFL", season=season)
        print(f"    Total teams found: {len(teams)}")

        # Take first 2 teams
        sample_teams = teams[:2]
        for team in sample_teams:
            print(f"    - Team ID {team['id']}: {team['name']}")
    except Exception as e:
        print(f"    ERROR fetching teams: {e}")
        return

    if not sample_teams:
        print("    No teams found! Let's check the raw response for player stats directly.")
        # Fallback: use known NFL player IDs for testing
        # Patrick Mahomes is typically ID 8137 in API-Sports
        sample_players = [{"id": 8137, "name": "Patrick Mahomes", "position": "QB"}]
        sample_teams = [{"id": 1, "name": "Test Team"}]
    else:
        sample_players = None  # Will be fetched below

    # Step 2: Fetch players from first team
    print("\n[2] FETCHING PLAYERS FROM FIRST TEAM...")
    first_team_id = sample_teams[0]["id"]

    if sample_players is None:  # Not set by fallback
        try:
            players = await api.list_players("NFL", season=season, team_id=first_team_id)
            print(f"    Total players found for team {first_team_id}: {len(players)}")

            # Take first 2 players
            sample_players = players[:2]
            for player in sample_players:
                print(f"    - Player ID {player['id']}: {player.get('name') or player.get('first_name', '')} {player.get('last_name', '')}")
                print(f"      Position: {player.get('position')}, Team ID: {player.get('team_id')}")
        except Exception as e:
            print(f"    ERROR fetching players: {e}")
            return

        if not sample_players:
            print("    No players found! Using fallback player IDs...")
            # Use known player IDs
            sample_players = [
                {"id": 8137, "name": "Patrick Mahomes", "position": "QB"},
                {"id": 1, "name": "Test Player", "position": "RB"}
            ]
    else:
        print("    Using fallback player list from Step 1")

    # Step 3: Fetch player stats for each sample player
    print("\n[3] FETCHING PLAYER STATISTICS...")
    for player in sample_players:
        player_id = player["id"]
        player_name = player.get("name") or f"{player.get('first_name', '')} {player.get('last_name', '')}"

        print(f"\n    --- Player {player_id}: {player_name} ---")

        try:
            stats = await api.get_player_statistics(str(player_id), "NFL", season)

            print(f"    Raw response type: {type(stats)}")
            print(f"    Response empty: {not stats}")

            if stats:
                print(f"    Response keys: {list(stats.keys()) if isinstance(stats, dict) else 'N/A'}")
                print(f"\n    FULL RAW RESPONSE:")
                print(json.dumps(stats, indent=2, default=str)[:2000])  # Limit output
                if len(json.dumps(stats)) > 2000:
                    print("    ... (truncated)")
            else:
                print("    EMPTY RESPONSE - No stats returned!")

        except Exception as e:
            print(f"    ERROR fetching stats: {e}")
            import traceback
            traceback.print_exc()

    # Step 4: Fetch team stats for sample teams
    print("\n[4] FETCHING TEAM STATISTICS (from standings)...")
    for team in sample_teams:
        team_id = team["id"]
        team_name = team["name"]

        print(f"\n    --- Team {team_id}: {team_name} ---")

        try:
            stats = await api.get_team_statistics(str(team_id), "NFL", season)

            print(f"    Raw response type: {type(stats)}")
            print(f"    Response empty: {not stats}")

            if stats:
                print(f"    Response keys: {list(stats.keys()) if isinstance(stats, dict) else 'N/A'}")
                print(f"\n    FULL RAW RESPONSE:")
                print(json.dumps(stats, indent=2, default=str)[:1500])
                if len(json.dumps(stats)) > 1500:
                    print("    ... (truncated)")
            else:
                print("    EMPTY RESPONSE - No stats returned!")

        except Exception as e:
            print(f"    ERROR fetching team stats: {e}")
            import traceback
            traceback.print_exc()

    # Step 5: Test the raw API endpoint directly
    print("\n[5] TESTING RAW API ENDPOINT DIRECTLY...")
    if sample_players:
        player_id = sample_players[0]["id"]
        print(f"    Testing /players/statistics?id={player_id}&season={season}")

        try:
            import httpx
            base_url = api._base_url_for("NFL")
            headers = api._headers(base_url)
            params = {"id": player_id, "season": int(season)}

            async with httpx.AsyncClient(timeout=30.0) as client:
                r = await client.get(f"{base_url}/players/statistics", headers=headers, params=params)
                print(f"    HTTP Status: {r.status_code}")
                raw_json = r.json()
                print(f"    Raw API response structure:")
                print(f"    - errors: {raw_json.get('errors')}")
                print(f"    - results: {raw_json.get('results')}")
                print(f"    - response type: {type(raw_json.get('response'))}")
                response_data = raw_json.get('response', [])
                print(f"    - response length: {len(response_data) if isinstance(response_data, list) else 'N/A'}")

                if response_data:
                    print(f"\n    First response item:")
                    print(json.dumps(response_data[0] if isinstance(response_data, list) else response_data, indent=2, default=str)[:2000])

        except Exception as e:
            print(f"    ERROR in raw request: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "="*80)
    print("DEBUG COMPLETE")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(debug_nfl_stats())
