"""
Base seeder class for stats database population.

All sport-specific seeders inherit from this class and implement
the abstract methods for data transformation.
"""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from ..connection import StatsDB
    from ...services.apisports import ApiSportsService

logger = logging.getLogger(__name__)


class BaseSeeder(ABC):
    """
    Abstract base class for sport-specific seeders.

    Subclasses must implement:
    - sport_id: The sport identifier (NBA, NFL, FOOTBALL)
    - fetch_teams(): Fetch teams from API
    - fetch_players(): Fetch players from API
    - fetch_player_stats(): Fetch player statistics
    - fetch_team_stats(): Fetch team statistics
    - transform_player_stats(): Transform API response to DB schema
    - transform_team_stats(): Transform API response to DB schema
    """

    sport_id: str = ""

    def __init__(
        self,
        db: "StatsDB",
        api_service: "ApiSportsService",
    ):
        """
        Initialize the seeder.

        Args:
            db: Stats database connection
            api_service: API-Sports service instance
        """
        self.db = db
        self.api = api_service
        self._sync_id: Optional[int] = None

    # =========================================================================
    # Sync Tracking
    # =========================================================================

    def _start_sync(
        self,
        sync_type: str,
        entity_type: Optional[str] = None,
        season_id: Optional[int] = None,
    ) -> int:
        """Record the start of a sync operation."""
        self.db.execute(
            """
            INSERT INTO sync_log (sport_id, sync_type, entity_type, season_id, started_at, status)
            VALUES (?, ?, ?, ?, ?, 'running')
            """,
            (self.sport_id, sync_type, entity_type, season_id, int(time.time())),
        )
        result = self.db.fetchone("SELECT last_insert_rowid() as id")
        return result["id"]

    def _complete_sync(
        self,
        sync_id: int,
        records_processed: int,
        records_inserted: int,
        records_updated: int,
    ) -> None:
        """Record successful sync completion."""
        self.db.execute(
            """
            UPDATE sync_log
            SET status = 'completed',
                completed_at = ?,
                records_processed = ?,
                records_inserted = ?,
                records_updated = ?
            WHERE id = ?
            """,
            (
                int(time.time()),
                records_processed,
                records_inserted,
                records_updated,
                sync_id,
            ),
        )

    def _fail_sync(self, sync_id: int, error_message: str) -> None:
        """Record sync failure."""
        self.db.execute(
            """
            UPDATE sync_log
            SET status = 'failed',
                completed_at = ?,
                error_message = ?
            WHERE id = ?
            """,
            (int(time.time()), error_message, sync_id),
        )

    # =========================================================================
    # Season Management
    # =========================================================================

    def ensure_season(self, season_year: int, is_current: bool = False) -> int:
        """
        Ensure a season exists and return its ID.

        Args:
            season_year: The season year (e.g., 2024)
            is_current: Whether this is the current season

        Returns:
            Season ID
        """
        existing = self.db.fetchone(
            "SELECT id FROM seasons WHERE sport_id = ? AND season_year = ?",
            (self.sport_id, season_year),
        )

        if existing:
            # Update is_current if needed
            if is_current:
                self.db.execute(
                    "UPDATE seasons SET is_current = 0 WHERE sport_id = ?",
                    (self.sport_id,),
                )
                self.db.execute(
                    "UPDATE seasons SET is_current = 1 WHERE id = ?",
                    (existing["id"],),
                )
            return existing["id"]

        # Create new season
        label = self._get_season_label(season_year)

        if is_current:
            # Clear current flag from other seasons
            self.db.execute(
                "UPDATE seasons SET is_current = 0 WHERE sport_id = ?",
                (self.sport_id,),
            )

        self.db.execute(
            """
            INSERT INTO seasons (sport_id, season_year, season_label, is_current)
            VALUES (?, ?, ?, ?)
            """,
            (self.sport_id, season_year, label, is_current),
        )

        result = self.db.fetchone("SELECT last_insert_rowid() as id")
        return result["id"]

    def _get_season_label(self, season_year: int) -> str:
        """
        Get human-readable season label.

        Override in subclasses for sport-specific formatting.
        """
        return str(season_year)

    # =========================================================================
    # Team Management
    # =========================================================================

    def upsert_team(self, team_data: dict[str, Any]) -> int:
        """
        Insert or update a team record.

        Args:
            team_data: Team data matching TeamModel schema

        Returns:
            Team ID
        """
        self.db.execute(
            """
            INSERT INTO teams (
                id, sport_id, league_id, name, abbreviation, logo_url,
                conference, division, country, city, founded,
                venue_name, venue_capacity, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name = excluded.name,
                abbreviation = excluded.abbreviation,
                logo_url = excluded.logo_url,
                conference = excluded.conference,
                division = excluded.division,
                country = excluded.country,
                city = excluded.city,
                venue_name = excluded.venue_name,
                venue_capacity = excluded.venue_capacity,
                updated_at = excluded.updated_at
            """,
            (
                team_data["id"],
                self.sport_id,
                team_data.get("league_id"),
                team_data["name"],
                team_data.get("abbreviation"),
                team_data.get("logo_url"),
                team_data.get("conference"),
                team_data.get("division"),
                team_data.get("country"),
                team_data.get("city"),
                team_data.get("founded"),
                team_data.get("venue_name"),
                team_data.get("venue_capacity"),
                int(time.time()),
            ),
        )
        return team_data["id"]

    # =========================================================================
    # Player Management
    # =========================================================================

    def upsert_player(self, player_data: dict[str, Any]) -> int:
        """
        Insert or update a player record.

        Args:
            player_data: Player data matching PlayerModel schema

        Returns:
            Player ID
        """
        self.db.execute(
            """
            INSERT INTO players (
                id, sport_id, first_name, last_name, full_name,
                position, position_group, nationality, birth_date, birth_place,
                height_cm, weight_kg, photo_url, current_team_id, jersey_number,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                first_name = excluded.first_name,
                last_name = excluded.last_name,
                full_name = excluded.full_name,
                position = excluded.position,
                position_group = excluded.position_group,
                nationality = excluded.nationality,
                photo_url = excluded.photo_url,
                current_team_id = excluded.current_team_id,
                jersey_number = excluded.jersey_number,
                updated_at = excluded.updated_at
            """,
            (
                player_data["id"],
                self.sport_id,
                player_data.get("first_name"),
                player_data.get("last_name"),
                player_data["full_name"],
                player_data.get("position"),
                player_data.get("position_group"),
                player_data.get("nationality"),
                player_data.get("birth_date"),
                player_data.get("birth_place"),
                player_data.get("height_cm"),
                player_data.get("weight_kg"),
                player_data.get("photo_url"),
                player_data.get("current_team_id"),
                player_data.get("jersey_number"),
                int(time.time()),
            ),
        )
        return player_data["id"]

    # =========================================================================
    # Abstract Methods (Must be implemented by subclasses)
    # =========================================================================

    @abstractmethod
    async def fetch_teams(self, season: int) -> list[dict[str, Any]]:
        """
        Fetch teams from API-Sports.

        Args:
            season: Season year

        Returns:
            List of team data dicts
        """
        pass

    @abstractmethod
    async def fetch_players(self, season: int, team_id: Optional[int] = None) -> list[dict[str, Any]]:
        """
        Fetch players from API-Sports.

        Args:
            season: Season year
            team_id: Optional team ID to filter by

        Returns:
            List of player data dicts
        """
        pass

    @abstractmethod
    async def fetch_player_stats(
        self,
        player_id: int,
        season: int,
    ) -> Optional[dict[str, Any]]:
        """
        Fetch player statistics from API-Sports.

        Args:
            player_id: Player ID
            season: Season year

        Returns:
            Raw stats response or None
        """
        pass

    @abstractmethod
    async def fetch_team_stats(
        self,
        team_id: int,
        season: int,
    ) -> Optional[dict[str, Any]]:
        """
        Fetch team statistics from API-Sports.

        Args:
            team_id: Team ID
            season: Season year

        Returns:
            Raw stats response or None
        """
        pass

    @abstractmethod
    def transform_player_stats(
        self,
        raw_stats: dict[str, Any],
        player_id: int,
        season_id: int,
        team_id: Optional[int] = None,
    ) -> dict[str, Any]:
        """
        Transform raw API stats to database schema.

        Args:
            raw_stats: Raw API response
            player_id: Player ID
            season_id: Season ID
            team_id: Team ID

        Returns:
            Dict matching the sport-specific stats table schema
        """
        pass

    @abstractmethod
    def transform_team_stats(
        self,
        raw_stats: dict[str, Any],
        team_id: int,
        season_id: int,
    ) -> dict[str, Any]:
        """
        Transform raw API team stats to database schema.

        Args:
            raw_stats: Raw API response
            team_id: Team ID
            season_id: Season ID

        Returns:
            Dict matching the sport-specific team stats table schema
        """
        pass

    @abstractmethod
    def upsert_player_stats(self, stats: dict[str, Any]) -> None:
        """
        Insert or update player statistics.

        Args:
            stats: Transformed stats dict
        """
        pass

    @abstractmethod
    def upsert_team_stats(self, stats: dict[str, Any]) -> None:
        """
        Insert or update team statistics.

        Args:
            stats: Transformed stats dict
        """
        pass

    # =========================================================================
    # Main Seeding Methods
    # =========================================================================

    async def seed_teams(self, season: int) -> int:
        """
        Seed all teams for a season.

        Args:
            season: Season year

        Returns:
            Number of teams seeded
        """
        season_id = self.ensure_season(season)
        sync_id = self._start_sync("full", "teams", season_id)

        try:
            teams = await self.fetch_teams(season)
            inserted = 0
            updated = 0

            for team_data in teams:
                existing = self.db.get_team(team_data["id"], self.sport_id)
                self.upsert_team(team_data)

                if existing:
                    updated += 1
                else:
                    inserted += 1

            self._complete_sync(sync_id, len(teams), inserted, updated)
            logger.info(
                "Seeded %d teams for %s %d (inserted: %d, updated: %d)",
                len(teams),
                self.sport_id,
                season,
                inserted,
                updated,
            )
            return len(teams)

        except Exception as e:
            self._fail_sync(sync_id, str(e))
            raise

    async def seed_players(self, season: int) -> int:
        """
        Seed all players for a season.

        Args:
            season: Season year

        Returns:
            Number of players seeded
        """
        season_id = self.ensure_season(season)
        sync_id = self._start_sync("full", "players", season_id)

        try:
            players = await self.fetch_players(season)
            inserted = 0
            updated = 0

            for player_data in players:
                existing = self.db.get_player(player_data["id"], self.sport_id)
                self.upsert_player(player_data)

                if existing:
                    updated += 1
                else:
                    inserted += 1

            self._complete_sync(sync_id, len(players), inserted, updated)
            logger.info(
                "Seeded %d players for %s %d (inserted: %d, updated: %d)",
                len(players),
                self.sport_id,
                season,
                inserted,
                updated,
            )
            return len(players)

        except Exception as e:
            self._fail_sync(sync_id, str(e))
            raise

    async def seed_player_stats(
        self,
        season: int,
        player_ids: Optional[list[int]] = None,
    ) -> int:
        """
        Seed player statistics for a season.

        Args:
            season: Season year
            player_ids: Optional list of specific player IDs to seed

        Returns:
            Number of stat records seeded
        """
        season_id = self.ensure_season(season)
        sync_id = self._start_sync("full", "player_stats", season_id)

        try:
            # Get players to process
            if player_ids:
                players = [
                    {"id": pid}
                    for pid in player_ids
                    if self.db.get_player(pid, self.sport_id)
                ]
            else:
                players = self.db.fetchall(
                    "SELECT id, current_team_id FROM players WHERE sport_id = ?",
                    (self.sport_id,),
                )

            processed = 0
            for player in players:
                player_id = player["id"]
                team_id = player.get("current_team_id")

                raw_stats = await self.fetch_player_stats(player_id, season)
                if raw_stats:
                    stats = self.transform_player_stats(
                        raw_stats, player_id, season_id, team_id
                    )
                    self.upsert_player_stats(stats)
                    processed += 1

            self._complete_sync(sync_id, len(players), processed, 0)
            logger.info(
                "Seeded stats for %d players for %s %d",
                processed,
                self.sport_id,
                season,
            )
            return processed

        except Exception as e:
            self._fail_sync(sync_id, str(e))
            raise

    async def seed_team_stats(self, season: int) -> int:
        """
        Seed team statistics for a season.

        Args:
            season: Season year

        Returns:
            Number of stat records seeded
        """
        season_id = self.ensure_season(season)
        sync_id = self._start_sync("full", "team_stats", season_id)

        try:
            teams = self.db.fetchall(
                "SELECT id FROM teams WHERE sport_id = ?",
                (self.sport_id,),
            )

            processed = 0
            for team in teams:
                team_id = team["id"]

                raw_stats = await self.fetch_team_stats(team_id, season)
                if raw_stats:
                    stats = self.transform_team_stats(raw_stats, team_id, season_id)
                    self.upsert_team_stats(stats)
                    processed += 1

            self._complete_sync(sync_id, len(teams), processed, 0)
            logger.info(
                "Seeded stats for %d teams for %s %d",
                processed,
                self.sport_id,
                season,
            )
            return processed

        except Exception as e:
            self._fail_sync(sync_id, str(e))
            raise

    async def seed_all(
        self,
        seasons: list[int],
        current_season: Optional[int] = None,
    ) -> dict[str, int]:
        """
        Seed all data for multiple seasons.

        Args:
            seasons: List of season years to seed
            current_season: Which season is the current one

        Returns:
            Summary of records seeded
        """
        summary = {
            "teams": 0,
            "players": 0,
            "player_stats": 0,
            "team_stats": 0,
        }

        for season in seasons:
            is_current = season == current_season

            # Ensure season exists
            self.ensure_season(season, is_current=is_current)

            # Seed in order: teams -> players -> stats
            summary["teams"] += await self.seed_teams(season)
            summary["players"] += await self.seed_players(season)
            summary["player_stats"] += await self.seed_player_stats(season)
            summary["team_stats"] += await self.seed_team_stats(season)

        return summary
