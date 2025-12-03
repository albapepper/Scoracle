"""Database package using JSON-based storage for serverless environments."""
from .json_db import (
    get_player_by_id,
    get_team_by_id,
    search_players,
    search_teams,
    list_all_players,
    list_all_teams,
)

__all__ = [
    'get_player_by_id',
    'get_team_by_id',
    'search_players',
    'search_teams',
    'list_all_players',
    'list_all_teams',
]