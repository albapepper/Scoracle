"""
Test script to verify seeder data capture for all sports.
Fetches 2 players and 2 teams from each sport (NFL, NBA, Football).
"""

import asyncio
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.apisports import apisports_service
from app.statsdb.seeders.nfl_seeder import NFLSeeder
from app.statsdb.seeders.nba_seeder import NBASeeder
from app.statsdb.seeders.football_seeder import FootballSeeder


async def test_nfl():
    """Test NFL data capture."""
    print("\n" + "=" * 60)
    print("NFL TEST")
    print("=" * 60)

    api = apisports_service

    # Test raw API response for a known player (Dak Prescott)
    print("\n--- Raw API Response (Dak Prescott, ID 2076) ---")
    try:
        players = await api.list_players("NFL", season="2025", team_id=29)
        dak = next((p for p in players if p.get("id") == 2076), None)
        if dak:
            print(f"  ID: {dak.get('id')}")
            print(f"  Name: {dak.get('name')}")
            print(f"  Position: {dak.get('position')}")
            print(f"  Group: {dak.get('group')}")
            print(f"  Height: {dak.get('height')}")
            print(f"  Weight: {dak.get('weight')}")
            print(f"  College: {dak.get('college')}")
            print(f"  Experience: {dak.get('experience')}")
            print(f"  Number: {dak.get('number')}")
        else:
            print("  Dak Prescott not found in response")
            if players:
                print(f"  Sample player: {players[0]}")
    except Exception as e:
        print(f"  Error: {e}")

    # Test seeder parsing
    print("\n--- Seeder Parsing Test ---")
    # Create a mock seeder (we won't actually write to DB)

    class MockDB:
        def execute(self, *args, **kwargs):
            pass

        def fetchone(self, *args, **kwargs):
            return None

        def fetchall(self, *args, **kwargs):
            return []

    seeder = NFLSeeder(db=MockDB(), api_service=api)

    # Test height parsing
    test_cases = [
        {"height": "6' 2\""},
        {"height": "6-2"},
        {"height": "5' 11\""},
    ]
    print("  Height parsing:")
    for tc in test_cases:
        result = seeder._parse_height(tc)
        print(f"    {tc['height']} -> {result} inches ({result // 12}'{result % 12}\")" if result else f"    {tc['height']} -> None")

    # Test weight parsing
    test_cases = [
        {"weight": "238 lbs"},
        {"weight": "220"},
        {"weight": 195},
    ]
    print("  Weight parsing:")
    for tc in test_cases:
        result = seeder._parse_weight(tc)
        print(f"    {tc['weight']} -> {result} lbs" if result else f"    {tc['weight']} -> None")

    # Test experience parsing
    test_cases = [10, "5", "Rookie"]
    print("  Experience parsing:")
    for tc in test_cases:
        result = seeder._parse_experience(tc)
        print(f"    {tc} -> {result} years" if result else f"    {tc} -> None")


