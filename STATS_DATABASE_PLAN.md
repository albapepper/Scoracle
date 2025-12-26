# Scoracle Stats Database Plan

## Executive Summary

This document outlines the comprehensive plan for building a **unified local database** that serves as the single source of truth for all entity profiles and statistics. The system eliminates live API calls for user requests, enabling sub-10ms response times while reducing API-Sports usage to ~100 calls/week (batch updates only).

### Key Design Decisions

- **Local-first architecture**: All user requests served from SQLite, never live API
- **Tiered football coverage**: Full data for Top 5 European leagues + MLS; minimal data for others
- **NBA/NFL always full coverage**: Single league per sport, always complete data
- **Two-phase seeding**: Discovery (roster changes) → Profile fetch (new entities only)
- **Daily roster diffs**: Catch trades/transfers during season
- **Yearly profile refresh**: Photos only change annually
- **Percentiles from priority leagues only**: Meaningful comparisons against quality competition

---

## Table of Contents

1. [Goals & Objectives](#1-goals--objectives)
2. [Architecture Overview](#2-architecture-overview)
3. [Tiered Data Coverage](#3-tiered-data-coverage)
4. [Database Schema Design](#4-database-schema-design)
5. [Sport-Specific Data Models](#5-sport-specific-data-models)
6. [Two-Phase Seeding System](#6-two-phase-seeding-system)
7. [Percentile Calculation System](#7-percentile-calculation-system)
8. [Service Layer Architecture](#8-service-layer-architecture)
9. [API Integration](#9-api-integration)
10. [Implementation Phases](#10-implementation-phases)
11. [File Structure](#11-file-structure)

---

## 1. Goals & Objectives

### Primary Goals

1. **Unified Local Database**: Single SQLite database for ALL entity profiles AND statistics
2. **Zero Live API Calls**: User requests never trigger API-Sports calls; all data served locally
3. **Sub-10ms Response Times**: SQLite reads replace 300-500ms API calls
4. **~100 API Calls/Week**: Predictable, budgeted API usage via batch seeding only
5. **Real-Time News**: Eliminate news caching for always-fresh content
6. **Tiered Coverage**: Full data for priority leagues; minimal + fallback for others

### Design Principles

- **Local-First**: Database is the source of truth, not a cache
- **Two-Phase Seeding**: Discovery phase detects changes; Profile phase fetches only what's new
- **Smart Diffing**: Daily roster diffs catch trades/transfers without full re-seed
- **Priority-Based Percentiles**: Only calculate against quality competition (Top 5 + MLS)
- **Graceful Degradation**: Non-priority entities show "Building statistical profile" indicator

---

## 2. Architecture Overview

### System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     SCORACLE LOCAL-FIRST ARCHITECTURE                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  USER REQUESTS (Sub-10ms response)                                       │
│  ─────────────────────────────────                                       │
│  Frontend → EntityRepository → stats.sqlite → Response                   │
│                                    │                                     │
│                                    ├── Priority entity? → Full profile   │
│                                    └── Non-priority? → "Building..." UI  │
│                                                                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  BATCH SEEDING (2-3x/week, ~100 API calls)                              │
│  ─────────────────────────────────────────                              │
│                                                                          │
│  ┌─────────────┐    ┌─────────────────────────────────────────────────┐ │
│  │ API-Sports  │───▶│  TWO-PHASE SEEDING PIPELINE                     │ │
│  │ (External)  │    │                                                 │ │
│  └─────────────┘    │  Phase 1: DISCOVERY                             │ │
│                     │  ├── Fetch league rosters                       │ │
│                     │  ├── Compare against existing DB                │ │
│                     │  └── Identify NEW entities (no profile_fetched) │ │
│                     │                                                 │ │
│                     │  Phase 2: PROFILE FETCH                         │ │
│                     │  ├── Batch fetch profiles for NEW entities only │ │
│                     │  └── Skip entities with profile_fetched_at set  │ │
│                     │                                                 │ │
│                     │  Phase 3: STATS UPDATE                          │ │
│                     │  ├── Fetch current season stats                 │ │
│                     │  └── Recalculate percentiles                    │ │
│                     └─────────────────────────────────────────────────┘ │
│                                      │                                   │
│                                      ▼                                   │
│                            ┌─────────────────┐                          │
│                            │  stats.sqlite   │                          │
│                            │  (Unified DB)   │                          │
│                            └─────────────────┘                          │
│                                                                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  DAILY ROSTER DIFF (Priority leagues only, ~10 calls)                   │
│  ────────────────────────────────────────────────────                   │
│  ├── Fetch current rosters for priority leagues                         │
│  ├── Detect trades/transfers (player.current_team changed)              │
│  ├── Update player_teams history                                        │
│  └── Fetch profile for any genuinely NEW players                        │
│                                                                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  NEWS (Real-time, no caching)                                           │
│  ────────────────────────────                                           │
│  Frontend → Google News RSS → Response (60s TTL max)                    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Database Strategy

- **Unified Database**: `instance/statsdb/stats.sqlite` - Profiles + Stats + Percentiles
- **Replaces Live API**: EntityRepository reads locally, never calls API-Sports
- **Read-Only Production**: Database bundled with deployment, updates via CI/CD
- **Autocomplete Unchanged**: Existing `instance/localdb/*.sqlite` remains separate

---

## 3. Tiered Data Coverage

### Coverage Strategy by Sport

| Sport | Coverage Type | Leagues | Data Level |
|-------|---------------|---------|------------|
| **NFL** | Full | NFL (1 league) | All teams, players, stats, profiles |
| **NBA** | Full | NBA (1 league) | All teams, players, stats, profiles |
| **Football** | Tiered | See below | Priority vs Minimal |

### Football League Tiers

#### Priority Leagues (Full Local Data)

| League | API ID | Country | Why Priority |
|--------|--------|---------|--------------|
| Premier League | 39 | England | Top global viewership |
| La Liga | 140 | Spain | Top European league |
| Bundesliga | 78 | Germany | Top European league |
| Serie A | 135 | Italy | Top European league |
| Ligue 1 | 61 | France | Top European league |
| MLS | 253 | USA | Primary US market |

**Priority league entities receive:**
- Full profile data (logo, photo, venue, bio, height, weight, etc.)
- Complete season statistics
- Percentile calculations (compared within priority pool)
- Immediate widget rendering

#### Non-Priority Leagues (Minimal + Fallback)

All other football leagues receive:
- **Minimal local data**: `id`, `name`, `league_id`, `normalized_name`, `tokens`
- **No local stats**: Statistics fetched on-demand via live API
- **No percentile badges**: Insufficient local data for comparison
- **UI indicator**: "Building statistical profile" shown during render

### API Call Budget (~100 calls/week)

| Operation | Priority Leagues | Estimated Calls | Frequency |
|-----------|------------------|-----------------|-----------|
| Team rosters (NFL) | 1 league | 1 | 2x/week |
| Team rosters (NBA) | 1 league | 1 | 2x/week |
| Team rosters (Football) | 6 leagues | 6 | 2x/week |
| Player profiles (NEW only) | ~50 new/week | 50 | As discovered |
| Player stats (paginated) | All priority | 25 | 2x/week |
| Team stats | All priority | 10 | 2x/week |
| Daily roster diff | Priority only | 8 | Daily |
| **Total** | | **~100/week** | |

### Percentile Calculation Scope

Percentiles are ONLY calculated using priority league data:

```sql
-- Football percentile query filters to priority leagues
SELECT stat_value,
       PERCENT_RANK() OVER (ORDER BY stat_value) as percentile
FROM football_player_stats fps
JOIN players p ON fps.player_id = p.id
JOIN leagues l ON p.current_league_id = l.id
WHERE l.priority_tier = 1  -- Top 5 European + MLS only
  AND fps.stat_category = ?;
```

This ensures percentiles reflect meaningful comparisons against quality competition.

---

## 4. Database Schema Design

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
    priority_tier INTEGER DEFAULT 0,  -- 1 = priority (full data), 0 = minimal
    is_active INTEGER DEFAULT 1
);

-- Priority tier values:
--   1 = Priority league (Top 5 European + MLS for Football)
--       Full profiles, stats, percentiles
--   0 = Non-priority league
--       Minimal data, live API fallback, no percentiles

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
    city TEXT,
    founded INTEGER,
    venue_name TEXT,
    venue_city TEXT,
    venue_capacity INTEGER,
    venue_surface TEXT,
    venue_image TEXT,
    -- Profile tracking
    profile_fetched_at INTEGER,    -- NULL = needs fetch, timestamp = fetched
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
);

-- Profile refresh strategy:
--   profile_fetched_at = NULL → Entity discovered, needs profile fetch
--   profile_fetched_at > 1 year ago → Consider refresh (photos may change)
--   profile_fetched_at recent → Skip fetch, use cached profile

-- Players master table
CREATE TABLE players (
    id INTEGER PRIMARY KEY,        -- API-Sports player ID
    sport_id TEXT NOT NULL REFERENCES sports(id),
    first_name TEXT,
    last_name TEXT,
    full_name TEXT NOT NULL,
    position TEXT,
    position_group TEXT,           -- For NFL: 'offense', 'defense', 'special'
    jersey_number INTEGER,
    nationality TEXT,
    birth_date TEXT,
    birth_place TEXT,
    height_cm INTEGER,
    weight_kg INTEGER,
    photo_url TEXT,
    current_team_id INTEGER REFERENCES teams(id),
    current_league_id INTEGER REFERENCES leagues(id),
    is_active INTEGER DEFAULT 1,
    -- Profile tracking
    profile_fetched_at INTEGER,    -- NULL = needs fetch, timestamp = fetched
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
);

-- Index for finding entities needing profile fetch
CREATE INDEX idx_teams_needs_profile ON teams(profile_fetched_at) WHERE profile_fetched_at IS NULL;
CREATE INDEX idx_players_needs_profile ON players(profile_fetched_at) WHERE profile_fetched_at IS NULL;
CREATE INDEX idx_players_current_league ON players(current_league_id);

-- Player-Team history (for trades/transfers)
CREATE TABLE player_teams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL REFERENCES players(id),
    team_id INTEGER NOT NULL REFERENCES teams(id),
    season_id INTEGER NOT NULL REFERENCES seasons(id),
    start_date TEXT,
    end_date TEXT,
    detected_at INTEGER NOT NULL,  -- When we detected this assignment
    UNIQUE(player_id, team_id, season_id)
);

-- Minimal entities table (for non-priority league autocomplete)
CREATE TABLE entities_minimal (
    id INTEGER PRIMARY KEY,
    entity_type TEXT NOT NULL,     -- 'team' or 'player'
    sport_id TEXT NOT NULL,
    league_id INTEGER,
    name TEXT NOT NULL,
    normalized_name TEXT,          -- Lowercase, accent-stripped
    tokens TEXT,                   -- Space-separated search tokens
    created_at INTEGER NOT NULL
);

CREATE INDEX idx_entities_minimal_type ON entities_minimal(entity_type, sport_id);
CREATE INDEX idx_entities_minimal_search ON entities_minimal(normalized_name);
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

## 5. Sport-Specific Data Models

### 5.1 NBA Statistics

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

### 5.2 NFL Statistics

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

### 5.3 Football (Soccer) Statistics

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

## 7. Percentile Calculation System

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

## 6. Two-Phase Seeding System

### Overview

The seeding system minimizes API calls by:
1. **Discovery Phase**: Fetch rosters, detect what's new/changed
2. **Profile Phase**: Only fetch profiles for genuinely new entities
3. **Stats Phase**: Update statistics for all priority entities
4. **Daily Diff**: Lightweight roster check for trades/transfers

### Two-Phase Seeding Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     TWO-PHASE SEEDING PIPELINE                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  PHASE 1: DISCOVERY (Minimal API calls)                                 │
│  ════════════════════════════════════════                               │
│                                                                          │
│  ┌──────────────────┐                                                   │
│  │ Fetch Rosters    │──▶ GET /teams?league={id} (1 call per league)    │
│  │ (Teams + Players)│    GET /players?team={id} (paginated)            │
│  └────────┬─────────┘                                                   │
│           │                                                              │
│           ▼                                                              │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    ENTITY DIFF ENGINE                             │   │
│  │                                                                   │   │
│  │  For each entity in API response:                                │   │
│  │    ├── EXISTS in DB with profile_fetched_at? → Skip profile      │   │
│  │    ├── EXISTS but profile_fetched_at NULL?   → Queue for fetch   │   │
│  │    └── NEW entity not in DB?                 → Insert + Queue    │   │
│  │                                                                   │   │
│  │  Additionally for players:                                        │   │
│  │    └── current_team changed? → Update player_teams history       │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│           │                                                              │
│           ▼                                                              │
│  Output: List of entity IDs needing profile fetch                       │
│                                                                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  PHASE 2: PROFILE FETCH (Only for new entities)                         │
│  ═══════════════════════════════════════════════                        │
│                                                                          │
│  ┌──────────────────┐                                                   │
│  │ Profile Fetcher  │──▶ GET /teams?id={id}   (full profile)           │
│  │ (Batch by queue) │    GET /players?id={id} (full profile)           │
│  └────────┬─────────┘                                                   │
│           │                                                              │
│           ▼                                                              │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  Profile fields populated:                                        │   │
│  │  - Teams: logo, venue_*, founded, city                           │   │
│  │  - Players: photo, height, weight, birth_date, nationality       │   │
│  │                                                                   │   │
│  │  SET profile_fetched_at = NOW()                                  │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  PHASE 3: STATS UPDATE (All priority entities)                          │
│  ══════════════════════════════════════════════                         │
│                                                                          │
│  ┌──────────────────┐                                                   │
│  │ Stats Fetcher    │──▶ GET /players/statistics?id={id}&season=...    │
│  │ (Paginated)      │    GET /teams/statistics?id={id}&season=...      │
│  └────────┬─────────┘                                                   │
│           │                                                              │
│           ▼                                                              │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  Upsert into sport-specific stats tables                         │   │
│  │  Recalculate percentile_cache (priority leagues only)            │   │
│  │  Update sync_log with completion status                          │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Daily Roster Diff (Trades/Transfers)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     DAILY ROSTER DIFF                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Runs: Daily during season (priority leagues only)                      │
│  Cost: ~8-10 API calls (1 per priority league)                          │
│                                                                          │
│  ┌──────────────────┐                                                   │
│  │ For each league: │                                                   │
│  │ GET /players     │──▶ Fetch current rosters (team assignments)      │
│  │ ?team={id}       │                                                   │
│  └────────┬─────────┘                                                   │
│           │                                                              │
│           ▼                                                              │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  Compare current_team_id vs API response:                         │   │
│  │                                                                   │   │
│  │  ├── Same team?     → No action                                  │   │
│  │  ├── Different team? → Trade detected:                           │   │
│  │  │   └── Close old player_teams record (set end_date)           │   │
│  │  │   └── Create new player_teams record                         │   │
│  │  │   └── Update player.current_team_id                          │   │
│  │  └── New player?    → Insert player, queue profile fetch         │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Profile Refresh Strategy

```python
# Profiles are fetched ONCE and rarely refreshed
# Photos are the main thing that changes (yearly at most)

def needs_profile_fetch(entity) -> bool:
    if entity.profile_fetched_at is None:
        return True  # Never fetched

    age = now() - entity.profile_fetched_at
    if age > timedelta(days=365):
        return True  # Annual refresh for photos

    return False  # Use cached profile
```

### Seeding Script Structure

```
backend/app/statsdb/
├── __init__.py
├── connection.py          # Database connection manager
├── schema.py              # Schema creation/migration
├── models.py              # Pydantic models for validation
├── seeders/
│   ├── __init__.py
│   ├── base.py            # Base seeder with two-phase logic
│   ├── diff_engine.py     # Entity comparison + queue building
│   ├── profile_fetcher.py # Batch profile fetching
│   ├── nba_seeder.py      # NBA-specific transformations
│   ├── nfl_seeder.py      # NFL-specific transformations
│   └── football_seeder.py # Football-specific (priority tier aware)
├── percentiles/
│   ├── __init__.py
│   ├── calculator.py      # Percentile calculation logic
│   └── cache.py           # Percentile cache management
├── roster_diff/
│   ├── __init__.py
│   └── daily_diff.py      # Daily trade/transfer detection
├── queries/
│   ├── __init__.py
│   ├── players.py         # Player stat queries
│   └── teams.py           # Team stat queries
└── cli.py                 # Command-line interface
```

### Automation Schedule

| Task | Frequency | Trigger | API Calls |
|------|-----------|---------|-----------|
| Full seed (all sports) | Weekly (Sunday) | Cron/GitHub Action | ~50 |
| Stats update only | Mid-week (Wed) | Cron/GitHub Action | ~30 |
| Daily roster diff | Daily (in-season) | Cron/GitHub Action | ~8 |
| Yearly profile refresh | Annually (preseason) | Manual | ~100 |
| Percentile recalc | After each update | Automatic | 0 (local) |

### In-Season Detection

```python
# Sports have different in-season periods
SEASON_WINDOWS = {
    "NFL": {"start_month": 9, "end_month": 2},   # Sep - Feb
    "NBA": {"start_month": 10, "end_month": 6},  # Oct - Jun
    "FOOTBALL": {"start_month": 8, "end_month": 5},  # Aug - May
}

def is_in_season(sport: str) -> bool:
    """Determine if we should run daily diffs for this sport."""
    window = SEASON_WINDOWS.get(sport)
    current_month = datetime.now().month

    if window["start_month"] > window["end_month"]:
        # Season spans year boundary (e.g., NFL Sep-Feb)
        return current_month >= window["start_month"] or current_month <= window["end_month"]
    else:
        return window["start_month"] <= current_month <= window["end_month"]
```

### CLI Commands

```bash
# Full database initialization
python -m backend.app.statsdb.cli init

# Two-phase seed for specific sport (discovery → profile → stats)
python -m backend.app.statsdb.cli seed --sport NBA --season 2025

# Seed all priority leagues
python -m backend.app.statsdb.cli seed --all --priority-only

# Stats update only (skip profile phase)
python -m backend.app.statsdb.cli update-stats --sport NFL

# Daily roster diff
python -m backend.app.statsdb.cli roster-diff --sport NBA

# Force profile refresh (annual)
python -m backend.app.statsdb.cli refresh-profiles --sport FOOTBALL --force

# Recalculate percentiles (local, no API)
python -m backend.app.statsdb.cli percentiles --sport NBA --season 2025

# Show seeding status
python -m backend.app.statsdb.cli status
# Output: Last sync times, entities needing profiles, in-season status
```

---

## 8. Service Layer Architecture

### Overview

The service layer is redesigned for local-first data access. User requests never trigger API calls.

### EntityRepository (New Core Service)

```python
# backend/app/services/entity_repository.py

class EntityRepository:
    """
    Single source of truth for entity data.
    Reads from local SQLite, never calls API-Sports.
    """

    def __init__(self, statsdb: StatsDB):
        self.db = statsdb

    async def get_player(self, player_id: int, sport: str) -> PlayerProfile | None:
        """Fetch player profile + stats from local DB."""
        player = await self.db.query_one(
            "SELECT * FROM players WHERE id = ? AND sport_id = ?",
            (player_id, sport)
        )
        if not player:
            return None

        # Check if this is a priority league entity
        is_priority = await self._is_priority_entity(player_id, "player", sport)

        if is_priority:
            stats = await self._get_player_stats(player_id, sport)
            percentiles = await self._get_percentiles(player_id, "player", sport)
            return PlayerProfile(
                player=player,
                stats=stats,
                percentiles=percentiles,
                status="complete"
            )
        else:
            # Non-priority: minimal data, indicate building status
            return PlayerProfile(
                player=player,
                stats=None,
                percentiles=None,
                status="building"  # UI shows "Building statistical profile"
            )

    async def get_team(self, team_id: int, sport: str) -> TeamProfile | None:
        """Fetch team profile + stats from local DB."""
        # Similar pattern to get_player
        ...

    async def _is_priority_entity(
        self, entity_id: int, entity_type: str, sport: str
    ) -> bool:
        """Check if entity belongs to a priority league."""
        if sport in ("NBA", "NFL"):
            return True  # Always full coverage

        # For Football, check league priority tier
        if entity_type == "player":
            result = await self.db.query_one("""
                SELECT l.priority_tier
                FROM players p
                JOIN leagues l ON p.current_league_id = l.id
                WHERE p.id = ?
            """, (entity_id,))
        else:
            result = await self.db.query_one("""
                SELECT l.priority_tier
                FROM teams t
                JOIN leagues l ON t.league_id = l.id
                WHERE t.id = ?
            """, (entity_id,))

        return result and result["priority_tier"] == 1
```

### Removing Live API Caching

**Before (complex caching for live API):**
```
widget_service → singleflight → cache → API-Sports
                     ↓
              3 cache tiers (basic, stats, widget)
              TTLs from 2 min to 30 days
```

**After (simple local reads):**
```
EntityRepository → SQLite (5-10ms reads)
                     ↓
              No caching needed (DB is the cache)
```

**Components to remove/simplify:**
- `singleflight.py` - No longer needed (no thundering herd risk)
- `cache.py` - Dramatically simplified or removed
- `widget_cache`, `stats_cache`, `basic_cache` - Remove

### Non-Priority Entity Fallback

For non-priority football league entities, we still need to serve some data:

```python
class NonPriorityFallbackService:
    """
    Handles requests for entities outside priority leagues.
    Uses live API with caching as fallback.
    """

    def __init__(self, apisports: ApiSportsService, cache: TTLCache):
        self.api = apisports
        self.cache = cache  # Simple 6-hour cache

    async def get_stats(self, entity_id: int, entity_type: str, sport: str):
        cache_key = f"fallback:{sport}:{entity_type}:{entity_id}"

        # Check cache first
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        # Live API call (only for non-priority)
        stats = await self.api.get_statistics(entity_id, entity_type, sport)

        # Cache for 6 hours
        self.cache.set(cache_key, stats, ttl=21600)

        return stats
```

### News Service (Real-Time)

```python
# backend/app/services/news_service.py

class NewsService:
    """
    Real-time news with minimal caching.
    Google News RSS is fast, so we prioritize freshness.
    """

    # Reduced TTL: 60 seconds max (was 10 minutes)
    CACHE_TTL = 60

    async def get_news(self, entity_name: str, sport: str, hours: int = 48):
        cache_key = f"news:{sport}:{entity_name}:{hours}"

        # Very short cache check
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        # Fetch fresh from Google News RSS
        articles = await self._fetch_google_news(entity_name, sport, hours)

        # Short TTL for freshness
        self.cache.set(cache_key, articles, ttl=self.CACHE_TTL)

        return articles
```

### Request Flow Summary

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        REQUEST ROUTING                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  GET /api/v1/widget/player/{id}?sport=NFL                               │
│      │                                                                   │
│      ▼                                                                   │
│  EntityRepository.get_player(id, "NFL")                                 │
│      │                                                                   │
│      ├── NFL → Always priority → Full local data                        │
│      │                                                                   │
│      └── Return PlayerProfile(status="complete")                        │
│                                                                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  GET /api/v1/widget/player/{id}?sport=FOOTBALL                          │
│      │                                                                   │
│      ▼                                                                   │
│  EntityRepository.get_player(id, "FOOTBALL")                            │
│      │                                                                   │
│      ├── Check league.priority_tier                                     │
│      │   ├── priority_tier = 1 → Full local data                       │
│      │   └── priority_tier = 0 → Minimal data + "building" status      │
│      │                                                                   │
│      └── If "building" → Frontend shows indicator, may call fallback   │
│                                                                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  GET /api/v1/news/{entity_name}?sport=NBA                               │
│      │                                                                   │
│      ▼                                                                   │
│  NewsService.get_news(entity_name, "NBA")                               │
│      │                                                                   │
│      └── 60-second cache → Google News RSS → Fresh results              │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 9. API Integration

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

## Appendix A: Extensibility Framework

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

## 10. Implementation Phases

### Phase 1: Schema & Foundation

- [ ] Update database schema with new fields (`profile_fetched_at`, `priority_tier`, etc.)
- [ ] Create `entities_minimal` table for non-priority entities
- [ ] Add indexes for profile fetch tracking
- [ ] Create migration scripts
- [ ] Update connection manager

### Phase 2: Two-Phase Seeding Infrastructure

- [ ] Create `diff_engine.py` for entity comparison
- [ ] Create `profile_fetcher.py` for batch profile fetching
- [ ] Update base seeder with two-phase logic
- [ ] Add `needs_profile_fetch()` logic
- [ ] Implement profile queue system

### Phase 3: Sport Seeders (Priority Coverage)

- [ ] Update NBA seeder (full coverage, always priority)
- [ ] Update NFL seeder (full coverage, always priority)
- [ ] Update Football seeder with priority tier awareness
- [ ] Configure priority leagues (Top 5 European + MLS)
- [ ] Implement minimal entity seeding for non-priority leagues

### Phase 4: Daily Roster Diff

- [ ] Create `roster_diff/daily_diff.py`
- [ ] Implement trade/transfer detection
- [ ] Add `player_teams` history tracking
- [ ] Create in-season detection logic
- [ ] Set up daily cron trigger (priority leagues only)

### Phase 5: EntityRepository Service

- [ ] Create `entity_repository.py`
- [ ] Implement `get_player()` with priority tier check
- [ ] Implement `get_team()` with priority tier check
- [ ] Add "building" status for non-priority entities
- [ ] Remove/simplify `singleflight.py`, cache layers

### Phase 6: Non-Priority Fallback

- [ ] Create `NonPriorityFallbackService`
- [ ] Implement 6-hour cache for live API fallback
- [ ] Add frontend "Building statistical profile" indicator
- [ ] Test fallback flow for non-priority entities

### Phase 7: News Service Optimization

- [ ] Reduce news cache TTL to 60 seconds
- [ ] Remove or simplify news caching layer
- [ ] Test real-time news delivery

### Phase 8: Percentile System

- [ ] Update percentile calculator to filter by priority leagues only
- [ ] Add `priority_tier` filter to all percentile queries
- [ ] Recalculate percentile cache after seeding
- [ ] Test percentile accuracy

### Phase 9: API & Frontend Integration

- [ ] Update widget endpoints to use EntityRepository
- [ ] Add `status` field to API responses ("complete" | "building")
- [ ] Update frontend to handle "building" status
- [ ] Remove unused caching endpoints

### Phase 10: Automation & Monitoring

- [ ] Set up GitHub Actions for weekly seed
- [ ] Set up GitHub Actions for daily roster diff
- [ ] Add in-season detection to skip off-season diffs
- [ ] Implement seeding status dashboard
- [ ] Add error alerting for failed syncs

---

## 11. File Structure

### Complete Directory Structure

```
Scoracle/
├── instance/
│   ├── localdb/                    # Existing autocomplete DBs (unchanged)
│   │   ├── nba.sqlite
│   │   ├── nfl.sqlite
│   │   └── football.sqlite
│   └── statsdb/                    # Unified entity + stats database
│       └── stats.sqlite            # Single source of truth
│
├── backend/
│   └── app/
│       ├── services/
│       │   ├── entity_repository.py   # NEW: Local-first data access
│       │   ├── news_service.py        # UPDATED: 60-second cache
│       │   ├── fallback_service.py    # NEW: Non-priority API fallback
│       │   ├── apisports.py           # UPDATED: Seeder-only, not user-facing
│       │   ├── cache.py               # SIMPLIFIED: Minimal caching
│       │   └── singleflight.py        # DEPRECATED: No longer needed
│       │
│       ├── database/               # Existing
│       │   ├── local_dbs.py
│       │   └── seed_local_dbs.py
│       │
│       └── statsdb/
│           ├── __init__.py
│           ├── connection.py       # DB connection manager
│           ├── schema.py           # Schema definitions + migrations
│           ├── models.py           # Pydantic models
│           │
│           ├── seeders/
│           │   ├── __init__.py
│           │   ├── base.py         # Two-phase seeding base class
│           │   ├── diff_engine.py  # NEW: Entity comparison + queue
│           │   ├── profile_fetcher.py # NEW: Batch profile fetching
│           │   ├── nba_seeder.py   # NBA (always priority)
│           │   ├── nfl_seeder.py   # NFL (always priority)
│           │   └── football_seeder.py # Football (priority-tier aware)
│           │
│           ├── roster_diff/        # NEW: Trade/transfer detection
│           │   ├── __init__.py
│           │   └── daily_diff.py   # Daily roster comparison
│           │
│           ├── percentiles/
│           │   ├── __init__.py
│           │   ├── calculator.py   # Priority-league-only percentiles
│           │   ├── cache.py        # Cache management
│           │   └── config.py       # Stat categories by sport
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
│           │   ├── 004_football_stats.sql
│           │   └── 005_profile_tracking.sql  # NEW: profile_fetched_at, priority_tier
│           │
│           └── cli.py              # Command-line interface
│
├── .github/
│   └── workflows/
│       ├── sync-stats-weekly.yml   # Weekly full seed (Sun)
│       ├── sync-stats-midweek.yml  # Mid-week stats update (Wed)
│       └── roster-diff-daily.yml   # Daily roster diff (in-season only)
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

1. **Review this plan** and provide feedback on the evolved architecture
2. **Begin Phase 1**: Schema updates with `profile_fetched_at` and `priority_tier`
3. **Implement two-phase seeding** with entity discovery and profile queue
4. **Set up daily roster diff** for trade/transfer detection
5. **Build EntityRepository** to replace live API widget calls

---

*Document Version: 2.0*
*Created: December 25, 2024*
*Updated: December 26, 2024*
*Author: Claude (AI Assistant)*

## Changelog

### v2.0 (December 26, 2024)
- Added tiered data coverage (priority vs non-priority leagues)
- Introduced two-phase seeding (discovery → profile fetch)
- Added daily roster diff for trade/transfer detection
- Defined priority leagues: NFL, NBA, Top 5 European + MLS
- Added `profile_fetched_at` for yearly profile refresh
- Introduced EntityRepository for local-first data access
- Reduced news cache to 60 seconds for real-time relevance
- Added "building statistical profile" status for non-priority entities
- Updated implementation phases to reflect new architecture
- Added new file structure with `diff_engine.py`, `roster_diff/`, `entity_repository.py`

### v1.0 (December 25, 2024)
- Initial plan with core schema and sport-specific data models
- Basic seeding pipeline and percentile calculation system
