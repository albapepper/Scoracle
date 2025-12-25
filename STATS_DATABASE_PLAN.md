# Scoracle Stats Database Plan

## Executive Summary

This document outlines the comprehensive plan for building a local SQLite database system to store current and historical season statistics from API-Sports. The system will enable interactive graphs, tables, and percentile-based comparisons while dramatically reducing API calls to the third-party service.

---

## Table of Contents

1. [Goals & Objectives](#1-goals--objectives)
2. [Architecture Overview](#2-architecture-overview)
3. [Database Schema Design](#3-database-schema-design)
4. [Sport-Specific Data Models](#4-sport-specific-data-models)
5. [Percentile Calculation System](#5-percentile-calculation-system)
6. [Data Seeding & Automation](#6-data-seeding--automation)
7. [API Integration](#7-api-integration)
8. [Extensibility Framework](#8-extensibility-framework)
9. [Implementation Phases](#9-implementation-phases)
10. [File Structure](#10-file-structure)

---

## 1. Goals & Objectives

### Primary Goals

1. **Local Data Storage**: Store comprehensive player and team statistics locally to minimize third-party API calls
2. **Percentile Analytics**: Enable percentile-based comparisons for visual statistical profiling
3. **Interactive Visualizations**: Support data for graphs, charts, and comparative tables
4. **Minimal API Usage**: Reduce API calls to a handful per week (batch updates only)
5. **Historical Data**: Maintain current season + previous season(s) for trend analysis

### Design Principles

- **Sport-Agnostic Core**: Central schema that works across all sports
- **Sport-Specific Extensions**: Dedicated tables for sport-unique statistics
- **Automation-First**: Built for automated updates via cron/scheduler
- **Extensibility**: Easy to add new sports without schema refactoring
- **Performance**: Optimized for read-heavy percentile calculations

---

## 2. Architecture Overview

### System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        SCORACLE STATS SYSTEM                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────────┐    ┌──────────────────┐    ┌───────────────┐  │
│  │   API-Sports     │───▶│  Seed Pipeline   │───▶│  Stats DB     │  │
│  │   (External)     │    │  (Weekly Cron)   │    │  (SQLite)     │  │
│  └──────────────────┘    └──────────────────┘    └───────┬───────┘  │
│                                                          │          │
│                          ┌───────────────────────────────┘          │
│                          ▼                                          │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    ANALYTICS LAYER                            │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐   │   │
│  │  │ Percentile  │  │ Aggregation │  │ Comparison Engine   │   │   │
│  │  │ Calculator  │  │ Service     │  │ (Player vs Player)  │   │   │
│  │  └─────────────┘  └─────────────┘  └─────────────────────┘   │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                          │                                          │
│                          ▼                                          │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    PRESENTATION LAYER                         │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐   │   │
│  │  │ Radar/Spider│  │ Bar Charts  │  │ Comparison Tables   │   │   │
│  │  │ Graphs      │  │ & Trends    │  │ & Rankings          │   │   │
│  │  └─────────────┘  └─────────────┘  └─────────────────────┘   │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Database Strategy

- **Primary Database**: `instance/statsdb/stats.sqlite` - Single unified database
- **Separate from Autocomplete**: Keeps existing `instance/localdb/*.sqlite` unchanged
- **Read-Only Production**: Database bundled with deployment, updates via CI/CD

---

## 3. Database Schema Design

### Core Tables (Sport-Agnostic)

```sql
-- Metadata table for tracking updates
CREATE TABLE meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at INTEGER NOT NULL
);

-- Sports registry
CREATE TABLE sports (
    id TEXT PRIMARY KEY,          -- 'NBA', 'NFL', 'FOOTBALL'
    display_name TEXT NOT NULL,
    api_base_url TEXT NOT NULL,
    current_season INTEGER NOT NULL,
    is_active INTEGER DEFAULT 1,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
);

-- Seasons registry
CREATE TABLE seasons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sport_id TEXT NOT NULL REFERENCES sports(id),
    season_year INTEGER NOT NULL,  -- e.g., 2024, 2025
    season_label TEXT,             -- e.g., "2024-25" for NBA
    is_current INTEGER DEFAULT 0,
    start_date TEXT,
    end_date TEXT,
    games_played INTEGER DEFAULT 0,
    UNIQUE(sport_id, season_year)
);

-- Leagues registry (for multi-league sports like Football)
CREATE TABLE leagues (
    id INTEGER PRIMARY KEY,        -- API-Sports league ID
    sport_id TEXT NOT NULL REFERENCES sports(id),
    name TEXT NOT NULL,
    country TEXT,
    logo_url TEXT,
    is_active INTEGER DEFAULT 1
);

-- Teams master table
CREATE TABLE teams (
    id INTEGER PRIMARY KEY,        -- API-Sports team ID
    sport_id TEXT NOT NULL REFERENCES sports(id),
    league_id INTEGER REFERENCES leagues(id),
    name TEXT NOT NULL,
    abbreviation TEXT,
    logo_url TEXT,
    conference TEXT,               -- For NBA/NFL
    division TEXT,                 -- For NBA/NFL
    country TEXT,                  -- For Football
    founded INTEGER,
    venue_name TEXT,
    venue_capacity INTEGER,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
);

-- Players master table
CREATE TABLE players (
    id INTEGER PRIMARY KEY,        -- API-Sports player ID
    sport_id TEXT NOT NULL REFERENCES sports(id),
    first_name TEXT,
    last_name TEXT,
    full_name TEXT NOT NULL,
    position TEXT,
    nationality TEXT,
    birth_date TEXT,
    height_cm INTEGER,
    weight_kg INTEGER,
    photo_url TEXT,
    current_team_id INTEGER REFERENCES teams(id),
    is_active INTEGER DEFAULT 1,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
);

-- Player-Team history (for trades/transfers)
CREATE TABLE player_teams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL REFERENCES players(id),
    team_id INTEGER NOT NULL REFERENCES teams(id),
    season_id INTEGER NOT NULL REFERENCES seasons(id),
    start_date TEXT,
    end_date TEXT,
    UNIQUE(player_id, team_id, season_id)
);
```

### Statistics Tables Architecture

Each sport has dedicated statistics tables that store raw stat values. Percentiles are calculated dynamically or cached.

```sql
-- Template for stat storage (actual tables are sport-specific)
-- See Section 4 for sport-specific implementations

-- Percentile cache (optional, for performance)
CREATE TABLE percentile_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT NOT NULL,     -- 'player' or 'team'
    entity_id INTEGER NOT NULL,
    sport_id TEXT NOT NULL,
    season_id INTEGER NOT NULL,
    stat_category TEXT NOT NULL,   -- e.g., 'points', 'assists'
    stat_value REAL NOT NULL,
    percentile REAL NOT NULL,      -- 0-100
    sample_size INTEGER NOT NULL,  -- Number of entities in calculation
    calculated_at INTEGER NOT NULL,
    UNIQUE(entity_type, entity_id, sport_id, season_id, stat_category)
);

-- Index for fast percentile lookups
CREATE INDEX idx_percentile_lookup
ON percentile_cache(entity_type, sport_id, season_id, stat_category);
```

---

## 4. Sport-Specific Data Models

### 4.1 NBA Statistics

#### Player Statistics Table

```sql
CREATE TABLE nba_player_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL REFERENCES players(id),
    season_id INTEGER NOT NULL REFERENCES seasons(id),
    team_id INTEGER REFERENCES teams(id),

    -- Games & Minutes
    games_played INTEGER DEFAULT 0,
    games_started INTEGER DEFAULT 0,
    minutes_total INTEGER DEFAULT 0,
    minutes_per_game REAL DEFAULT 0,

    -- Scoring
    points_total INTEGER DEFAULT 0,
    points_per_game REAL DEFAULT 0,

    -- Field Goals
    fgm INTEGER DEFAULT 0,         -- Field Goals Made
    fga INTEGER DEFAULT 0,         -- Field Goals Attempted
    fg_pct REAL DEFAULT 0,         -- Field Goal Percentage

    -- Three Pointers
    tpm INTEGER DEFAULT 0,         -- Three Pointers Made
    tpa INTEGER DEFAULT 0,         -- Three Pointers Attempted
    tp_pct REAL DEFAULT 0,         -- Three Point Percentage

    -- Free Throws
    ftm INTEGER DEFAULT 0,         -- Free Throws Made
    fta INTEGER DEFAULT 0,         -- Free Throws Attempted
    ft_pct REAL DEFAULT 0,         -- Free Throw Percentage

    -- Rebounds
    offensive_rebounds INTEGER DEFAULT 0,
    defensive_rebounds INTEGER DEFAULT 0,
    total_rebounds INTEGER DEFAULT 0,
    rebounds_per_game REAL DEFAULT 0,

    -- Assists & Turnovers
    assists INTEGER DEFAULT 0,
    assists_per_game REAL DEFAULT 0,
    turnovers INTEGER DEFAULT 0,
    turnovers_per_game REAL DEFAULT 0,

    -- Defense
    steals INTEGER DEFAULT 0,
    steals_per_game REAL DEFAULT 0,
    blocks INTEGER DEFAULT 0,
    blocks_per_game REAL DEFAULT 0,

    -- Fouls
    personal_fouls INTEGER DEFAULT 0,
    fouls_per_game REAL DEFAULT 0,

    -- Advanced (calculated)
    plus_minus INTEGER DEFAULT 0,
    efficiency REAL DEFAULT 0,
    true_shooting_pct REAL DEFAULT 0,

    updated_at INTEGER NOT NULL,
    UNIQUE(player_id, season_id, team_id)
);

CREATE INDEX idx_nba_player_stats_season ON nba_player_stats(season_id);
CREATE INDEX idx_nba_player_stats_team ON nba_player_stats(team_id);
```

#### Team Statistics Table

```sql
CREATE TABLE nba_team_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_id INTEGER NOT NULL REFERENCES teams(id),
    season_id INTEGER NOT NULL REFERENCES seasons(id),

    -- Record
    games_played INTEGER DEFAULT 0,
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    win_pct REAL DEFAULT 0,
    home_wins INTEGER DEFAULT 0,
    home_losses INTEGER DEFAULT 0,
    away_wins INTEGER DEFAULT 0,
    away_losses INTEGER DEFAULT 0,

    -- Scoring
    points_per_game REAL DEFAULT 0,
    opponent_ppg REAL DEFAULT 0,
    point_differential REAL DEFAULT 0,

    -- Shooting
    fg_pct REAL DEFAULT 0,
    tp_pct REAL DEFAULT 0,
    ft_pct REAL DEFAULT 0,

    -- Rebounds
    rebounds_per_game REAL DEFAULT 0,
    opponent_rpg REAL DEFAULT 0,

    -- Other
    assists_per_game REAL DEFAULT 0,
    steals_per_game REAL DEFAULT 0,
    blocks_per_game REAL DEFAULT 0,
    turnovers_per_game REAL DEFAULT 0,

    -- Rankings (within league)
    offensive_rating REAL DEFAULT 0,
    defensive_rating REAL DEFAULT 0,
    net_rating REAL DEFAULT 0,
    pace REAL DEFAULT 0,

    updated_at INTEGER NOT NULL,
    UNIQUE(team_id, season_id)
);
```

### 4.2 NFL Statistics

#### Player Statistics Tables

```sql
-- NFL stats are position-dependent, so we use separate tables

-- Passing stats (QB)
CREATE TABLE nfl_player_passing (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL REFERENCES players(id),
    season_id INTEGER NOT NULL REFERENCES seasons(id),
    team_id INTEGER REFERENCES teams(id),

    games_played INTEGER DEFAULT 0,
    games_started INTEGER DEFAULT 0,

    -- Passing
    pass_attempts INTEGER DEFAULT 0,
    pass_completions INTEGER DEFAULT 0,
    completion_pct REAL DEFAULT 0,
    pass_yards INTEGER DEFAULT 0,
    yards_per_attempt REAL DEFAULT 0,
    pass_touchdowns INTEGER DEFAULT 0,
    interceptions INTEGER DEFAULT 0,
    passer_rating REAL DEFAULT 0,
    sacks_taken INTEGER DEFAULT 0,
    sack_yards_lost INTEGER DEFAULT 0,
    longest_pass INTEGER DEFAULT 0,

    updated_at INTEGER NOT NULL,
    UNIQUE(player_id, season_id)
);

-- Rushing stats (RB, QB, WR)
CREATE TABLE nfl_player_rushing (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL REFERENCES players(id),
    season_id INTEGER NOT NULL REFERENCES seasons(id),
    team_id INTEGER REFERENCES teams(id),

    games_played INTEGER DEFAULT 0,

    rush_attempts INTEGER DEFAULT 0,
    rush_yards INTEGER DEFAULT 0,
    yards_per_carry REAL DEFAULT 0,
    rush_touchdowns INTEGER DEFAULT 0,
    longest_rush INTEGER DEFAULT 0,
    fumbles INTEGER DEFAULT 0,
    fumbles_lost INTEGER DEFAULT 0,

    updated_at INTEGER NOT NULL,
    UNIQUE(player_id, season_id)
);

-- Receiving stats (WR, TE, RB)
CREATE TABLE nfl_player_receiving (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL REFERENCES players(id),
    season_id INTEGER NOT NULL REFERENCES seasons(id),
    team_id INTEGER REFERENCES teams(id),

    games_played INTEGER DEFAULT 0,

    targets INTEGER DEFAULT 0,
    receptions INTEGER DEFAULT 0,
    catch_pct REAL DEFAULT 0,
    receiving_yards INTEGER DEFAULT 0,
    yards_per_reception REAL DEFAULT 0,
    receiving_touchdowns INTEGER DEFAULT 0,
    longest_reception INTEGER DEFAULT 0,
    yards_after_catch INTEGER DEFAULT 0,

    updated_at INTEGER NOT NULL,
    UNIQUE(player_id, season_id)
);

-- Defense stats (LB, DB, DL)
CREATE TABLE nfl_player_defense (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL REFERENCES players(id),
    season_id INTEGER NOT NULL REFERENCES seasons(id),
    team_id INTEGER REFERENCES teams(id),

    games_played INTEGER DEFAULT 0,

    tackles_total INTEGER DEFAULT 0,
    tackles_solo INTEGER DEFAULT 0,
    tackles_assist INTEGER DEFAULT 0,
    tackles_for_loss INTEGER DEFAULT 0,
    sacks REAL DEFAULT 0,
    sack_yards INTEGER DEFAULT 0,
    interceptions INTEGER DEFAULT 0,
    int_yards INTEGER DEFAULT 0,
    int_touchdowns INTEGER DEFAULT 0,
    passes_defended INTEGER DEFAULT 0,
    forced_fumbles INTEGER DEFAULT 0,
    fumble_recoveries INTEGER DEFAULT 0,

    updated_at INTEGER NOT NULL,
    UNIQUE(player_id, season_id)
);
```

#### Team Statistics Table

```sql
CREATE TABLE nfl_team_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_id INTEGER NOT NULL REFERENCES teams(id),
    season_id INTEGER NOT NULL REFERENCES seasons(id),

    -- Record
    games_played INTEGER DEFAULT 0,
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    ties INTEGER DEFAULT 0,
    win_pct REAL DEFAULT 0,

    -- Scoring
    points_for INTEGER DEFAULT 0,
    points_against INTEGER DEFAULT 0,
    point_differential INTEGER DEFAULT 0,

    -- Offense
    total_yards INTEGER DEFAULT 0,
    yards_per_game REAL DEFAULT 0,
    pass_yards INTEGER DEFAULT 0,
    rush_yards INTEGER DEFAULT 0,
    turnovers INTEGER DEFAULT 0,

    -- Defense
    yards_allowed INTEGER DEFAULT 0,
    pass_yards_allowed INTEGER DEFAULT 0,
    rush_yards_allowed INTEGER DEFAULT 0,
    takeaways INTEGER DEFAULT 0,
    sacks INTEGER DEFAULT 0,

    -- Special Teams
    field_goal_pct REAL DEFAULT 0,
    punt_avg REAL DEFAULT 0,

    updated_at INTEGER NOT NULL,
    UNIQUE(team_id, season_id)
);
```

### 4.3 Football (Soccer) Statistics

#### Player Statistics Table

```sql
CREATE TABLE football_player_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL REFERENCES players(id),
    season_id INTEGER NOT NULL REFERENCES seasons(id),
    team_id INTEGER REFERENCES teams(id),
    league_id INTEGER REFERENCES leagues(id),

    -- Appearances
    appearances INTEGER DEFAULT 0,
    starts INTEGER DEFAULT 0,
    minutes_played INTEGER DEFAULT 0,

    -- Goals & Assists
    goals INTEGER DEFAULT 0,
    assists INTEGER DEFAULT 0,

    -- Shots
    shots_total INTEGER DEFAULT 0,
    shots_on_target INTEGER DEFAULT 0,
    shot_accuracy REAL DEFAULT 0,

    -- Passing
    passes_total INTEGER DEFAULT 0,
    passes_accurate INTEGER DEFAULT 0,
    pass_accuracy REAL DEFAULT 0,
    key_passes INTEGER DEFAULT 0,

    -- Dribbling
    dribbles_attempted INTEGER DEFAULT 0,
    dribbles_successful INTEGER DEFAULT 0,
    dribble_success_rate REAL DEFAULT 0,

    -- Duels
    duels_total INTEGER DEFAULT 0,
    duels_won INTEGER DEFAULT 0,
    duel_success_rate REAL DEFAULT 0,

    -- Tackles & Interceptions
    tackles INTEGER DEFAULT 0,
    interceptions INTEGER DEFAULT 0,
    blocks INTEGER DEFAULT 0,

    -- Fouls & Cards
    fouls_committed INTEGER DEFAULT 0,
    fouls_drawn INTEGER DEFAULT 0,
    yellow_cards INTEGER DEFAULT 0,
    red_cards INTEGER DEFAULT 0,

    -- Goalkeeper specific
    saves INTEGER DEFAULT 0,
    goals_conceded INTEGER DEFAULT 0,
    clean_sheets INTEGER DEFAULT 0,
    penalty_saves INTEGER DEFAULT 0,

    updated_at INTEGER NOT NULL,
    UNIQUE(player_id, season_id, league_id)
);

CREATE INDEX idx_football_player_stats_league ON football_player_stats(league_id, season_id);
```

#### Team Statistics Table

```sql
CREATE TABLE football_team_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_id INTEGER NOT NULL REFERENCES teams(id),
    season_id INTEGER NOT NULL REFERENCES seasons(id),
    league_id INTEGER NOT NULL REFERENCES leagues(id),

    -- Record
    matches_played INTEGER DEFAULT 0,
    wins INTEGER DEFAULT 0,
    draws INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    points INTEGER DEFAULT 0,

    -- Goals
    goals_for INTEGER DEFAULT 0,
    goals_against INTEGER DEFAULT 0,
    goal_difference INTEGER DEFAULT 0,
    clean_sheets INTEGER DEFAULT 0,

    -- Form
    home_wins INTEGER DEFAULT 0,
    home_draws INTEGER DEFAULT 0,
    home_losses INTEGER DEFAULT 0,
    away_wins INTEGER DEFAULT 0,
    away_draws INTEGER DEFAULT 0,
    away_losses INTEGER DEFAULT 0,

    -- Attack
    shots_per_game REAL DEFAULT 0,
    shots_on_target_per_game REAL DEFAULT 0,

    -- Defense
    tackles_per_game REAL DEFAULT 0,
    interceptions_per_game REAL DEFAULT 0,

    -- Possession
    avg_possession REAL DEFAULT 0,

    -- Discipline
    yellow_cards INTEGER DEFAULT 0,
    red_cards INTEGER DEFAULT 0,

    -- Standings
    league_position INTEGER,

    updated_at INTEGER NOT NULL,
    UNIQUE(team_id, season_id, league_id)
);
```

---

## 5. Percentile Calculation System

### Calculation Methodology

Percentiles will be calculated using the **percentile rank formula**:

```
Percentile Rank = (Number of values below X / Total number of values) × 100
```

### Comparison Groups

Percentiles are meaningful only within appropriate comparison groups:

| Sport | Player Comparison Group | Team Comparison Group |
|-------|------------------------|----------------------|
| NBA | Same position, same season | All teams, same season |
| NFL | Same position, same season | All teams, same season |
| Football | Same position, same league, same season | Same league, same season |

### Implementation Approach

```python
# Percentile calculation pseudocode
def calculate_percentile(
    entity_id: int,
    entity_type: str,  # 'player' or 'team'
    stat_name: str,
    sport: str,
    season_id: int,
    position: str = None,  # For players
    league_id: int = None  # For Football
) -> dict:
    """
    Returns:
        {
            "stat_name": "points_per_game",
            "value": 28.5,
            "percentile": 95.2,
            "rank": 12,
            "total": 450,
            "comparison_group": "NBA Point Guards, 2024-25"
        }
    """
    # 1. Query all values for the stat within comparison group
    # 2. Sort values
    # 3. Find entity's rank
    # 4. Calculate percentile
    # 5. Cache result
```

### Stat Categories for Percentile Profiles

Each sport has key stat categories for creating visual profiles:

#### NBA Player Profile (8 axes for radar chart)
1. Scoring (PPG)
2. Efficiency (FG%)
3. Three-Point Shooting (3P%)
4. Rebounding (RPG)
5. Assists (APG)
6. Steals (SPG)
7. Blocks (BPG)
8. Plus/Minus

#### NFL QB Profile (6 axes)
1. Passing Yards
2. Touchdowns
3. Passer Rating
4. Completion %
5. Yards per Attempt
6. Interceptions (inverse)

#### Football Player Profile (8 axes)
1. Goals
2. Assists
3. Shot Accuracy
4. Pass Accuracy
5. Dribble Success
6. Tackles
7. Interceptions
8. Minutes Played

---

## 6. Data Seeding & Automation

### Seed Pipeline Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                     SEED PIPELINE                               │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. FETCH PHASE                                                │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐                  │
│  │  Teams   │    │ Players  │    │  Stats   │                  │
│  │ Fetcher  │    │ Fetcher  │    │ Fetcher  │                  │
│  └────┬─────┘    └────┬─────┘    └────┬─────┘                  │
│       │               │               │                         │
│       ▼               ▼               ▼                         │
│  2. TRANSFORM PHASE                                            │
│  ┌──────────────────────────────────────────────────────┐      │
│  │              Data Normalizer & Validator              │      │
│  │  - Standardize field names across sports             │      │
│  │  - Validate data types and ranges                    │      │
│  │  - Handle missing/null values                        │      │
│  └──────────────────────────────────────────────────────┘      │
│       │                                                         │
│       ▼                                                         │
│  3. LOAD PHASE                                                 │
│  ┌──────────────────────────────────────────────────────┐      │
│  │                  SQLite Upserter                      │      │
│  │  - Upsert teams/players/stats                        │      │
│  │  - Update percentile cache                           │      │
│  │  - Record sync metadata                              │      │
│  └──────────────────────────────────────────────────────┘      │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### Seed Script Structure

```
backend/app/statsdb/
├── __init__.py
├── connection.py          # Database connection manager
├── schema.py              # Schema creation/migration
├── models.py              # Pydantic models for validation
├── seeders/
│   ├── __init__.py
│   ├── base.py            # Base seeder class
│   ├── nba_seeder.py      # NBA-specific seeding logic
│   ├── nfl_seeder.py      # NFL-specific seeding logic
│   └── football_seeder.py # Football-specific seeding logic
├── percentiles/
│   ├── __init__.py
│   ├── calculator.py      # Percentile calculation logic
│   └── cache.py           # Percentile cache management
├── queries/
│   ├── __init__.py
│   ├── players.py         # Player stat queries
│   └── teams.py           # Team stat queries
└── cli.py                 # Command-line interface for seeding
```

### Automation Schedule

| Task | Frequency | Trigger |
|------|-----------|---------|
| Full stats refresh | Weekly (Sunday night) | Cron/GitHub Action |
| Incremental update | Daily (during season) | Cron/GitHub Action |
| Percentile recalculation | After each data update | Automatic |
| Schema migration | As needed | Manual/CI |

### CLI Commands

```bash
# Full database initialization
python -m backend.app.statsdb.cli init

# Seed specific sport
python -m backend.app.statsdb.cli seed --sport NBA --season 2025

# Seed all sports
python -m backend.app.statsdb.cli seed --all

# Update only new data (incremental)
python -m backend.app.statsdb.cli update --sport NBA

# Recalculate percentiles
python -m backend.app.statsdb.cli percentiles --sport NBA --season 2025

# Export to JSON (for frontend)
python -m backend.app.statsdb.cli export --format json --output ./exports/
```

---

## 7. API Integration

### New Backend Endpoints

```python
# New routes for stats database queries

GET /api/v1/stats/player/{player_id}/profile
    ?sport=NBA
    &season=2025
    Response: {
        "player": {...},
        "stats": {...},
        "percentiles": {
            "ppg": {"value": 28.5, "percentile": 95.2, "rank": 12},
            "rpg": {"value": 7.2, "percentile": 78.4, "rank": 89},
            ...
        },
        "comparison_group": "NBA Point Guards"
    }

GET /api/v1/stats/team/{team_id}/profile
    ?sport=NBA
    &season=2025
    Response: {
        "team": {...},
        "stats": {...},
        "percentiles": {...}
    }

GET /api/v1/stats/compare
    ?entities=player:123,player:456
    &sport=NBA
    &stats=ppg,rpg,apg
    Response: {
        "entities": [...],
        "comparison": [...]
    }

GET /api/v1/stats/rankings
    ?sport=NBA
    &stat=ppg
    &position=PG
    &limit=50
    Response: {
        "rankings": [
            {"rank": 1, "player": {...}, "value": 32.1, "percentile": 99.8},
            ...
        ]
    }

GET /api/v1/stats/percentile-distribution
    ?sport=NBA
    &stat=ppg
    &position=PG
    Response: {
        "stat": "ppg",
        "distribution": [
            {"percentile": 0, "value": 2.1},
            {"percentile": 10, "value": 5.4},
            ...
        ]
    }
```

### Integration with Existing Services

```python
# In backend/app/services/stats_service.py

class StatsService:
    def __init__(self, statsdb: StatsDB, apisports: ApiSportsService):
        self.statsdb = statsdb
        self.apisports = apisports  # Fallback if local data missing

    async def get_player_profile(
        self,
        player_id: int,
        sport: str,
        season: int
    ) -> PlayerProfile:
        # 1. Try local database first
        local_data = await self.statsdb.get_player_stats(player_id, sport, season)

        if local_data:
            # Calculate/retrieve percentiles
            percentiles = await self.statsdb.get_percentiles(
                entity_type='player',
                entity_id=player_id,
                sport=sport,
                season=season
            )
            return PlayerProfile(stats=local_data, percentiles=percentiles)

        # 2. Fallback to API (and optionally cache)
        api_data = await self.apisports.get_player_statistics(player_id, sport, season)
        return PlayerProfile(stats=api_data, percentiles=None)
```

---

## 8. Extensibility Framework

### Adding a New Sport

To add a new sport (e.g., NHL, MLB), follow these steps:

#### Step 1: Register the Sport

```python
# In backend/app/config.py, add to API_SPORTS_DEFAULTS
"NHL": SportDefaults(
    base_url="https://v1.hockey.api-sports.io",
    default_league=57,  # NHL
    default_season=2025,
)
```

#### Step 2: Create Sport-Specific Tables

```sql
-- Create migration file: migrations/003_add_nhl.sql

-- NHL Player Stats
CREATE TABLE nhl_player_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL REFERENCES players(id),
    season_id INTEGER NOT NULL REFERENCES seasons(id),
    team_id INTEGER REFERENCES teams(id),

    games_played INTEGER DEFAULT 0,
    goals INTEGER DEFAULT 0,
    assists INTEGER DEFAULT 0,
    points INTEGER DEFAULT 0,
    plus_minus INTEGER DEFAULT 0,
    penalty_minutes INTEGER DEFAULT 0,
    shots INTEGER DEFAULT 0,
    shot_pct REAL DEFAULT 0,
    -- ... more hockey-specific stats

    updated_at INTEGER NOT NULL,
    UNIQUE(player_id, season_id)
);
```

#### Step 3: Create Seeder

```python
# backend/app/statsdb/seeders/nhl_seeder.py

class NHLSeeder(BaseSeeder):
    sport_id = "NHL"

    def transform_player_stats(self, raw_data: dict) -> dict:
        """Transform API response to database schema"""
        return {
            "games_played": raw_data.get("games", {}).get("played", 0),
            "goals": raw_data.get("goals", {}).get("total", 0),
            # ... map all fields
        }
```

#### Step 4: Configure Percentile Categories

```python
# backend/app/statsdb/percentiles/config.py

PERCENTILE_CATEGORIES = {
    "NHL": {
        "player": [
            "goals", "assists", "points", "plus_minus",
            "shot_pct", "penalty_minutes", "time_on_ice"
        ],
        "team": [
            "goals_for", "goals_against", "win_pct",
            "power_play_pct", "penalty_kill_pct"
        ]
    }
}
```

### Configuration-Driven Design

```python
# Sport configurations are defined declaratively
SPORT_CONFIGS = {
    "NBA": {
        "player_positions": ["PG", "SG", "SF", "PF", "C"],
        "stat_tables": ["nba_player_stats"],
        "percentile_stats": ["ppg", "rpg", "apg", "spg", "bpg", "fg_pct", "tp_pct"],
        "team_divisions": True,
    },
    "NFL": {
        "player_positions": ["QB", "RB", "WR", "TE", "OL", "DL", "LB", "DB", "K", "P"],
        "stat_tables": ["nfl_player_passing", "nfl_player_rushing", "nfl_player_receiving", "nfl_player_defense"],
        "percentile_stats_by_position": {
            "QB": ["pass_yards", "pass_touchdowns", "passer_rating"],
            "RB": ["rush_yards", "rush_touchdowns", "yards_per_carry"],
            # ...
        }
    },
    # Easy to add new sports
}
```

---

## 9. Implementation Phases

### Phase 1: Foundation (Week 1)

- [ ] Create database directory structure
- [ ] Implement core schema (sports, seasons, teams, players)
- [ ] Create connection manager with read/write modes
- [ ] Build base seeder class
- [ ] Create CLI scaffolding

### Phase 2: NBA Implementation (Week 2)

- [ ] Implement NBA-specific schema
- [ ] Create NBA seeder with API-Sports integration
- [ ] Seed current + previous season data
- [ ] Test data integrity

### Phase 3: NFL Implementation (Week 3)

- [ ] Implement NFL position-specific schemas
- [ ] Create NFL seeder (handling multiple stat tables)
- [ ] Seed current + previous season data
- [ ] Test data integrity

### Phase 4: Football Implementation (Week 4)

- [ ] Implement Football schema (multi-league)
- [ ] Create Football seeder (handling 13+ leagues)
- [ ] Seed current + previous season data
- [ ] Test data integrity

### Phase 5: Percentile System (Week 5)

- [ ] Implement percentile calculator
- [ ] Create percentile cache system
- [ ] Build comparison group logic
- [ ] Create recalculation triggers

### Phase 6: API & Integration (Week 6)

- [ ] Create new stats endpoints
- [ ] Integrate with existing services
- [ ] Add caching layer
- [ ] Frontend integration preparation

### Phase 7: Automation (Week 7)

- [ ] Set up GitHub Actions for weekly sync
- [ ] Implement incremental update logic
- [ ] Add monitoring and alerting
- [ ] Documentation

---

## 10. File Structure

### Complete Directory Structure

```
Scoracle/
├── instance/
│   ├── localdb/                    # Existing autocomplete DBs
│   │   ├── nba.sqlite
│   │   ├── nfl.sqlite
│   │   └── football.sqlite
│   └── statsdb/                    # NEW: Stats database
│       └── stats.sqlite            # Unified stats database
│
├── backend/
│   └── app/
│       ├── database/               # Existing
│       │   ├── local_dbs.py
│       │   └── seed_local_dbs.py
│       │
│       └── statsdb/                # NEW: Stats database module
│           ├── __init__.py
│           ├── connection.py       # DB connection manager
│           ├── schema.py           # Schema definitions
│           ├── models.py           # Pydantic models
│           │
│           ├── seeders/
│           │   ├── __init__.py
│           │   ├── base.py         # Abstract base seeder
│           │   ├── nba_seeder.py
│           │   ├── nfl_seeder.py
│           │   └── football_seeder.py
│           │
│           ├── percentiles/
│           │   ├── __init__.py
│           │   ├── calculator.py   # Percentile math
│           │   ├── cache.py        # Cache management
│           │   └── config.py       # Stat categories config
│           │
│           ├── queries/
│           │   ├── __init__.py
│           │   ├── players.py      # Player queries
│           │   └── teams.py        # Team queries
│           │
│           ├── migrations/
│           │   ├── 001_initial.sql
│           │   ├── 002_nba_stats.sql
│           │   ├── 003_nfl_stats.sql
│           │   └── 004_football_stats.sql
│           │
│           └── cli.py              # Command-line interface
│
├── .github/
│   └── workflows/
│       └── sync-stats.yml          # NEW: Weekly sync action
│
└── STATS_DATABASE_PLAN.md          # This document
```

---

## API-Sports Endpoints Reference

### Endpoints to Use (URLs to be provided by user)

The following API-Sports endpoints will be used for data collection:

#### NBA
- `/players` - List all players
- `/players/statistics` - Player season statistics
- `/teams` - List all teams
- `/teams/statistics` - Team season statistics
- `/standings` - League standings

#### NFL
- `/players` - List all players
- `/players/{id}/statistics/{season}` - Player stats by season
- `/teams` - List all teams
- `/teams/statistics` - Team season statistics
- `/standings` - League standings

#### Football
- `/players` - List all players
- `/players/{id}/statistics/seasons` - Player stats by season
- `/teams` - List all teams
- `/teams/statistics` - Team statistics
- `/standings` - League standings

---

## Next Steps

1. **Review this plan** and provide feedback
2. **Provide API-Sports URLs** for each endpoint mentioned
3. **Confirm priority order** of sports implementation
4. **Discuss any additional requirements** for the percentile/visualization system

---

*Document Version: 1.0*
*Created: December 25, 2024*
*Author: Claude (AI Assistant)*
