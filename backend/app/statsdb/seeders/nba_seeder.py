"""
NBA-specific seeder for stats database.

Handles fetching and transforming NBA player and team statistics
from the API-Sports NBA API.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Optional

from .base import BaseSeeder

logger = logging.getLogger(__name__)


class NBASeeder(BaseSeeder):
    """Seeder for NBA statistics."""

    sport_id = "NBA"

    def _get_season_label(self, season_year: int) -> str:
        """NBA seasons span two years (e.g., 2024-25)."""
        next_year = (season_year + 1) % 100
        return f"{season_year}-{next_year:02d}"

    # =========================================================================
    # Data Fetching
    # =========================================================================

    async def fetch_teams(self, season: int) -> list[dict[str, Any]]:
        """Fetch NBA teams from API-Sports."""
        teams = await self.api.list_teams(sport="NBA", season=season)

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
    ) -> list[dict[str, Any]]:
        """Fetch NBA players from API-Sports."""
        all_players = []
        page = 1

        while True:
            players = await self.api.list_players(
                sport="NBA",
                season=season,
                page=page,
            )

            if not players:
                break

            for player in players:
                # Extract team ID from nested structure
                team = player.get("team") or {}
                current_team_id = team.get("id") if isinstance(team, dict) else None

                all_players.append({
                    "id": player["id"],
                    "first_name": player.get("first_name") or player.get("firstname"),
                    "last_name": player.get("last_name") or player.get("lastname"),
                    "full_name": self._build_full_name(player),
                    "position": player.get("position"),
                    "position_group": self._get_position_group(player.get("position")),
                    "nationality": player.get("nationality") or player.get("country"),
                    "birth_date": player.get("birth_date") or player.get("birth", {}).get("date"),
                    "height_cm": self._parse_height(player),
                    "weight_kg": self._parse_weight(player),
                    "photo_url": player.get("photo_url"),
                    "current_team_id": current_team_id,
                    "jersey_number": player.get("jersey"),
                })

            page += 1

            # Safety limit
            if page > 50:
                logger.warning("Reached page limit for NBA players")
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
                player_id=player_id,
                sport="NBA",
                season=season,
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
                team_id=team_id,
                sport="NBA",
                season=season,
            )
            return stats
        except Exception as e:
            logger.warning("Failed to fetch stats for team %d: %s", team_id, e)
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
        """Transform API stats to database schema."""
        # API-Sports NBA stats structure varies, handle common patterns
        stats = raw_stats if isinstance(raw_stats, dict) else {}

        # Try to extract from nested structure
        if "response" in stats and stats["response"]:
            stats = stats["response"][0] if isinstance(stats["response"], list) else stats["response"]

        # Extract games/minutes
        games = stats.get("games", {}) if isinstance(stats.get("games"), dict) else {}
        games_played = games.get("played") or stats.get("games_played", 0)
        games_started = games.get("started") or stats.get("games_started", 0)
        minutes = stats.get("min") or stats.get("minutes", 0)

        # Points
        points = stats.get("points", {}) if isinstance(stats.get("points"), dict) else {}
        points_total = points.get("total") or stats.get("points_total", 0) or 0

        # Field goals
        fg = stats.get("fgm", {}) if isinstance(stats.get("fgm"), dict) else {}
        fgm = fg.get("made") or stats.get("fgm", 0) or 0
        fga = fg.get("attempted") or stats.get("fga", 0) or 0
        fg_pct = self._safe_pct(fgm, fga) or stats.get("fgp", 0) or 0

        # Three pointers
        tp = stats.get("tpm", {}) if isinstance(stats.get("tpm"), dict) else {}
        tpm = tp.get("made") or stats.get("tpm", 0) or 0
        tpa = tp.get("attempted") or stats.get("tpa", 0) or 0
        tp_pct = self._safe_pct(tpm, tpa) or stats.get("tpp", 0) or 0

        # Free throws
        ft = stats.get("ftm", {}) if isinstance(stats.get("ftm"), dict) else {}
        ftm = ft.get("made") or stats.get("ftm", 0) or 0
        fta = ft.get("attempted") or stats.get("fta", 0) or 0
        ft_pct = self._safe_pct(ftm, fta) or stats.get("ftp", 0) or 0

        # Rebounds
        rebounds = stats.get("rebounds", {}) if isinstance(stats.get("rebounds"), dict) else {}
        off_reb = rebounds.get("offensive") or stats.get("offReb", 0) or 0
        def_reb = rebounds.get("defensive") or stats.get("defReb", 0) or 0
        tot_reb = rebounds.get("total") or stats.get("totReb", 0) or off_reb + def_reb

        # Other stats
        assists = stats.get("assists") or stats.get("assists", 0) or 0
        turnovers = stats.get("turnovers") or stats.get("turnovers", 0) or 0
        steals = stats.get("steals") or stats.get("steals", 0) or 0
        blocks = stats.get("blocks") or stats.get("blocks", 0) or 0
        fouls = stats.get("pFouls") or stats.get("personal_fouls", 0) or 0
        plus_minus = stats.get("plusMinus") or stats.get("plus_minus", 0) or 0

        # Calculate per-game averages
        gp = max(games_played, 1)  # Avoid division by zero

        return {
            "player_id": player_id,
            "season_id": season_id,
            "team_id": team_id,
            "games_played": games_played,
            "games_started": games_started,
            "minutes_total": self._parse_minutes_total(minutes),
            "minutes_per_game": self._parse_minutes_total(minutes) / gp if isinstance(minutes, (int, float)) else 0,
            "points_total": points_total,
            "points_per_game": round(points_total / gp, 1) if points_total else 0,
            "fgm": fgm,
            "fga": fga,
            "fg_pct": fg_pct,
            "tpm": tpm,
            "tpa": tpa,
            "tp_pct": tp_pct,
            "ftm": ftm,
            "fta": fta,
            "ft_pct": ft_pct,
            "offensive_rebounds": off_reb,
            "defensive_rebounds": def_reb,
            "total_rebounds": tot_reb,
            "rebounds_per_game": round(tot_reb / gp, 1) if tot_reb else 0,
            "assists": assists,
            "assists_per_game": round(assists / gp, 1) if assists else 0,
            "turnovers": turnovers,
            "turnovers_per_game": round(turnovers / gp, 1) if turnovers else 0,
            "steals": steals,
            "steals_per_game": round(steals / gp, 1) if steals else 0,
            "blocks": blocks,
            "blocks_per_game": round(blocks / gp, 1) if blocks else 0,
            "personal_fouls": fouls,
            "fouls_per_game": round(fouls / gp, 1) if fouls else 0,
            "plus_minus": plus_minus,
            "plus_minus_per_game": round(plus_minus / gp, 1) if plus_minus else 0,
            "efficiency": self._calculate_efficiency(stats, gp),
            "true_shooting_pct": self._calculate_ts_pct(points_total, fga, fta),
            "effective_fg_pct": self._calculate_efg_pct(fgm, tpm, fga),
            "assist_turnover_ratio": round(assists / max(turnovers, 1), 2) if assists else 0,
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

        # Extract record
        games = stats.get("games", {}) if isinstance(stats.get("games"), dict) else {}
        wins = games.get("wins", {}) if isinstance(games.get("wins"), dict) else {}
        losses = games.get("losses", {}) if isinstance(games.get("losses"), dict) else {}

        total_wins = wins.get("all", {}).get("total", 0) or stats.get("wins", 0) or 0
        total_losses = losses.get("all", {}).get("total", 0) or stats.get("losses", 0) or 0
        games_played = total_wins + total_losses

        return {
            "team_id": team_id,
            "season_id": season_id,
            "games_played": games_played,
            "wins": total_wins,
            "losses": total_losses,
            "win_pct": self._safe_pct(total_wins, games_played),
            "home_wins": wins.get("home", {}).get("total", 0) or 0,
            "home_losses": losses.get("home", {}).get("total", 0) or 0,
            "away_wins": wins.get("away", {}).get("total", 0) or 0,
            "away_losses": losses.get("away", {}).get("total", 0) or 0,
            "points_per_game": stats.get("points", {}).get("for", {}).get("average", {}).get("all", 0) or 0,
            "opponent_ppg": stats.get("points", {}).get("against", {}).get("average", {}).get("all", 0) or 0,
            "updated_at": int(time.time()),
        }

    # =========================================================================
    # Database Operations
    # =========================================================================

    def upsert_player_stats(self, stats: dict[str, Any]) -> None:
        """Insert or update NBA player statistics."""
        self.db.execute(
            """
            INSERT INTO nba_player_stats (
                player_id, season_id, team_id,
                games_played, games_started, minutes_total, minutes_per_game,
                points_total, points_per_game,
                fgm, fga, fg_pct, tpm, tpa, tp_pct, ftm, fta, ft_pct,
                offensive_rebounds, defensive_rebounds, total_rebounds, rebounds_per_game,
                assists, assists_per_game, turnovers, turnovers_per_game,
                steals, steals_per_game, blocks, blocks_per_game,
                personal_fouls, fouls_per_game,
                plus_minus, plus_minus_per_game, efficiency,
                true_shooting_pct, effective_fg_pct, assist_turnover_ratio,
                updated_at
            )
            VALUES (
                :player_id, :season_id, :team_id,
                :games_played, :games_started, :minutes_total, :minutes_per_game,
                :points_total, :points_per_game,
                :fgm, :fga, :fg_pct, :tpm, :tpa, :tp_pct, :ftm, :fta, :ft_pct,
                :offensive_rebounds, :defensive_rebounds, :total_rebounds, :rebounds_per_game,
                :assists, :assists_per_game, :turnovers, :turnovers_per_game,
                :steals, :steals_per_game, :blocks, :blocks_per_game,
                :personal_fouls, :fouls_per_game,
                :plus_minus, :plus_minus_per_game, :efficiency,
                :true_shooting_pct, :effective_fg_pct, :assist_turnover_ratio,
                :updated_at
            )
            ON CONFLICT(player_id, season_id, team_id) DO UPDATE SET
                games_played = excluded.games_played,
                games_started = excluded.games_started,
                minutes_total = excluded.minutes_total,
                minutes_per_game = excluded.minutes_per_game,
                points_total = excluded.points_total,
                points_per_game = excluded.points_per_game,
                fgm = excluded.fgm,
                fga = excluded.fga,
                fg_pct = excluded.fg_pct,
                tpm = excluded.tpm,
                tpa = excluded.tpa,
                tp_pct = excluded.tp_pct,
                ftm = excluded.ftm,
                fta = excluded.fta,
                ft_pct = excluded.ft_pct,
                offensive_rebounds = excluded.offensive_rebounds,
                defensive_rebounds = excluded.defensive_rebounds,
                total_rebounds = excluded.total_rebounds,
                rebounds_per_game = excluded.rebounds_per_game,
                assists = excluded.assists,
                assists_per_game = excluded.assists_per_game,
                turnovers = excluded.turnovers,
                turnovers_per_game = excluded.turnovers_per_game,
                steals = excluded.steals,
                steals_per_game = excluded.steals_per_game,
                blocks = excluded.blocks,
                blocks_per_game = excluded.blocks_per_game,
                personal_fouls = excluded.personal_fouls,
                fouls_per_game = excluded.fouls_per_game,
                plus_minus = excluded.plus_minus,
                plus_minus_per_game = excluded.plus_minus_per_game,
                efficiency = excluded.efficiency,
                true_shooting_pct = excluded.true_shooting_pct,
                effective_fg_pct = excluded.effective_fg_pct,
                assist_turnover_ratio = excluded.assist_turnover_ratio,
                updated_at = excluded.updated_at
            """,
            stats,
        )

    def upsert_team_stats(self, stats: dict[str, Any]) -> None:
        """Insert or update NBA team statistics."""
        self.db.execute(
            """
            INSERT INTO nba_team_stats (
                team_id, season_id,
                games_played, wins, losses, win_pct,
                home_wins, home_losses, away_wins, away_losses,
                points_per_game, opponent_ppg,
                updated_at
            )
            VALUES (
                :team_id, :season_id,
                :games_played, :wins, :losses, :win_pct,
                :home_wins, :home_losses, :away_wins, :away_losses,
                :points_per_game, :opponent_ppg,
                :updated_at
            )
            ON CONFLICT(team_id, season_id) DO UPDATE SET
                games_played = excluded.games_played,
                wins = excluded.wins,
                losses = excluded.losses,
                win_pct = excluded.win_pct,
                home_wins = excluded.home_wins,
                home_losses = excluded.home_losses,
                away_wins = excluded.away_wins,
                away_losses = excluded.away_losses,
                points_per_game = excluded.points_per_game,
                opponent_ppg = excluded.opponent_ppg,
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
        guard_positions = {"PG", "SG", "G", "G-F"}
        forward_positions = {"SF", "PF", "F", "F-C", "F-G"}
        center_positions = {"C", "C-F"}

        if position in guard_positions:
            return "Guard"
        elif position in forward_positions:
            return "Forward"
        elif position in center_positions:
            return "Center"
        return None

    def _parse_height(self, player: dict) -> Optional[int]:
        """Parse height to centimeters."""
        height = player.get("height")
        if not height:
            return None

        if isinstance(height, dict):
            # Nested structure with meters/feets
            if "meters" in height and height["meters"]:
                try:
                    return int(float(height["meters"]) * 100)
                except (ValueError, TypeError):
                    pass
        elif isinstance(height, str):
            # String format like "6-8" or "2.03"
            if "-" in height:
                try:
                    feet, inches = map(int, height.split("-"))
                    return int((feet * 12 + inches) * 2.54)
                except (ValueError, TypeError):
                    pass
            elif "." in height:
                try:
                    return int(float(height) * 100)
                except (ValueError, TypeError):
                    pass

        return None

    def _parse_weight(self, player: dict) -> Optional[int]:
        """Parse weight to kilograms."""
        weight = player.get("weight")
        if not weight:
            return None

        if isinstance(weight, dict):
            if "kilograms" in weight and weight["kilograms"]:
                try:
                    return int(float(weight["kilograms"]))
                except (ValueError, TypeError):
                    pass
        elif isinstance(weight, (int, float)):
            return int(weight)
        elif isinstance(weight, str):
            try:
                # Assume pounds if just a number
                return int(float(weight) * 0.453592)
            except (ValueError, TypeError):
                pass

        return None

    def _parse_minutes_total(self, minutes: Any) -> int:
        """Parse minutes to integer total."""
        if isinstance(minutes, (int, float)):
            return int(minutes)
        if isinstance(minutes, str):
            try:
                return int(minutes)
            except ValueError:
                # Try parsing "MM:SS" format
                if ":" in minutes:
                    parts = minutes.split(":")
                    return int(parts[0]) * 60 + int(parts[1])
        return 0

    def _safe_pct(self, made: int, attempted: int) -> float:
        """Calculate percentage safely."""
        if not attempted:
            return 0.0
        return round((made / attempted) * 100, 1)

    def _calculate_efficiency(self, stats: dict, games: int) -> float:
        """Calculate NBA efficiency rating."""
        if games == 0:
            return 0.0

        points = stats.get("points_total", 0) or 0
        rebounds = stats.get("total_rebounds", 0) or 0
        assists = stats.get("assists", 0) or 0
        steals = stats.get("steals", 0) or 0
        blocks = stats.get("blocks", 0) or 0
        fga = stats.get("fga", 0) or 0
        fgm = stats.get("fgm", 0) or 0
        fta = stats.get("fta", 0) or 0
        ftm = stats.get("ftm", 0) or 0
        turnovers = stats.get("turnovers", 0) or 0

        eff = (points + rebounds + assists + steals + blocks -
               (fga - fgm) - (fta - ftm) - turnovers)
        return round(eff / games, 1)

    def _calculate_ts_pct(self, points: int, fga: int, fta: int) -> float:
        """Calculate true shooting percentage."""
        if not points or (not fga and not fta):
            return 0.0
        tsa = fga + (0.44 * fta)
        if tsa == 0:
            return 0.0
        return round((points / (2 * tsa)) * 100, 1)

    def _calculate_efg_pct(self, fgm: int, tpm: int, fga: int) -> float:
        """Calculate effective field goal percentage."""
        if not fga:
            return 0.0
        return round(((fgm + 0.5 * tpm) / fga) * 100, 1)