async def test_nba():
    """Test NBA data capture."""
    print("\n" + "=" * 60)
    print("NBA TEST")
    print("=" * 60)

    api = apisports_service

    # Test raw API response for a known player (Cade Cunningham)
    print("\n--- Raw API Response (Cade Cunningham, ID 2801) ---")
    try:
        players = await api.list_players("NBA", season="2025", team_id=10)
        cade = next((p for p in players if p.get("id") == 2801), None)
        if cade:
            print(f"  ID: {cade.get('id')}")
            print(f"  First Name: {cade.get('first_name')}")
            print(f"  Last Name: {cade.get('last_name')}")
            print(f"  Position: {cade.get('position')}")
            print(f"  Height: {cade.get('height')}")
            print(f"  Weight: {cade.get('weight')}")
            print(f"  College: {cade.get('college')}")
            print(f"  Jersey: {cade.get('jersey')}")
            print(f"  Birth Date: {cade.get('birth_date')}")
        else:
            print("  Cade Cunningham not found in response")
            if players:
                print(f"  Sample player: {players[0]}")
    except Exception as e:
        print(f"  Error: {e}")

    # Test seeder parsing
    print("\n--- Seeder Parsing Test ---")

    class MockDB:
        def execute(self, *args, **kwargs):
            pass

        def fetchone(self, *args, **kwargs):
            return None

        def fetchall(self, *args, **kwargs):
            return []

    seeder = NBASeeder(db=MockDB(), api_service=api)

    # Test height parsing (NBA uses dict format)
    test_cases = [
        {"height": {"feets": "6", "inches": "6", "meters": "1.98"}},
        {"height": {"feets": "7", "inches": "0", "meters": "2.13"}},
        {"height": "6-8"},
        {"height": "2.03"},
    ]
    print("  Height parsing:")
    for tc in test_cases:
        result = seeder._parse_height(tc)
        if result:
            print(f"    {tc['height']} -> {result} inches ({result // 12}'{result % 12}\")")
        else:
            print(f"    {tc['height']} -> None")

    # Test weight parsing (NBA uses dict format)
    test_cases = [
        {"weight": {"pounds": "220", "kilograms": "99.8"}},
        {"weight": {"kilograms": "90.7"}},
        {"weight": "215"},
        {"weight": 200},
    ]
    print("  Weight parsing:")
    for tc in test_cases:
        result = seeder._parse_weight(tc)
        print(f"    {tc['weight']} -> {result} lbs" if result else f"    {tc['weight']} -> None")


async def test_football():
    """Test Football data capture."""
    print("\n" + "=" * 60)
    print("FOOTBALL TEST")
    print("=" * 60)

    api = apisports_service

    # Test raw API response for a known player (Cole Palmer)
    print("\n--- Raw API Response (Cole Palmer, ID 152982) ---")
    try:
        # Football uses league-based pagination
        players = await api.list_players("FOOTBALL", season="2025", league=39, page=1)
        palmer = next((p for p in players if p.get("id") == 152982), None)
        if palmer:
            print(f"  ID: {palmer.get('id')}")
            print(f"  Name: {palmer.get('name')}")
            print(f"  First Name: {palmer.get('first_name')}")
            print(f"  Last Name: {palmer.get('last_name')}")
            print(f"  Position: {palmer.get('position')}")
            print(f"  Height: {palmer.get('height')}")
            print(f"  Weight: {palmer.get('weight')}")
            print(f"  Nationality: {palmer.get('nationality')}")
            print(f"  Birth Date: {palmer.get('birth_date')}")
            print(f"  Number: {palmer.get('number')}")
        else:
            print("  Cole Palmer not found in first page")
            if players:
                print(f"  Sample player: {players[0]}")
    except Exception as e:
        print(f"  Error: {e}")

    # Test seeder parsing
    print("\n--- Seeder Parsing Test ---")

    class MockDB:
        def execute(self, *args, **kwargs):
            pass

        def fetchone(self, *args, **kwargs):
            return None

        def fetchall(self, *args, **kwargs):
            return []

    seeder = FootballSeeder(db=MockDB(), api_service=api)

    # Test height parsing (Football uses cm)
    test_cases = [
        {"height": "189"},
        {"height": "180 cm"},
        {"height": 175},
    ]
    print("  Height parsing (cm -> inches):")
    for tc in test_cases:
        result = seeder._parse_height(tc)
        if result:
            print(f"    {tc['height']} cm -> {result} inches ({result // 12}'{result % 12}\")")
        else:
            print(f"    {tc['height']} -> None")

    # Test weight parsing (Football uses kg)
    test_cases = [
        {"weight": "76"},
        {"weight": "80 kg"},
        {"weight": 70},
    ]
    print("  Weight parsing (kg -> lbs):")
    for tc in test_cases:
        result = seeder._parse_weight(tc)
        print(f"    {tc['weight']} kg -> {result} lbs" if result else f"    {tc['weight']} -> None")


async def main():
    print("=" * 60)
    print("SEEDER DATA CAPTURE TEST")
    print("Testing height, weight, college, experience parsing")
    print("=" * 60)

    await test_nfl()
    await test_nba()
    await test_football()

    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
