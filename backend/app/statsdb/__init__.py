"""
Scoracle Stats Database Module

A comprehensive local database system for storing and analyzing sports statistics
from API-Sports. Supports percentile calculations, historical data, and
multi-sport extensibility.

Usage:
    from app.statsdb import StatsDB, get_stats_db

    # Get database instance
    db = get_stats_db()

    # Query player stats
    stats = await db.get_player_stats(player_id=123, sport="NBA", season=2025)

    # Get percentiles
    percentiles = await db.get_player_percentiles(player_id=123, sport="NBA", season=2025)
"""

from .connection import StatsDB, get_stats_db
from .schema import init_database, run_migrations

__all__ = [
    "StatsDB",
    "get_stats_db",
    "init_database",
    "run_migrations",
]
