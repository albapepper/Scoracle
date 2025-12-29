"""Test the refactored _aggregate_nba_player_stats and helper functions."""
import sys
sys.path.insert(0, '/home/user/Scoracle/backend')

from app.services.apisports import ApiSportsService


def test_extract_game_season():
    """Test season extraction helper."""
    service = ApiSportsService(api_key="test")

    # Test game.game.season
    game1 = {"game": {"season": "2024"}}
    assert service._extract_game_season(game1) == 2024

    # Test game.team.season
    game2 = {"team": {"season": "2023"}}
    assert service._extract_game_season(game2) == 2023

    # Test invalid season
    game3 = {"game": {"season": "invalid"}}
    assert service._extract_game_season(game3) is None

    # Test no season
    game4 = {}
    assert service._extract_game_season(game4) is None

    print("✓ test_extract_game_season passed")


def test_filter_games_by_season():
    """Test season filtering helper."""
    service = ApiSportsService(api_key="test")

    games = [
        {"game": {"season": "2024"}, "points": 10},
        {"game": {"season": "2023"}, "points": 20},
        {"game": {"season": "2024"}, "points": 30},
        {"team": {"season": "2024"}, "points": 40},
        {},  # No season - should be included
    ]

    filtered = service._filter_games_by_season(games, 2024)
    assert len(filtered) == 4  # 3 with 2024 season + 1 with no season
    assert filtered[0]["points"] == 10
    assert filtered[1]["points"] == 30
    assert filtered[2]["points"] == 40

    print("✓ test_filter_games_by_season passed")


def test_parse_minutes():
    """Test minutes parsing helper."""
    service = ApiSportsService(api_key="test")

    # Test MM:SS format
    assert service._parse_minutes("35:30") == 35.5
    assert service._parse_minutes("12:00") == 12.0

    # Test numeric formats
    assert service._parse_minutes(25.5) == 25.5
    assert service._parse_minutes("30") == 30.0
    assert service._parse_minutes(20) == 20.0

    # Test edge cases
    assert service._parse_minutes(None) == 0.0
    assert service._parse_minutes("") == 0.0
    assert service._parse_minutes("invalid") == 0.0

    print("✓ test_parse_minutes passed")


def test_parse_plus_minus():
    """Test plus/minus parsing helper."""
    service = ApiSportsService(api_key="test")

    # Test string formats
    assert service._parse_plus_minus("+5") == 5
    assert service._parse_plus_minus("-3") == -3
    assert service._parse_plus_minus("12") == 12

    # Test numeric formats
    assert service._parse_plus_minus(7) == 7
    assert service._parse_plus_minus(-4) == -4

    # Test edge cases
    assert service._parse_plus_minus(None) == 0
    assert service._parse_plus_minus("") == 0
    assert service._parse_plus_minus("invalid") == 0

    print("✓ test_parse_plus_minus passed")


def test_aggregate_nba_player_stats():
    """Test the main aggregation function with sample data."""
    service = ApiSportsService(api_key="test")

    # Sample game data
    games = [
        {
            "player": {"id": 265, "name": "LeBron James"},
            "team": {"id": 17, "name": "Lakers"},
            "game": {"season": "2024"},
            "pos": "PF",
            "min": "35:30",
            "points": 28,
            "fgm": 10,
            "fga": 20,
            "tpm": 2,
            "tpa": 6,
            "ftm": 6,
            "fta": 8,
            "offReb": 1,
            "defReb": 7,
            "totReb": 8,
            "assists": 5,
            "turnovers": 3,
            "steals": 1,
            "blocks": 1,
            "pFouls": 2,
            "plusMinus": "+8"
        },
        {
            "player": {"id": 265, "name": "LeBron James"},
            "team": {"id": 17, "name": "Lakers"},
            "game": {"season": "2024"},
            "min": "32:00",
            "points": 25,
            "fgm": 9,
            "fga": 18,
            "tpm": 3,
            "tpa": 7,
            "ftm": 4,
            "fta": 5,
            "offReb": 2,
            "defReb": 6,
            "totReb": 8,
            "assists": 7,
            "turnovers": 2,
            "steals": 2,
            "blocks": 0,
            "pFouls": 1,
            "plusMinus": "-3"
        },
    ]

    result = service._aggregate_nba_player_stats(games)

    # Verify aggregation
    assert result["games"]["played"] == 2
    assert result["games"]["started"] == 1  # Only first game has "pos"
    assert result["points_total"] == 53  # 28 + 25
    assert result["fgm"] == 19  # 10 + 9
    assert result["fga"] == 38  # 20 + 18
    assert result["assists"] == 12  # 5 + 7
    assert result["plusMinus"] == 5  # 8 + (-3)
    assert result["min"] == 67  # 35.5 + 32 = 67.5, converted to int

    # Verify percentages
    assert result["fgp"] == 50.0  # 19/38 * 100

    print("✓ test_aggregate_nba_player_stats passed")


def test_aggregate_with_season_filter():
    """Test aggregation with season filtering."""
    service = ApiSportsService(api_key="test")

    games = [
        {
            "player": {"id": 1},
            "team": {"id": 1},
            "game": {"season": "2024"},
            "points": 20,
            "min": "30:00",
        },
        {
            "player": {"id": 1},
            "team": {"id": 1},
            "game": {"season": "2023"},  # Different season
            "points": 15,
            "min": "25:00",
        },
        {
            "player": {"id": 1},
            "team": {"id": 1},
            "game": {"season": "2024"},
            "points": 25,
            "min": "35:00",
        },
    ]

    # Aggregate only 2024 season
    result = service._aggregate_nba_player_stats(games, target_season=2024)

    assert result["games"]["played"] == 2  # Only 2024 games
    assert result["points_total"] == 45  # 20 + 25 (not including 2023)

    print("✓ test_aggregate_with_season_filter passed")


if __name__ == "__main__":
    print("Running refactored code tests...\n")

    try:
        test_extract_game_season()
        test_filter_games_by_season()
        test_parse_minutes()
        test_parse_plus_minus()
        test_aggregate_nba_player_stats()
        test_aggregate_with_season_filter()

        print("\n✅ All tests passed! Refactored code maintains the same behavior.")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error running tests: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
