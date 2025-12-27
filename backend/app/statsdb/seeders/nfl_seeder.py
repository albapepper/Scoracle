"""
NFL-specific seeder for stats database.

Handles fetching and transforming NFL player and team statistics
from the API-Sports American Football API.

NFL stats are position-specific, so this seeder handles multiple
stat tables based on player position.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Optional

from .base import BaseSeeder

logger = logging.getLogger(__name__)


class NFLSeeder(BaseSeeder):
    """Seeder for NFL statistics."""

    sport_id = "NFL"

    # Position to stat table mapping
    POSITION_TABLES = {
        "QB": ["passing", "rushing"],
        "RB": ["rushing", "receiving"],
        "FB": ["rushing", "receiving"],
        "WR": ["receiving", "rushing"],
        "TE": ["receiving"],
        "OL": [],
        "OT": [],
        "OG": [],
        "C": [],
        "DL": ["defense"],
        "DE": ["defense"],
        "DT": ["defense"],
        "NT": ["defense"],
        "LB": ["defense"],
        "ILB": ["defense"],
        "OLB": ["defense"],
        "MLB": ["defense"],
        "DB": ["defense"],
        "CB": ["defense"],
        "S": ["defense"],
        "FS": ["defense"],
        "SS": ["defense"],
        "K": ["kicking"],
        "P": ["kicking"],
        "LS": [],
    }

    def _get_season_label(self, season_year: int) -> str:
        """NFL seasons are single year."""
        return str(season_year)

    # =========================================================================
    # Data Fetching
    # =========================================================================

    async def fetch_teams(
        self,
        season: int,
        league_id: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        """Fetch NFL teams from API-Sports.

        Note: NFL doesn't use league_id, parameter included for interface compliance.
        """
        teams = await self.api.list_teams("NFL", season=str(season))

        result = []
        for team in teams:
            result.append({
                "id": team["id"],
                "name": team["name"],
                "abbreviation": team.get("abbreviation") or team.get("code"),
                "logo_url": team.get("logo_url") or team.get("logo"),
                "conference": team.get("conference"),
                "division": team.get("division"),
                "city": team.get("city"),
            })

        return result

    async def fetch_players(
        self,
        season: int,
        team_id: Optional[int] = None,
        league_id: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        """Fetch NFL players from API-Sports.

        Note: NFL doesn't use league_id, parameter included for interface compliance.
        Uses paginated fetching (all players across all teams).
        """
        all_players = []
        page = 1

        while True:
            players = await self.api.list_players(
                "NFL",
                season=str(season),
                page=page,
            )

            if not players:
                break

            for player in players:
                team = player.get("team") or {}
                current_team_id = team.get("id") if isinstance(team, dict) else None
                position = player.get("position")

                all_players.append({
                    "id": player["id"],
                    "first_name": player.get("first_name") or player.get("firstname"),
                    "last_name": player.get("last_name") or player.get("lastname"),
                    "full_name": self._build_full_name(player),
                    "position": position,
                    "position_group": self._get_position_group(position),
                    "nationality": player.get("nationality"),
                    "birth_date": player.get("birth_date"),
                    "height_cm": self._parse_height(player),
                    "weight_kg": self._parse_weight(player),
                    "photo_url": player.get("photo_url"),
                    "current_team_id": current_team_id,
                    "jersey_number": player.get("number"),
                })

            page += 1

            if page > 100:
                logger.warning("Reached page limit for NFL players")
                break

        return all_players

    async def fetch_player_stats(
        self,
        player_id: int,
        season: int,
    ) -> Optional[dict[str, Any]]:
        """Fetch player statistics from API-Sports."""
        try:
            stats = await self.api.get_player_statistics(
                str(player_id),
                "NFL",
                str(season),
            )
            return stats
        except Exception as e:
            logger.warning("Failed to fetch stats for player %d: %s", player_id, e)
            return None

    async def fetch_team_stats(
        self,
        team_id: int,
        season: int,
    ) -> Optional[dict[str, Any]]:
        """Fetch team statistics from API-Sports."""
        try:
            stats = await self.api.get_team_statistics(
                str(team_id),
                "NFL",
                str(season),
            )
            return stats
        except Exception as e:
            logger.warning("Failed to fetch stats for team %d: %s", team_id, e)
            return None

    async def fetch_team_profile(self, team_id: int) -> Optional[dict[str, Any]]:
        """Fetch detailed team profile from API-Sports.

        Returns extended team info including venue details.
        API: GET /teams?id={team_id}
        """
        try:
            response = await self.api.get_team_profile(str(team_id), "NFL")

            if not response:
                return None

            team = response

            # Handle country - may be string or dict
            country = team.get("country")
            if isinstance(country, dict):
                country = country.get("name") or country.get("code") or "USA"
            elif not country:
                country = "USA"

            # Handle venue - may be dict or string
            venue = team.get("venue")
            if isinstance(venue, dict):
                venue_name = venue.get("name") or team.get("stadium")
                venue_city = venue.get("city") or team.get("city")
                venue_capacity = venue.get("capacity")
                venue_surface = venue.get("surface")
            else:
                venue_name = team.get("stadium")
                venue_city = team.get("city")
                venue_capacity = None
                venue_surface = None

            return {
                "id": team["id"],
                "name": team["name"],
                "abbreviation": team.get("abbreviation") or team.get("code"),
                "logo_url": team.get("logo_url") or team.get("logo"),
                "conference": team.get("conference"),
                "division": team.get("division"),
                "city": team.get("city"),
                "country": country,
                "founded": team.get("founded") or team.get("established"),
                "venue_name": venue_name,
                "venue_city": venue_city,
                "venue_capacity": venue_capacity,
                "venue_surface": venue_surface,
            }
        except Exception as e:
            logger.warning("Failed to fetch profile for team %d: %s", team_id, e)
            return None

    async def fetch_player_profile(self, player_id: int) -> Optional[dict[str, Any]]:
        """Fetch detailed player profile from API-Sports.

        Returns extended player info including full biographical data.
        API: GET /players?id={player_id}
        """
        try:
            response = await self.api.get_player_profile(str(player_id), "NFL")

            if not response:
                return None

            player = response

            # Extract team from nested structure
            team = player.get("team") or {}
            current_team_id = team.get("id") if isinstance(team, dict) else None
            position = player.get("position")

            return {
                "id": player["id"],
                "first_name": player.get("first_name") or player.get("firstname"),
                "last_name": player.get("last_name") or player.get("lastname"),
                "full_name": self._build_full_name(player),
                "position": position,
                "position_group": self._get_position_group(position),
                "nationality": player.get("nationality") or player.get("country"),
                "birth_date": player.get("birth_date") or player.get("birth", {}).get("date") if isinstance(player.get("birth"), dict) else player.get("birth_date"),
                "birth_place": player.get("birth", {}).get("place") if isinstance(player.get("birth"), dict) else None,
                "height_cm": self._parse_height(player),
                "weight_kg": self._parse_weight(player),
                "photo_url": player.get("photo_url") or player.get("image"),
                "current_team_id": current_team_id,
                "jersey_number": player.get("number"),
            }
        except Exception as e:
            logger.warning("Failed to fetch profile for player %d: %s", player_id, e)
            return None

    # =========================================================================
    # Data Transformation
    # =========================================================================

    def transform_player_stats(
        self,
        raw_stats: dict[str, Any],
        player_id: int,
        season_id: int,
        team_id: Optional[int] = None,
    ) -> dict[str, Any]:
        """
        Transform API stats to database schema.

        Returns a dict with keys for each stat type the player has.
        """
        stats = raw_stats if isinstance(raw_stats, dict) else {}

        if "response" in stats and stats["response"]:
            stats = stats["response"][0] if isinstance(stats["response"], list) else stats["response"]

        result = {
            "player_id": player_id,
            "season_id": season_id,
            "team_id": team_id,
        }

        # Get player position to determine which stats to extract
        player = self.db.get_player(player_id, self.sport_id)
        position = player.get("position") if player else None

        # Extract stats based on position
        stat_tables = self.POSITION_TABLES.get(position, [])

        if "passing" in stat_tables or self._has_passing_stats(stats):
            result["passing"] = self._transform_passing_stats(stats, player_id, season_id, team_id)

        if "rushing" in stat_tables or self._has_rushing_stats(stats):
            result["rushing"] = self._transform_rushing_stats(stats, player_id, season_id, team_id)

        if "receiving" in stat_tables or self._has_receiving_stats(stats):
            result["receiving"] = self._transform_receiving_stats(stats, player_id, season_id, team_id)

        if "defense" in stat_tables or self._has_defense_stats(stats):
            result["defense"] = self._transform_defense_stats(stats, player_id, season_id, team_id)

        if "kicking" in stat_tables or self._has_kicking_stats(stats):
            result["kicking"] = self._transform_kicking_stats(stats, player_id, season_id, team_id)

        return result

    def _transform_passing_stats(
        self,
        stats: dict,
        player_id: int,
        season_id: int,
        team_id: Optional[int],
    ) -> dict[str, Any]:
        """Transform passing statistics."""
        passing = stats.get("passing", {}) or {}

        attempts = passing.get("attempts", 0) or 0
        completions = passing.get("completions", 0) or 0
        yards = passing.get("yards", 0) or 0
        touchdowns = passing.get("touchdowns", 0) or 0
        interceptions = passing.get("interceptions", 0) or 0

        games = stats.get("games", {}).get("played", 1) or 1

        return {
            "player_id": player_id,
            "season_id": season_id,
            "team_id": team_id,
            "games_played": games,
            "games_started": stats.get("games", {}).get("started", 0) or 0,
            "pass_attempts": attempts,
            "pass_completions": completions,
            "completion_pct": self._safe_pct(completions, attempts),
            "pass_yards": yards,
            "pass_yards_per_game": round(yards / games, 1),
            "yards_per_attempt": round(yards / max(attempts, 1), 1),
            "yards_per_completion": round(yards / max(completions, 1), 1),
            "pass_touchdowns": touchdowns,
            "interceptions": interceptions,
            "td_int_ratio": round(touchdowns / max(interceptions, 1), 2),
            "passer_rating": self._calculate_passer_rating(completions, attempts, yards, touchdowns, interceptions),
            "sacks_taken": passing.get("sacks", 0) or 0,
            "sack_yards_lost": passing.get("sack_yards", 0) or 0,
            "longest_pass": passing.get("longest", 0) or 0,
            "updated_at": int(time.time()),
        }

    def _transform_rushing_stats(
        self,
        stats: dict,
        player_id: int,
        season_id: int,
        team_id: Optional[int],
    ) -> dict[str, Any]:
        """Transform rushing statistics."""
        rushing = stats.get("rushing", {}) or {}

        attempts = rushing.get("attempts", 0) or 0
        yards = rushing.get("yards", 0) or 0
        touchdowns = rushing.get("touchdowns", 0) or 0

        games = stats.get("games", {}).get("played", 1) or 1

        return {
            "player_id": player_id,
            "season_id": season_id,
            "team_id": team_id,
            "games_played": games,
            "rush_attempts": attempts,
            "rush_yards": yards,
            "rush_yards_per_game": round(yards / games, 1),
            "yards_per_carry": round(yards / max(attempts, 1), 1),
            "rush_touchdowns": touchdowns,
            "longest_rush": rushing.get("longest", 0) or 0,
            "fumbles": rushing.get("fumbles", 0) or stats.get("fumbles", {}).get("total", 0) or 0,
            "fumbles_lost": rushing.get("fumbles_lost", 0) or stats.get("fumbles", {}).get("lost", 0) or 0,
            "updated_at": int(time.time()),
        }

    def _transform_receiving_stats(
        self,
        stats: dict,
        player_id: int,
        season_id: int,
        team_id: Optional[int],
    ) -> dict[str, Any]:
        """Transform receiving statistics."""
        receiving = stats.get("receiving", {}) or {}

        targets = receiving.get("targets", 0) or 0
        receptions = receiving.get("receptions", 0) or 0
        yards = receiving.get("yards", 0) or 0
        touchdowns = receiving.get("touchdowns", 0) or 0

        games = stats.get("games", {}).get("played", 1) or 1

        return {
            "player_id": player_id,
            "season_id": season_id,
            "team_id": team_id,
            "games_played": games,
            "targets": targets,
            "receptions": receptions,
            "catch_pct": self._safe_pct(receptions, targets),
            "receiving_yards": yards,
            "receiving_yards_per_game": round(yards / games, 1),
            "yards_per_reception": round(yards / max(receptions, 1), 1),
            "yards_per_target": round(yards / max(targets, 1), 1),
            "receiving_touchdowns": touchdowns,
            "longest_reception": receiving.get("longest", 0) or 0,
            "yards_after_catch": receiving.get("yac", 0) or 0,
            "fumbles": receiving.get("fumbles", 0) or 0,
            "fumbles_lost": receiving.get("fumbles_lost", 0) or 0,
            "updated_at": int(time.time()),
        }

    def _transform_defense_stats(
        self,
        stats: dict,
        player_id: int,
        season_id: int,
        team_id: Optional[int],
    ) -> dict[str, Any]:
        """Transform defensive statistics."""
        defense = stats.get("defense", {}) or {}
        tackles_data = defense.get("tackles", {}) or {}

        tackles_total = tackles_data.get("total", 0) or defense.get("tackles", 0) or 0
        tackles_solo = tackles_data.get("solo", 0) or 0
        tackles_assist = tackles_data.get("assists", 0) or 0

        games = stats.get("games", {}).get("played", 1) or 1

        return {
            "player_id": player_id,
            "season_id": season_id,
            "team_id": team_id,
            "games_played": games,
            "games_started": stats.get("games", {}).get("started", 0) or 0,
            "tackles_total": tackles_total,
            "tackles_solo": tackles_solo,
            "tackles_assist": tackles_assist,
            "tackles_for_loss": defense.get("tfl", 0) or 0,
            "sacks": defense.get("sacks", 0) or 0,
            "sack_yards": defense.get("sack_yards", 0) or 0,
            "qb_hits": defense.get("qb_hits", 0) or 0,
            "interceptions": defense.get("interceptions", 0) or 0,
            "int_yards": defense.get("int_yards", 0) or 0,
            "int_touchdowns": defense.get("int_tds", 0) or 0,
            "passes_defended": defense.get("passes_defended", 0) or 0,
            "forced_fumbles": defense.get("forced_fumbles", 0) or 0,
            "fumble_recoveries": defense.get("fumble_recoveries", 0) or 0,
            "updated_at": int(time.time()),
        }

    def _transform_kicking_stats(
        self,
        stats: dict,
        player_id: int,
        season_id: int,
        team_id: Optional[int],
    ) -> dict[str, Any]:
        """Transform kicking/punting statistics."""
        kicking = stats.get("kicking", {}) or {}
        punting = stats.get("punting", {}) or {}

        fg_made = kicking.get("fg_made", 0) or 0
        fg_attempts = kicking.get("fg_attempts", 0) or 0
        xp_made = kicking.get("xp_made", 0) or 0
        xp_attempts = kicking.get("xp_attempts", 0) or 0

        games = stats.get("games", {}).get("played", 1) or 1

        return {
            "player_id": player_id,
            "season_id": season_id,
            "team_id": team_id,
            "games_played": games,
            "fg_attempts": fg_attempts,
            "fg_made": fg_made,
            "fg_pct": self._safe_pct(fg_made, fg_attempts),
            "fg_long": kicking.get("fg_long", 0) or 0,
            "xp_attempts": xp_attempts,
            "xp_made": xp_made,
            "xp_pct": self._safe_pct(xp_made, xp_attempts),
            "total_points": (fg_made * 3) + xp_made,
            "punts": punting.get("punts", 0) or 0,
            "punt_yards": punting.get("yards", 0) or 0,
            "punt_avg": punting.get("average", 0) or 0,
            "punt_long": punting.get("longest", 0) or 0,
            "punts_inside_20": punting.get("inside_20", 0) or 0,
            "touchbacks": punting.get("touchbacks", 0) or 0,
            "updated_at": int(time.time()),
        }

    def transform_team_stats(
        self,
        raw_stats: dict[str, Any],
        team_id: int,
        season_id: int,
    ) -> dict[str, Any]:
        """Transform API team stats to database schema."""
        stats = raw_stats if isinstance(raw_stats, dict) else {}

        if "response" in stats and stats["response"]:
            stats = stats["response"][0] if isinstance(stats["response"], list) else stats["response"]

        games = stats.get("games", {}) or {}
        wins = games.get("wins", 0) or 0
        losses = games.get("losses", 0) or 0
        ties = games.get("ties", 0) or 0
        games_played = wins + losses + ties

        offense = stats.get("offense", {}) or {}
        defense = stats.get("defense", {}) or {}

        return {
            "team_id": team_id,
            "season_id": season_id,
            "games_played": games_played,
            "wins": wins,
            "losses": losses,
            "ties": ties,
            "win_pct": self._safe_pct(wins, games_played),
            "points_for": stats.get("points", {}).get("for", 0) or 0,
            "points_against": stats.get("points", {}).get("against", 0) or 0,
            "point_differential": (stats.get("points", {}).get("for", 0) or 0) - (stats.get("points", {}).get("against", 0) or 0),
            "total_yards": offense.get("yards", 0) or 0,
            "yards_per_game": round(offense.get("yards", 0) / max(games_played, 1), 1),
            "pass_yards": offense.get("pass_yards", 0) or 0,
            "rush_yards": offense.get("rush_yards", 0) or 0,
            "turnovers": offense.get("turnovers", 0) or 0,
            "yards_allowed": defense.get("yards", 0) or 0,
            "pass_yards_allowed": defense.get("pass_yards", 0) or 0,
            "rush_yards_allowed": defense.get("rush_yards", 0) or 0,
            "takeaways": defense.get("takeaways", 0) or 0,
            "sacks": defense.get("sacks", 0) or 0,
            "updated_at": int(time.time()),
        }

    # =========================================================================
    # Database Operations
    # =========================================================================

    def upsert_player_stats(self, stats: dict[str, Any]) -> None:
        """Insert or update NFL player statistics."""
        player_id = stats["player_id"]
        season_id = stats["season_id"]

        if "passing" in stats:
            self._upsert_passing_stats(stats["passing"])

        if "rushing" in stats:
            self._upsert_rushing_stats(stats["rushing"])

        if "receiving" in stats:
            self._upsert_receiving_stats(stats["receiving"])

        if "defense" in stats:
            self._upsert_defense_stats(stats["defense"])

        if "kicking" in stats:
            self._upsert_kicking_stats(stats["kicking"])

    def _upsert_passing_stats(self, stats: dict[str, Any]) -> None:
        """Upsert passing statistics."""
        self.db.execute(
            """
            INSERT INTO nfl_player_passing (
                player_id, season_id, team_id, games_played, games_started,
                pass_attempts, pass_completions, completion_pct,
                pass_yards, pass_yards_per_game, yards_per_attempt, yards_per_completion,
                pass_touchdowns, interceptions, td_int_ratio, passer_rating,
                sacks_taken, sack_yards_lost, longest_pass, updated_at
            )
            VALUES (
                :player_id, :season_id, :team_id, :games_played, :games_started,
                :pass_attempts, :pass_completions, :completion_pct,
                :pass_yards, :pass_yards_per_game, :yards_per_attempt, :yards_per_completion,
                :pass_touchdowns, :interceptions, :td_int_ratio, :passer_rating,
                :sacks_taken, :sack_yards_lost, :longest_pass, :updated_at
            )
            ON CONFLICT(player_id, season_id) DO UPDATE SET
                team_id = excluded.team_id,
                games_played = excluded.games_played,
                games_started = excluded.games_started,
                pass_attempts = excluded.pass_attempts,
                pass_completions = excluded.pass_completions,
                completion_pct = excluded.completion_pct,
                pass_yards = excluded.pass_yards,
                pass_yards_per_game = excluded.pass_yards_per_game,
                yards_per_attempt = excluded.yards_per_attempt,
                yards_per_completion = excluded.yards_per_completion,
                pass_touchdowns = excluded.pass_touchdowns,
                interceptions = excluded.interceptions,
                td_int_ratio = excluded.td_int_ratio,
                passer_rating = excluded.passer_rating,
                sacks_taken = excluded.sacks_taken,
                sack_yards_lost = excluded.sack_yards_lost,
                longest_pass = excluded.longest_pass,
                updated_at = excluded.updated_at
            """,
            stats,
        )

    def _upsert_rushing_stats(self, stats: dict[str, Any]) -> None:
        """Upsert rushing statistics."""
        self.db.execute(
            """
            INSERT INTO nfl_player_rushing (
                player_id, season_id, team_id, games_played,
                rush_attempts, rush_yards, rush_yards_per_game, yards_per_carry,
                rush_touchdowns, longest_rush, fumbles, fumbles_lost, updated_at
            )
            VALUES (
                :player_id, :season_id, :team_id, :games_played,
                :rush_attempts, :rush_yards, :rush_yards_per_game, :yards_per_carry,
                :rush_touchdowns, :longest_rush, :fumbles, :fumbles_lost, :updated_at
            )
            ON CONFLICT(player_id, season_id) DO UPDATE SET
                team_id = excluded.team_id,
                games_played = excluded.games_played,
                rush_attempts = excluded.rush_attempts,
                rush_yards = excluded.rush_yards,
                rush_yards_per_game = excluded.rush_yards_per_game,
                yards_per_carry = excluded.yards_per_carry,
                rush_touchdowns = excluded.rush_touchdowns,
                longest_rush = excluded.longest_rush,
                fumbles = excluded.fumbles,
                fumbles_lost = excluded.fumbles_lost,
                updated_at = excluded.updated_at
            """,
            stats,
        )

    def _upsert_receiving_stats(self, stats: dict[str, Any]) -> None:
        """Upsert receiving statistics."""
        self.db.execute(
            """
            INSERT INTO nfl_player_receiving (
                player_id, season_id, team_id, games_played,
                targets, receptions, catch_pct,
                receiving_yards, receiving_yards_per_game, yards_per_reception, yards_per_target,
                receiving_touchdowns, longest_reception, yards_after_catch,
                fumbles, fumbles_lost, updated_at
            )
            VALUES (
                :player_id, :season_id, :team_id, :games_played,
                :targets, :receptions, :catch_pct,
                :receiving_yards, :receiving_yards_per_game, :yards_per_reception, :yards_per_target,
                :receiving_touchdowns, :longest_reception, :yards_after_catch,
                :fumbles, :fumbles_lost, :updated_at
            )
            ON CONFLICT(player_id, season_id) DO UPDATE SET
                team_id = excluded.team_id,
                games_played = excluded.games_played,
                targets = excluded.targets,
                receptions = excluded.receptions,
                catch_pct = excluded.catch_pct,
                receiving_yards = excluded.receiving_yards,
                receiving_yards_per_game = excluded.receiving_yards_per_game,
                yards_per_reception = excluded.yards_per_reception,
                yards_per_target = excluded.yards_per_target,
                receiving_touchdowns = excluded.receiving_touchdowns,
                longest_reception = excluded.longest_reception,
                yards_after_catch = excluded.yards_after_catch,
                fumbles = excluded.fumbles,
                fumbles_lost = excluded.fumbles_lost,
                updated_at = excluded.updated_at
            """,
            stats,
        )

    def _upsert_defense_stats(self, stats: dict[str, Any]) -> None:
        """Upsert defensive statistics."""
        self.db.execute(
            """
            INSERT INTO nfl_player_defense (
                player_id, season_id, team_id, games_played, games_started,
                tackles_total, tackles_solo, tackles_assist, tackles_for_loss,
                sacks, sack_yards, qb_hits,
                interceptions, int_yards, int_touchdowns, passes_defended,
                forced_fumbles, fumble_recoveries, updated_at
            )
            VALUES (
                :player_id, :season_id, :team_id, :games_played, :games_started,
                :tackles_total, :tackles_solo, :tackles_assist, :tackles_for_loss,
                :sacks, :sack_yards, :qb_hits,
                :interceptions, :int_yards, :int_touchdowns, :passes_defended,
                :forced_fumbles, :fumble_recoveries, :updated_at
            )
            ON CONFLICT(player_id, season_id) DO UPDATE SET
                team_id = excluded.team_id,
                games_played = excluded.games_played,
                games_started = excluded.games_started,
                tackles_total = excluded.tackles_total,
                tackles_solo = excluded.tackles_solo,
                tackles_assist = excluded.tackles_assist,
                tackles_for_loss = excluded.tackles_for_loss,
                sacks = excluded.sacks,
                sack_yards = excluded.sack_yards,
                qb_hits = excluded.qb_hits,
                interceptions = excluded.interceptions,
                int_yards = excluded.int_yards,
                int_touchdowns = excluded.int_touchdowns,
                passes_defended = excluded.passes_defended,
                forced_fumbles = excluded.forced_fumbles,
                fumble_recoveries = excluded.fumble_recoveries,
                updated_at = excluded.updated_at
            """,
            stats,
        )

    def _upsert_kicking_stats(self, stats: dict[str, Any]) -> None:
        """Upsert kicking/punting statistics."""
        self.db.execute(
            """
            INSERT INTO nfl_player_kicking (
                player_id, season_id, team_id, games_played,
                fg_attempts, fg_made, fg_pct, fg_long,
                xp_attempts, xp_made, xp_pct, total_points,
                punts, punt_yards, punt_avg, punt_long, punts_inside_20, touchbacks,
                updated_at
            )
            VALUES (
                :player_id, :season_id, :team_id, :games_played,
                :fg_attempts, :fg_made, :fg_pct, :fg_long,
                :xp_attempts, :xp_made, :xp_pct, :total_points,
                :punts, :punt_yards, :punt_avg, :punt_long, :punts_inside_20, :touchbacks,
                :updated_at
            )
            ON CONFLICT(player_id, season_id) DO UPDATE SET
                team_id = excluded.team_id,
                games_played = excluded.games_played,
                fg_attempts = excluded.fg_attempts,
                fg_made = excluded.fg_made,
                fg_pct = excluded.fg_pct,
                fg_long = excluded.fg_long,
                xp_attempts = excluded.xp_attempts,
                xp_made = excluded.xp_made,
                xp_pct = excluded.xp_pct,
                total_points = excluded.total_points,
                punts = excluded.punts,
                punt_yards = excluded.punt_yards,
                punt_avg = excluded.punt_avg,
                punt_long = excluded.punt_long,
                punts_inside_20 = excluded.punts_inside_20,
                touchbacks = excluded.touchbacks,
                updated_at = excluded.updated_at
            """,
            stats,
        )

    def upsert_team_stats(self, stats: dict[str, Any]) -> None:
        """Insert or update NFL team statistics."""
        self.db.execute(
            """
            INSERT INTO nfl_team_stats (
                team_id, season_id, games_played, wins, losses, ties, win_pct,
                points_for, points_against, point_differential,
                total_yards, yards_per_game, pass_yards, rush_yards, turnovers,
                yards_allowed, pass_yards_allowed, rush_yards_allowed, takeaways, sacks,
                updated_at
            )
            VALUES (
                :team_id, :season_id, :games_played, :wins, :losses, :ties, :win_pct,
                :points_for, :points_against, :point_differential,
                :total_yards, :yards_per_game, :pass_yards, :rush_yards, :turnovers,
                :yards_allowed, :pass_yards_allowed, :rush_yards_allowed, :takeaways, :sacks,
                :updated_at
            )
            ON CONFLICT(team_id, season_id) DO UPDATE SET
                games_played = excluded.games_played,
                wins = excluded.wins,
                losses = excluded.losses,
                ties = excluded.ties,
                win_pct = excluded.win_pct,
                points_for = excluded.points_for,
                points_against = excluded.points_against,
                point_differential = excluded.point_differential,
                total_yards = excluded.total_yards,
                yards_per_game = excluded.yards_per_game,
                pass_yards = excluded.pass_yards,
                rush_yards = excluded.rush_yards,
                turnovers = excluded.turnovers,
                yards_allowed = excluded.yards_allowed,
                pass_yards_allowed = excluded.pass_yards_allowed,
                rush_yards_allowed = excluded.rush_yards_allowed,
                takeaways = excluded.takeaways,
                sacks = excluded.sacks,
                updated_at = excluded.updated_at
            """,
            stats,
        )

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _build_full_name(self, player: dict) -> str:
        """Build full name from first and last name."""
        first = player.get("first_name") or player.get("firstname") or ""
        last = player.get("last_name") or player.get("lastname") or ""
        return f"{first} {last}".strip() or "Unknown"

    def _get_position_group(self, position: Optional[str]) -> Optional[str]:
        """Map position to position group."""
        if not position:
            return None

        position = position.upper()

        offense_skill = {"QB", "RB", "FB", "WR", "TE"}
        offense_line = {"OL", "OT", "OG", "C", "T", "G"}
        defense_line = {"DL", "DE", "DT", "NT"}
        linebackers = {"LB", "ILB", "OLB", "MLB"}
        secondary = {"DB", "CB", "S", "FS", "SS"}
        special_teams = {"K", "P", "LS"}

        if position in offense_skill:
            return "Offense - Skill"
        elif position in offense_line:
            return "Offense - Line"
        elif position in defense_line:
            return "Defense - Line"
        elif position in linebackers:
            return "Defense - Linebacker"
        elif position in secondary:
            return "Defense - Secondary"
        elif position in special_teams:
            return "Special Teams"

        return None

    def _parse_height(self, player: dict) -> Optional[int]:
        """Parse height to centimeters."""
        height = player.get("height")
        if not height:
            return None

        if isinstance(height, str) and "-" in height:
            try:
                feet, inches = map(int, height.split("-"))
                return int((feet * 12 + inches) * 2.54)
            except (ValueError, TypeError):
                pass

        return None

    def _parse_weight(self, player: dict) -> Optional[int]:
        """Parse weight to kilograms."""
        weight = player.get("weight")
        if not weight:
            return None

        if isinstance(weight, (int, float)):
            # Assume pounds
            return int(weight * 0.453592)
        elif isinstance(weight, str):
            try:
                return int(float(weight) * 0.453592)
            except (ValueError, TypeError):
                pass

        return None

    def _safe_pct(self, made: int, attempted: int) -> float:
        """Calculate percentage safely."""
        if not attempted:
            return 0.0
        return round((made / attempted) * 100, 1)

    def _calculate_passer_rating(
        self,
        completions: int,
        attempts: int,
        yards: int,
        touchdowns: int,
        interceptions: int,
    ) -> float:
        """Calculate NFL passer rating."""
        if attempts == 0:
            return 0.0

        # NFL passer rating formula
        a = max(0, min(((completions / attempts) - 0.3) * 5, 2.375))
        b = max(0, min(((yards / attempts) - 3) * 0.25, 2.375))
        c = max(0, min((touchdowns / attempts) * 20, 2.375))
        d = max(0, min(2.375 - ((interceptions / attempts) * 25), 2.375))

        rating = ((a + b + c + d) / 6) * 100
        return round(rating, 1)

    def _has_passing_stats(self, stats: dict) -> bool:
        """Check if stats contain passing data."""
        passing = stats.get("passing", {})
        return bool(passing and (passing.get("attempts", 0) or passing.get("yards", 0)))

    def _has_rushing_stats(self, stats: dict) -> bool:
        """Check if stats contain rushing data."""
        rushing = stats.get("rushing", {})
        return bool(rushing and (rushing.get("attempts", 0) or rushing.get("yards", 0)))

    def _has_receiving_stats(self, stats: dict) -> bool:
        """Check if stats contain receiving data."""
        receiving = stats.get("receiving", {})
        return bool(receiving and (receiving.get("targets", 0) or receiving.get("receptions", 0)))

    def _has_defense_stats(self, stats: dict) -> bool:
        """Check if stats contain defensive data."""
        defense = stats.get("defense", {})
        return bool(defense and (defense.get("tackles", 0) or defense.get("sacks", 0)))

    def _has_kicking_stats(self, stats: dict) -> bool:
        """Check if stats contain kicking/punting data."""
        kicking = stats.get("kicking", {})
        punting = stats.get("punting", {})
        return bool(kicking or punting)
