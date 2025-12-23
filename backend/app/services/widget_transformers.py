"""
Widget Data Transformers

Transforms API-Sports responses into a unified format for the frontend.
Each sport has different response structures, so we normalize them here.

Unified Format:
- Team: { team: { id, name, logo, country, code, ... }, venue: { name, ... } }
- Player: { player: { id, name, photo, position, age, ... }, statistics: [...] }
"""
from typing import Any, Dict, List


def normalize_team_response(sport: str, raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform sport-specific team data into unified format.

    Args:
        sport: Sport code (FOOTBALL, NBA, NFL)
        raw_data: Raw API response data

    Returns:
        Normalized team data with structure:
        {
            "team": { id, name, logo, country, code, city, founded, ... },
            "venue": { name, city, capacity, surface, ... }
        }
    """
    if sport == "FOOTBALL":
        # FOOTBALL already returns the correct format
        return raw_data

    elif sport == "NBA":
        # NBA: { id, name, logo, code, city, ... }
        team = raw_data.copy()
        return {
            "team": {
                "id": team.get("id"),
                "name": team.get("name"),
                "logo": team.get("logo"),
                "code": team.get("code"),
                "city": team.get("city"),
                "country": "USA",  # NBA teams are all USA
                "founded": None,  # NBA doesn't provide this
            },
            "venue": {}  # NBA doesn't provide venue details
        }

    elif sport == "NFL":
        # NFL: { id, name, logo, code, city, stadium, coach, established, country: {...} }
        team = raw_data.copy()
        country_data = team.get("country", {})

        return {
            "team": {
                "id": team.get("id"),
                "name": team.get("name"),
                "logo": team.get("logo"),
                "code": team.get("code"),
                "city": team.get("city"),
                "country": country_data.get("name") if isinstance(country_data, dict) else country_data,
                "founded": team.get("established"),
                "coach": team.get("coach"),
                "owner": team.get("owner"),
            },
            "venue": {
                "name": team.get("stadium"),
            }
        }

    # Fallback: return as-is
    return {"team": raw_data, "venue": {}}


def normalize_player_response(sport: str, raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform sport-specific player data into unified format.

    Args:
        sport: Sport code (FOOTBALL, NBA, NFL)
        raw_data: Raw API response data

    Returns:
        Normalized player data with structure:
        {
            "player": { id, name, photo, position, age, height, weight, birth, ... },
            "statistics": [...]
        }
    """
    if sport == "FOOTBALL":
        # FOOTBALL already returns the correct format
        return raw_data

    elif sport == "NBA":
        # NBA: { id, firstname, lastname, birth, height: {...}, weight: {...}, leagues: {...} }
        player = raw_data.copy()

        # Build name from firstname/lastname
        name = f"{player.get('firstname', '')} {player.get('lastname', '')}".strip()

        # Extract position from leagues.standard.pos
        position = ""
        leagues = player.get("leagues", {})
        if isinstance(leagues, dict) and "standard" in leagues:
            position = leagues["standard"].get("pos", "")

        # Extract jersey number
        number = None
        if isinstance(leagues, dict) and "standard" in leagues:
            number = leagues["standard"].get("jersey")

        # Format height/weight for display
        height_obj = player.get("height", {})
        height_display = None
        if isinstance(height_obj, dict) and height_obj.get("meters"):
            height_display = f"{height_obj['meters']} m"

        weight_obj = player.get("weight", {})
        weight_display = None
        if isinstance(weight_obj, dict) and weight_obj.get("kilograms"):
            weight_display = f"{weight_obj['kilograms']} kg"

        return {
            "player": {
                "id": player.get("id"),
                "name": name,
                "photo": None,  # NBA doesn't provide photos in this endpoint
                "position": position,
                "number": number,
                "age": None,  # NBA doesn't provide age directly
                "height": height_display,
                "weight": weight_display,
                "nationality": player.get("birth", {}).get("country") if isinstance(player.get("birth"), dict) else None,
                "birth": player.get("birth"),
                "college": player.get("college"),
            },
            "statistics": []
        }

    elif sport == "NFL":
        # NFL: { id, name, age, height, weight, college, position, number, image, ... }
        player = raw_data.copy()

        return {
            "player": {
                "id": player.get("id"),
                "name": player.get("name"),
                "photo": player.get("image"),  # NFL uses 'image' field
                "position": player.get("position"),
                "number": player.get("number"),
                "age": player.get("age"),
                "height": player.get("height"),  # Already formatted as "6' 2""
                "weight": player.get("weight"),  # Already formatted as "238 lbs"
                "nationality": "USA",  # NFL doesn't provide nationality (assume USA)
                "college": player.get("college"),
                "experience": player.get("experience"),
                "group": player.get("group"),  # Offense/Defense/Special Teams
            },
            "statistics": []
        }

    # Fallback: return as-is
    return {"player": raw_data, "statistics": []}
