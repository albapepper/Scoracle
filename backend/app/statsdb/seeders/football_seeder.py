"""
Football (Soccer) specific seeder for stats database.

Handles fetching and transforming Football player and team statistics
from the API-Sports Football API. Supports multiple leagues.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Optional

from .base import BaseSeeder

logger = logging.getLogger(__name__)


# Major leagues to seed
MAJOR_LEAGUES = [
    {"id": 39, "name": "Premier League", "country": "England"},
    {"id": 140, "name": "La Liga", "country": "Spain"},
    {"id": 135, "name": "Serie A", "country": "Italy"},
    {"id": 78, "name": "Bundesliga", "country": "Germany"},
    {"id": 61, "name": "Ligue 1", "country": "France"},
    {"id": 94, "name": "Primeira Liga", "country": "Portugal"},
    {"id": 88, "name": "Eredivisie", "country": "Netherlands"},
    {"id": 144, "name": "Belgian Pro League", "country": "Belgium"},
    {"id": 203, "name": "Super Lig", "country": "Turkey"},
    {"id": 235, "name": "Russian Premier League", "country": "Russia"},
    {"id": 2, "name": "Champions League", "country": "Europe"},
    {"id": 3, "name": "Europa League", "country": "Europe"},
    {"id": 848, "name": "Europa Conference League", "country": "Europe"},
]


class FootballSeeder(BaseSeeder):
    """Seeder for Football (Soccer) statistics."""

    sport_id = "FOOTBALL"

    def __init__(self, *args, leagues: Optional[list[dict]] = None, **kwargs):
        """
        Initialize the Football seeder.

        Args:
            leagues: List of leagues to seed. Defaults to MAJOR_LEAGUES.
        """
        super().__init__(*args, **kwargs)
        self.leagues = leagues or MAJOR_LEAGUES

    def _get_season_label(self, season_year: int) -> str:
        """Football seasons span two years (e.g., 2024-25)."""
        next_year = (season_year + 1) % 100
        return f"{season_year}-{next_year:02d}"

    # =========================================================================
    # League Management
    # =========================================================================

    def ensure_leagues(self) -> list[int]:
        """Ensure all configured leagues exist in the database."""
        league_ids = []

        for league in self.leagues:
            self.db.execute(
                """
                INSERT INTO leagues (id, sport_id, name, country, is_active)
                VALUES (?, ?, ?, ?, 1)
                ON CONFLICT(id) DO UPDATE SET
                    name = excluded.name,
                    country = excluded.country,
                    updated_at = ?
                """,
                (
                    league["id"],
                    self.sport_id,
                    league["name"],
                    league["country"],
                    int(time.time()),
                ),
            )
            league_ids.append(league["id"])

        return league_ids

    # =========================================================================
    # Data Fetching
    # =========================================================================

    async def fetch_teams(self, season: int) -> list[dict[str, Any]]:
        """Fetch Football teams from API-Sports for all leagues."""
        all_teams = []
        seen_ids = set()

        for league in self.leagues:
            league_id = league["id"]

            try:
                teams = await self.api.list_teams(
                    sport="FOOTBALL",
                    league=league_id,
                    season=season,
                )

                for team in teams:
                    team_id = team["id"]
                    if team_id in seen_ids:
                        continue

                    seen_ids.add(team_id)
                    all_teams.append({
                        "id": team_id,
                        "name": team["name"],
                        "abbreviation": team.get("code") or team.get("abbreviation"),
                        "logo_url": team.get("logo_url") or team.get("logo"),
                        "country": team.get("country") or league["country"],
                        "league_id": league_id,
                        "venue_name": team.get("venue", {}).get("name") if isinstance(team.get("venue"), dict) else None,
                        "venue_capacity": team.get("venue", {}).get("capacity") if isinstance(team.get("venue"), dict) else None,
                        "founded": team.get("founded"),
                    })

            except Exception as e:
                logger.warning("Failed to fetch teams for league %d: %s", league_id, e)

        return all_teams

    async def fetch_players(
        self,
        season: int,
        team_id: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        """Fetch Football players from API-Sports."""
        all_players = []
        seen_ids = set()

        # If specific team, just fetch that team
        if team_id:
            teams_to_fetch = [{"id": team_id}]
        else:
            # Fetch players from all seeded teams
            teams_to_fetch = self.db.fetchall(
                "SELECT id FROM teams WHERE sport_id = ?",
                (self.sport_id,),
            )

        for team in teams_to_fetch:
            tid = team["id"]
            page = 1

            while page <= 10:  # Limit pages per team
                try:
                    players = await self.api.list_players(
                        sport="FOOTBALL",
                        season=season,
                        page=page,
                    )

                    if not players:
                        break

                    for player in players:
                        player_id = player["id"]
                        if player_id in seen_ids:
                            continue

                        seen_ids.add(player_id)
                        team_data = player.get("team") or {}

                        all_players.append({
                            "id": player_id,
                            "first_name": player.get("first_name") or player.get("firstname"),
                            "last_name": player.get("last_name") or player.get("lastname"),
                            "full_name": self._build_full_name(player),
                            "position": player.get("position"),
                            "position_group": self._get_position_group(player.get("position")),
                            "nationality": player.get("nationality"),
                            "birth_date": player.get("birth_date") or player.get("birth", {}).get("date"),
                            "birth_place": player.get("birth", {}).get("place"),
                            "height_cm": self._parse_height(player),
                            "weight_kg": self._parse_weight(player),
                            "photo_url": player.get("photo_url") or player.get("photo"),
                            "current_team_id": team_data.get("id") if isinstance(team_data, dict) else None,
                            "jersey_number": player.get("number"),
                        })

                    page += 1

                except Exception as e:
                    logger.warning("Failed to fetch players for team %d page %d: %s", tid, page, e)
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
                sport="FOOTBALL",
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
                sport="FOOTBALL",
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
        stats = raw_stats if isinstance(raw_stats, dict) else {}

        if "response" in stats and stats["response"]:
            response = stats["response"]
            if isinstance(response, list) and response:
                # Get first response item
                player_data = response[0]
                # Stats are in statistics array
                statistics = player_data.get("statistics", [])
                if statistics:
                    stats = statistics[0]  # First league's stats

        # Get league ID from stats
        league = stats.get("league", {}) or {}
        league_id = league.get("id")

        # Games
        games = stats.get("games", {}) or {}
        appearances = games.get("appearences", 0) or games.get("appearances", 0) or 0
        starts = games.get("lineups", 0) or 0
        minutes = games.get("minutes", 0) or 0

        # Goals & Assists
        goals_data = stats.get("goals", {}) or {}
        goals = goals_data.get("total", 0) or 0
        assists = goals_data.get("assists", 0) or 0

        # Shots
        shots = stats.get("shots", {}) or {}
        shots_total = shots.get("total", 0) or 0
        shots_on = shots.get("on", 0) or 0

        # Passing
        passes = stats.get("passes", {}) or {}
        passes_total = passes.get("total", 0) or 0
        passes_acc = passes.get("accuracy", 0) or 0
        key_passes = passes.get("key", 0) or 0

        # Dribbles
        dribbles = stats.get("dribbles", {}) or {}
        dribbles_attempted = dribbles.get("attempts", 0) or 0
        dribbles_success = dribbles.get("success", 0) or 0

        # Duels
        duels = stats.get("duels", {}) or {}
        duels_total = duels.get("total", 0) or 0
        duels_won = duels.get("won", 0) or 0

        # Tackles
        tackles = stats.get("tackles", {}) or {}
        tackles_total = tackles.get("total", 0) or 0
        interceptions = tackles.get("interceptions", 0) or 0
        blocks = tackles.get("blocks", 0) or 0

        # Fouls
        fouls = stats.get("fouls", {}) or {}
        fouls_drawn = fouls.get("drawn", 0) or 0
        fouls_committed = fouls.get("committed", 0) or 0

        # Cards
        cards = stats.get("cards", {}) or {}
        yellows = cards.get("yellow", 0) or 0
        reds = cards.get("red", 0) or 0

        # Penalties
        penalty = stats.get("penalty", {}) or {}
        pen_won = penalty.get("won", 0) or 0
        pen_scored = penalty.get("scored", 0) or 0
        pen_missed = penalty.get("missed", 0) or 0

        # Goalkeeper stats
        gk = stats.get("goals", {}) or {}
        gk_conceded = gk.get("conceded", 0) or 0
        gk_saves = gk.get("saves", 0) or 0

        # Calculate per-90 stats
        minutes_played = max(minutes, 1)
        per_90_factor = 90 / minutes_played if minutes_played > 90 else 1

        return {
            "player_id": player_id,
            "season_id": season_id,
            "team_id": team_id,
            "league_id": league_id,
            "appearances": appearances,
            "starts": starts,
            "bench_appearances": max(0, appearances - starts),
            "minutes_played": minutes,
            "goals": goals,
            "assists": assists,
            "goals_assists": goals + assists,
            "goals_per_90": round(goals * per_90_factor, 2) if minutes >= 90 else 0,
            "assists_per_90": round(assists * per_90_factor, 2) if minutes >= 90 else 0,
            "shots_total": shots_total,
            "shots_on_target": shots_on,
            "shot_accuracy": self._safe_pct(shots_on, shots_total),
            "passes_total": passes_total,
            "passes_accurate": int(passes_total * (passes_acc / 100)) if passes_acc else 0,
            "pass_accuracy": passes_acc,
            "key_passes": key_passes,
            "dribbles_attempted": dribbles_attempted,
            "dribbles_successful": dribbles_success,
            "dribble_success_rate": self._safe_pct(dribbles_success, dribbles_attempted),
            "duels_total": duels_total,
            "duels_won": duels_won,
            "duel_success_rate": self._safe_pct(duels_won, duels_total),
            "tackles": tackles_total,
            "interceptions": interceptions,
            "blocks": blocks,
            "fouls_committed": fouls_committed,
            "fouls_drawn": fouls_drawn,
            "yellow_cards": yellows,
            "red_cards": reds,
            "penalties_won": pen_won,
            "penalties_scored": pen_scored,
            "penalties_missed": pen_missed,
            "saves": gk_saves,
            "goals_conceded": gk_conceded,
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
            stats = stats["response"]

        league = stats.get("league", {}) or {}
        league_id = league.get("id")

        # Fixtures
        fixtures = stats.get("fixtures", {}) or {}
        played = fixtures.get("played", {}) or {}
        wins = fixtures.get("wins", {}) or {}
        draws = fixtures.get("draws", {}) or {}
        losses = fixtures.get("losses", {}) or {}

        home_played = played.get("home", 0) or 0
        away_played = played.get("away", 0) or 0
        total_played = played.get("total", 0) or home_played + away_played

        # Goals
        goals = stats.get("goals", {}) or {}
        goals_for = goals.get("for", {}) or {}
        goals_against = goals.get("against", {}) or {}

        gf_total = goals_for.get("total", {}).get("total", 0) or 0
        ga_total = goals_against.get("total", {}).get("total", 0) or 0

        # Clean sheets & failed to score
        clean_sheets = stats.get("clean_sheet", {}) or {}
        failed_to_score = stats.get("failed_to_score", {}) or {}

        return {
            "team_id": team_id,
            "season_id": season_id,
            "league_id": league_id,
            "matches_played": total_played,
            "wins": wins.get("total", 0) or 0,
            "draws": draws.get("total", 0) or 0,
            "losses": losses.get("total", 0) or 0,
            "points": (wins.get("total", 0) or 0) * 3 + (draws.get("total", 0) or 0),
            "home_played": home_played,
            "home_wins": wins.get("home", 0) or 0,
            "home_draws": draws.get("home", 0) or 0,
            "home_losses": losses.get("home", 0) or 0,
            "home_goals_for": goals_for.get("total", {}).get("home", 0) or 0,
            "home_goals_against": goals_against.get("total", {}).get("home", 0) or 0,
            "away_played": away_played,
            "away_wins": wins.get("away", 0) or 0,
            "away_draws": draws.get("away", 0) or 0,
            "away_losses": losses.get("away", 0) or 0,
            "away_goals_for": goals_for.get("total", {}).get("away", 0) or 0,
            "away_goals_against": goals_against.get("total", {}).get("away", 0) or 0,
            "goals_for": gf_total,
            "goals_against": ga_total,
            "goal_difference": gf_total - ga_total,
            "goals_per_game": round(gf_total / max(total_played, 1), 2),
            "goals_conceded_per_game": round(ga_total / max(total_played, 1), 2),
            "clean_sheets": clean_sheets.get("total", 0) or 0,
            "failed_to_score": failed_to_score.get("total", 0) or 0,
            "form": stats.get("form", ""),
            "avg_possession": self._extract_avg_possession(stats),
            "updated_at": int(time.time()),
        }

    # =========================================================================
    # Database Operations
    # =========================================================================

    def upsert_player_stats(self, stats: dict[str, Any]) -> None:
        """Insert or update Football player statistics."""
        self.db.execute(
            """
            INSERT INTO football_player_stats (
                player_id, season_id, team_id, league_id,
                appearances, starts, bench_appearances, minutes_played,
                goals, assists, goals_assists, goals_per_90, assists_per_90,
                shots_total, shots_on_target, shot_accuracy,
                passes_total, passes_accurate, pass_accuracy, key_passes,
                dribbles_attempted, dribbles_successful, dribble_success_rate,
                duels_total, duels_won, duel_success_rate,
                tackles, interceptions, blocks,
                fouls_committed, fouls_drawn, yellow_cards, red_cards,
                penalties_won, penalties_scored, penalties_missed,
                saves, goals_conceded,
                updated_at
            )
            VALUES (
                :player_id, :season_id, :team_id, :league_id,
                :appearances, :starts, :bench_appearances, :minutes_played,
                :goals, :assists, :goals_assists, :goals_per_90, :assists_per_90,
                :shots_total, :shots_on_target, :shot_accuracy,
                :passes_total, :passes_accurate, :pass_accuracy, :key_passes,
                :dribbles_attempted, :dribbles_successful, :dribble_success_rate,
                :duels_total, :duels_won, :duel_success_rate,
                :tackles, :interceptions, :blocks,
                :fouls_committed, :fouls_drawn, :yellow_cards, :red_cards,
                :penalties_won, :penalties_scored, :penalties_missed,
                :saves, :goals_conceded,
                :updated_at
            )
            ON CONFLICT(player_id, season_id, league_id) DO UPDATE SET
                team_id = excluded.team_id,
                appearances = excluded.appearances,
                starts = excluded.starts,
                bench_appearances = excluded.bench_appearances,
                minutes_played = excluded.minutes_played,
                goals = excluded.goals,
                assists = excluded.assists,
                goals_assists = excluded.goals_assists,
                goals_per_90 = excluded.goals_per_90,
                assists_per_90 = excluded.assists_per_90,
                shots_total = excluded.shots_total,
                shots_on_target = excluded.shots_on_target,
                shot_accuracy = excluded.shot_accuracy,
                passes_total = excluded.passes_total,
                passes_accurate = excluded.passes_accurate,
                pass_accuracy = excluded.pass_accuracy,
                key_passes = excluded.key_passes,
                dribbles_attempted = excluded.dribbles_attempted,
                dribbles_successful = excluded.dribbles_successful,
                dribble_success_rate = excluded.dribble_success_rate,
                duels_total = excluded.duels_total,
                duels_won = excluded.duels_won,
                duel_success_rate = excluded.duel_success_rate,
                tackles = excluded.tackles,
                interceptions = excluded.interceptions,
                blocks = excluded.blocks,
                fouls_committed = excluded.fouls_committed,
                fouls_drawn = excluded.fouls_drawn,
                yellow_cards = excluded.yellow_cards,
                red_cards = excluded.red_cards,
                penalties_won = excluded.penalties_won,
                penalties_scored = excluded.penalties_scored,
                penalties_missed = excluded.penalties_missed,
                saves = excluded.saves,
                goals_conceded = excluded.goals_conceded,
                updated_at = excluded.updated_at
            """,
            stats,
        )

    def upsert_team_stats(self, stats: dict[str, Any]) -> None:
        """Insert or update Football team statistics."""
        self.db.execute(
            """
            INSERT INTO football_team_stats (
                team_id, season_id, league_id,
                matches_played, wins, draws, losses, points,
                home_played, home_wins, home_draws, home_losses,
                home_goals_for, home_goals_against,
                away_played, away_wins, away_draws, away_losses,
                away_goals_for, away_goals_against,
                goals_for, goals_against, goal_difference,
                goals_per_game, goals_conceded_per_game,
                clean_sheets, failed_to_score, form, avg_possession,
                updated_at
            )
            VALUES (
                :team_id, :season_id, :league_id,
                :matches_played, :wins, :draws, :losses, :points,
                :home_played, :home_wins, :home_draws, :home_losses,
                :home_goals_for, :home_goals_against,
                :away_played, :away_wins, :away_draws, :away_losses,
                :away_goals_for, :away_goals_against,
                :goals_for, :goals_against, :goal_difference,
                :goals_per_game, :goals_conceded_per_game,
                :clean_sheets, :failed_to_score, :form, :avg_possession,
                :updated_at
            )
            ON CONFLICT(team_id, season_id, league_id) DO UPDATE SET
                matches_played = excluded.matches_played,
                wins = excluded.wins,
                draws = excluded.draws,
                losses = excluded.losses,
                points = excluded.points,
                home_played = excluded.home_played,
                home_wins = excluded.home_wins,
                home_draws = excluded.home_draws,
                home_losses = excluded.home_losses,
                home_goals_for = excluded.home_goals_for,
                home_goals_against = excluded.home_goals_against,
                away_played = excluded.away_played,
                away_wins = excluded.away_wins,
                away_draws = excluded.away_draws,
                away_losses = excluded.away_losses,
                away_goals_for = excluded.away_goals_for,
                away_goals_against = excluded.away_goals_against,
                goals_for = excluded.goals_for,
                goals_against = excluded.goals_against,
                goal_difference = excluded.goal_difference,
                goals_per_game = excluded.goals_per_game,
                goals_conceded_per_game = excluded.goals_conceded_per_game,
                clean_sheets = excluded.clean_sheets,
                failed_to_score = excluded.failed_to_score,
                form = excluded.form,
                avg_possession = excluded.avg_possession,
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
        name = player.get("name") or f"{first} {last}".strip()
        return name or "Unknown"

    def _get_position_group(self, position: Optional[str]) -> Optional[str]:
        """Map position to position group."""
        if not position:
            return None

        position = position.lower()

        if "goalkeeper" in position or position == "gk":
            return "Goalkeeper"
        elif "defender" in position or position in ("cb", "lb", "rb", "wb"):
            return "Defender"
        elif "midfielder" in position or position in ("cm", "dm", "am", "lm", "rm"):
            return "Midfielder"
        elif "attacker" in position or "forward" in position or position in ("cf", "lw", "rw", "st"):
            return "Forward"

        return None

    def _parse_height(self, player: dict) -> Optional[int]:
        """Parse height to centimeters."""
        height = player.get("height")
        if not height:
            return None

        if isinstance(height, str):
            # Remove "cm" suffix if present
            height = height.replace("cm", "").replace(" ", "")
            try:
                return int(height)
            except ValueError:
                pass

        return None

    def _parse_weight(self, player: dict) -> Optional[int]:
        """Parse weight to kilograms."""
        weight = player.get("weight")
        if not weight:
            return None

        if isinstance(weight, str):
            # Remove "kg" suffix if present
            weight = weight.replace("kg", "").replace(" ", "")
            try:
                return int(weight)
            except ValueError:
                pass

        return None

    def _safe_pct(self, made: int, total: int) -> float:
        """Calculate percentage safely."""
        if not total:
            return 0.0
        return round((made / total) * 100, 1)

    def _extract_avg_possession(self, stats: dict) -> float:
        """Extract average possession from stats."""
        possession = stats.get("possession", {}) or {}
        if possession:
            # Can be structured as {"0-15": "52%", ...} or {"average": 52}
            avg = possession.get("average")
            if avg:
                if isinstance(avg, str):
                    return float(avg.replace("%", ""))
                return float(avg)

            # Calculate from all values
            values = []
            for key, val in possession.items():
                if isinstance(val, str) and "%" in val:
                    try:
                        values.append(float(val.replace("%", "")))
                    except ValueError:
                        pass

            if values:
                return round(sum(values) / len(values), 1)

        return 0.0

    async def seed_all(
        self,
        seasons: list[int],
        current_season: Optional[int] = None,
    ) -> dict[str, int]:
        """
        Seed all data for multiple seasons.

        Overrides base to ensure leagues are created first.
        """
        # Ensure leagues exist
        self.ensure_leagues()

        # Call parent implementation
        return await super().seed_all(seasons, current_season)
