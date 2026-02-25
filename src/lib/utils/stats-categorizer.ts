/**
 * Stats Categorizer Utility
 *
 * Transforms flat stats from the API into categorized format for display.
 * Handles NBA, NFL, and Football (soccer) sports with appropriate stat groupings.
 * Supports both player and team entity types with dedicated configurations.
 */

export interface StatItem {
  key: string;
  label: string;
  value: number | string | null;
  percentile?: number | null;
  rank?: number | null;
  sample_size?: number | null;
}

export interface Category {
  id: string;
  label: string;
  volume: number;
  stats: StatItem[];
}

export interface BoxScoreGroup {
  id: string;
  label: string;
  stats: BoxScoreStat[];
}

export interface BoxScoreStat {
  key: string;
  abbrev: string;
  value: number | string | null;
}

/**
 * Category configurations for each sport and entity type
 * Keys: NBA, NFL, FOOTBALL (players), NBA_TEAM, NFL_TEAM, FOOTBALL_TEAM (teams)
 */
const CATEGORY_CONFIG: Record<string, { id: string; label: string; keys: string[] }[]> = {
  // =============================================================================
  // PLAYER CONFIGS
  // =============================================================================
  NBA: [
    { id: 'scoring', label: 'Scoring', keys: ['points', 'fgm', 'fga', 'fgp', 'ftm', 'fta', 'ftp', 'tpm', 'tpa', 'tpp'] },
    { id: 'rebounds', label: 'Rebounds', keys: ['totReb', 'offReb', 'defReb'] },
    { id: 'playmaking', label: 'Playmaking', keys: ['assists', 'turnovers'] },
    { id: 'defense', label: 'Defense', keys: ['steals', 'blocks', 'pFouls'] },
    { id: 'general', label: 'General', keys: ['games', 'plusMinus'] },
  ],
  NFL: [
    { id: 'passing', label: 'Passing', keys: ['passing_yards', 'passing_tds', 'interceptions', 'passer_rating', 'completions', 'attempts'] },
    { id: 'rushing', label: 'Rushing', keys: ['rushing_yards', 'rushing_tds', 'rushing_attempts', 'yards_per_carry'] },
    { id: 'receiving', label: 'Receiving', keys: ['receiving_yards', 'receiving_tds', 'receptions', 'targets', 'yards_per_reception'] },
    { id: 'defense', label: 'Defense', keys: ['tackles', 'sacks', 'interceptions_def', 'forced_fumbles', 'passes_defended'] },
  ],
  FOOTBALL: [
    { id: 'goals', label: 'Goals & Assists', keys: ['goals', 'assists', 'shots', 'shots_on', 'penalty_scored', 'penalty_missed'] },
    { id: 'passing', label: 'Passing', keys: ['passes', 'passes_accuracy', 'key_passes', 'crosses', 'crosses_accuracy'] },
    { id: 'defense', label: 'Defense', keys: ['tackles', 'blocks', 'interceptions', 'duels_won', 'duels_total'] },
    { id: 'discipline', label: 'Discipline', keys: ['yellow_cards', 'red_cards', 'fouls_committed', 'fouls_drawn'] },
    { id: 'general', label: 'General', keys: ['games', 'minutes', 'rating'] },
  ],

  // =============================================================================
  // TEAM CONFIGS
  // =============================================================================
  NBA_TEAM: [
    { id: 'record', label: 'Record', keys: ['games_played', 'wins', 'losses', 'win_pct', 'current_streak'] },
    { id: 'scoring', label: 'Scoring', keys: ['points_per_game', 'opponent_ppg', 'point_differential'] },
    { id: 'shooting', label: 'Shooting', keys: ['fg_pct', 'tp_pct', 'ft_pct', 'effective_fg_pct', 'true_shooting_pct'] },
    { id: 'rebounds', label: 'Rebounds', keys: ['total_rebounds_per_game', 'offensive_rebounds_per_game', 'defensive_rebounds_per_game'] },
    { id: 'other', label: 'Other', keys: ['assists_per_game', 'steals_per_game', 'blocks_per_game', 'turnovers_per_game'] },
    { id: 'advanced', label: 'Advanced', keys: ['offensive_rating', 'defensive_rating', 'net_rating', 'pace'] },
  ],
  NFL_TEAM: [
    { id: 'record', label: 'Record', keys: ['games_played', 'wins', 'losses', 'ties', 'win_pct', 'point_differential'] },
    { id: 'scoring', label: 'Scoring', keys: ['points_per_game', 'opponent_ppg', 'points_for', 'points_against'] },
    { id: 'offense', label: 'Offense', keys: ['yards_per_game', 'yards_per_play', 'third_down_pct', 'red_zone_pct'] },
    { id: 'passing', label: 'Passing', keys: ['pass_yards_per_game', 'completion_pct', 'pass_touchdowns', 'team_passer_rating'] },
    { id: 'rushing', label: 'Rushing', keys: ['rush_yards_per_game', 'yards_per_carry', 'rush_touchdowns'] },
    { id: 'turnovers', label: 'Turnovers', keys: ['takeaways', 'turnovers', 'turnover_differential'] },
  ],
  FOOTBALL_TEAM: [
    { id: 'record', label: 'Record', keys: ['matches_played', 'wins', 'draws', 'losses', 'points', 'league_position'] },
    { id: 'goals', label: 'Goals', keys: ['goals_for', 'goals_against', 'goal_difference', 'goals_per_game', 'goals_conceded_per_game', 'clean_sheets', 'failed_to_score'] },
    { id: 'attack', label: 'Attack', keys: ['shots_total', 'shots_on_target', 'shot_accuracy', 'expected_goals'] },
    { id: 'defense', label: 'Defense', keys: ['tackles_per_game', 'interceptions_per_game', 'clearances_per_game', 'expected_goals_against'] },
    { id: 'discipline', label: 'Discipline', keys: ['yellow_cards', 'red_cards', 'fouls_per_game'] },
  ],
};

/**
 * Human-readable labels for stat keys
 */
const STAT_LABELS: Record<string, string> = {
  // =============================================================================
  // NBA PLAYER
  // =============================================================================
  points: 'Points',
  fgm: 'FG Made',
  fga: 'FG Attempted',
  fgp: 'FG %',
  ftm: 'FT Made',
  fta: 'FT Attempted',
  ftp: 'FT %',
  tpm: '3PT Made',
  tpa: '3PT Attempted',
  tpp: '3PT %',
  totReb: 'Rebounds',
  offReb: 'Off Rebounds',
  defReb: 'Def Rebounds',
  assists: 'Assists',
  turnovers: 'Turnovers',
  steals: 'Steals',
  blocks: 'Blocks',
  pFouls: 'Fouls',
  games: 'Games',
  plusMinus: '+/-',
  minutes: 'Minutes',

  // =============================================================================
  // NFL PLAYER
  // =============================================================================
  passing_yards: 'Pass Yards',
  passing_tds: 'Pass TDs',
  interceptions: 'Interceptions',
  passer_rating: 'Passer Rating',
  completions: 'Completions',
  attempts: 'Attempts',
  rushing_yards: 'Rush Yards',
  rushing_tds: 'Rush TDs',
  rushing_attempts: 'Rush Attempts',
  yards_per_carry: 'Yards/Carry',
  receiving_yards: 'Rec Yards',
  receiving_tds: 'Rec TDs',
  receptions: 'Receptions',
  targets: 'Targets',
  yards_per_reception: 'Yards/Rec',
  tackles: 'Tackles',
  sacks: 'Sacks',
  interceptions_def: 'INTs (Def)',
  forced_fumbles: 'Forced Fumbles',
  passes_defended: 'Passes Defended',

  // =============================================================================
  // FOOTBALL PLAYER
  // =============================================================================
  goals: 'Goals',
  shots: 'Shots',
  shots_on: 'Shots on Target',
  penalty_scored: 'Penalties Scored',
  penalty_missed: 'Penalties Missed',
  passes: 'Passes',
  passes_accuracy: 'Pass Accuracy',
  key_passes: 'Key Passes',
  crosses: 'Crosses',
  crosses_accuracy: 'Cross Accuracy',
  duels_won: 'Duels Won',
  duels_total: 'Total Duels',
  yellow_cards: 'Yellow Cards',
  red_cards: 'Red Cards',
  fouls_committed: 'Fouls Committed',
  fouls_drawn: 'Fouls Drawn',
  rating: 'Rating',

  // =============================================================================
  // NBA TEAM
  // =============================================================================
  games_played: 'Games Played',
  wins: 'Wins',
  losses: 'Losses',
  win_pct: 'Win %',
  current_streak: 'Streak',
  points_per_game: 'Points/Game',
  opponent_ppg: 'Opp Points/Game',
  point_differential: 'Point Diff',
  fg_pct: 'FG %',
  tp_pct: '3PT %',
  ft_pct: 'FT %',
  effective_fg_pct: 'Eff FG %',
  true_shooting_pct: 'True Shooting %',
  total_rebounds_per_game: 'Rebounds/Game',
  offensive_rebounds_per_game: 'Off Reb/Game',
  defensive_rebounds_per_game: 'Def Reb/Game',
  assists_per_game: 'Assists/Game',
  steals_per_game: 'Steals/Game',
  blocks_per_game: 'Blocks/Game',
  turnovers_per_game: 'Turnovers/Game',
  offensive_rating: 'Off Rating',
  defensive_rating: 'Def Rating',
  net_rating: 'Net Rating',
  pace: 'Pace',

  // =============================================================================
  // NFL TEAM
  // =============================================================================
  ties: 'Ties',
  points_for: 'Points For',
  points_against: 'Points Against',
  yards_per_game: 'Yards/Game',
  yards_per_play: 'Yards/Play',
  third_down_pct: '3rd Down %',
  red_zone_pct: 'Red Zone %',
  pass_yards_per_game: 'Pass Yards/Game',
  completion_pct: 'Completion %',
  pass_touchdowns: 'Pass TDs',
  team_passer_rating: 'Team Passer Rating',
  rush_yards_per_game: 'Rush Yards/Game',
  rush_touchdowns: 'Rush TDs',
  takeaways: 'Takeaways',
  turnover_differential: 'Turnover Diff',

  // =============================================================================
  // FOOTBALL TEAM
  // =============================================================================
  matches_played: 'Matches Played',
  draws: 'Draws',
  // points already defined above in NBA Player section
  league_position: 'League Position',
  goals_for: 'Goals For',
  goals_against: 'Goals Against',
  goal_difference: 'Goal Diff',
  goals_per_game: 'Goals/Game',
  goals_conceded_per_game: 'Conceded/Game',
  clean_sheets: 'Clean Sheets',
  failed_to_score: 'Failed to Score',
  form: 'Form',
  shots_total: 'Total Shots',
  shots_on_target: 'Shots on Target',
  shot_accuracy: 'Shot Accuracy',
  expected_goals: 'xG',
  expected_goals_against: 'xGA',
  tackles_per_game: 'Tackles/Game',
  interceptions_per_game: 'Interceptions/Game',
  clearances_per_game: 'Clearances/Game',
  fouls_per_game: 'Fouls/Game',
  home_played: 'Home Matches',
  home_wins: 'Home Wins',
  home_draws: 'Home Draws',
  home_losses: 'Home Losses',
  home_goals_for: 'Home Goals For',
  home_goals_against: 'Home Goals Against',
  away_played: 'Away Matches',
  away_wins: 'Away Wins',
  away_draws: 'Away Draws',
  away_losses: 'Away Losses',
  away_goals_for: 'Away Goals For',
  away_goals_against: 'Away Goals Against',
};

/**
 * Short abbreviations for box score display
 */
const STAT_ABBREVS: Record<string, string> = {
  // =============================================================================
  // NBA PLAYER
  // =============================================================================
  points: 'PTS',
  totReb: 'REB',
  offReb: 'OREB',
  defReb: 'DREB',
  assists: 'AST',
  steals: 'STL',
  blocks: 'BLK',
  turnovers: 'TO',
  pFouls: 'PF',
  fgp: 'FG%',
  tpp: '3P%',
  ftp: 'FT%',
  fgm: 'FGM',
  fga: 'FGA',
  ftm: 'FTM',
  fta: 'FTA',
  tpm: '3PM',
  tpa: '3PA',
  games: 'GP',
  minutes: 'MIN',
  plusMinus: '+/-',

  // =============================================================================
  // NFL PLAYER
  // =============================================================================
  passing_yards: 'YDS',
  passing_tds: 'TD',
  interceptions: 'INT',
  passer_rating: 'RTG',
  completions: 'CMP',
  attempts: 'ATT',
  rushing_yards: 'YDS',
  rushing_tds: 'TD',
  rushing_attempts: 'ATT',
  yards_per_carry: 'Y/A',
  receiving_yards: 'YDS',
  receiving_tds: 'TD',
  receptions: 'REC',
  targets: 'TGT',
  yards_per_reception: 'Y/R',
  tackles: 'TKL',
  sacks: 'SCK',
  interceptions_def: 'INT',
  forced_fumbles: 'FF',
  passes_defended: 'PD',

  // =============================================================================
  // FOOTBALL PLAYER
  // =============================================================================
  goals: 'G',
  shots: 'SH',
  shots_on: 'SOT',
  penalty_scored: 'PEN',
  penalty_missed: 'PM',
  passes: 'PAS',
  passes_accuracy: 'ACC%',
  key_passes: 'KP',
  crosses: 'CRS',
  crosses_accuracy: 'CRS%',
  duels_won: 'DW',
  duels_total: 'DT',
  yellow_cards: 'YC',
  red_cards: 'RC',
  fouls_committed: 'FC',
  fouls_drawn: 'FD',
  rating: 'RTG',

  // =============================================================================
  // NBA TEAM
  // =============================================================================
  games_played: 'GP',
  wins: 'W',
  losses: 'L',
  win_pct: 'PCT',
  current_streak: 'STK',
  points_per_game: 'PPG',
  opponent_ppg: 'OPP',
  point_differential: 'DIFF',
  fg_pct: 'FG%',
  tp_pct: '3P%',
  ft_pct: 'FT%',
  effective_fg_pct: 'eFG%',
  true_shooting_pct: 'TS%',
  total_rebounds_per_game: 'RPG',
  offensive_rebounds_per_game: 'ORPG',
  defensive_rebounds_per_game: 'DRPG',
  assists_per_game: 'APG',
  steals_per_game: 'SPG',
  blocks_per_game: 'BPG',
  turnovers_per_game: 'TOPG',
  offensive_rating: 'ORTG',
  defensive_rating: 'DRTG',
  net_rating: 'NET',
  pace: 'PACE',

  // =============================================================================
  // NFL TEAM
  // =============================================================================
  ties: 'T',
  points_for: 'PF',
  points_against: 'PA',
  yards_per_game: 'YPG',
  yards_per_play: 'Y/P',
  third_down_pct: '3D%',
  red_zone_pct: 'RZ%',
  pass_yards_per_game: 'PYPG',
  completion_pct: 'CMP%',
  pass_touchdowns: 'PTD',
  team_passer_rating: 'TRTG',
  rush_yards_per_game: 'RYPG',
  rush_touchdowns: 'RTD',
  takeaways: 'TK',
  turnover_differential: 'TO±',

  // =============================================================================
  // FOOTBALL TEAM
  // =============================================================================
  matches_played: 'MP',
  draws: 'D',
  // points already defined above in NBA Player section
  league_position: 'POS',
  goals_for: 'GF',
  goals_against: 'GA',
  goal_difference: 'GD',
  goals_per_game: 'G/G',
  goals_conceded_per_game: 'GA/G',
  clean_sheets: 'CS',
  failed_to_score: 'FTS',
  shots_total: 'SH',
  shots_on_target: 'SOT',
  shot_accuracy: 'SH%',
  expected_goals: 'xG',
  expected_goals_against: 'xGA',
  tackles_per_game: 'TKL',
  interceptions_per_game: 'INT',
  clearances_per_game: 'CLR',
  fouls_per_game: 'FPG',
  home_played: 'HP',
  home_wins: 'HW',
  home_draws: 'HD',
  home_losses: 'HL',
  home_goals_for: 'HGF',
  home_goals_against: 'HGA',
  away_played: 'AP',
  away_wins: 'AW',
  away_draws: 'AD',
  away_losses: 'AL',
  away_goals_for: 'AGF',
  away_goals_against: 'AGA',
};

/**
 * Box score configuration - groups of stats for horizontal display
 * Each group becomes a row in the box score table
 */
const BOX_SCORE_CONFIG: Record<string, { id: string; label: string; keys: string[] }[]> = {
  // =============================================================================
  // PLAYER CONFIGS
  // =============================================================================
  NBA: [
    { id: 'counting', label: 'Per Game', keys: ['points', 'totReb', 'assists', 'steals', 'blocks', 'turnovers'] },
    { id: 'shooting', label: 'Shooting', keys: ['fgp', 'tpp', 'ftp'] },
    { id: 'activity', label: 'Activity', keys: ['games', 'minutes', 'plusMinus'] },
  ],
  NFL: [
    { id: 'passing', label: 'Passing', keys: ['passing_yards', 'passing_tds', 'interceptions', 'passer_rating'] },
    { id: 'rushing', label: 'Rushing', keys: ['rushing_yards', 'rushing_tds', 'rushing_attempts', 'yards_per_carry'] },
    { id: 'receiving', label: 'Receiving', keys: ['receiving_yards', 'receiving_tds', 'receptions', 'targets'] },
    { id: 'defense', label: 'Defense', keys: ['tackles', 'sacks', 'interceptions_def', 'forced_fumbles'] },
  ],
  FOOTBALL: [
    { id: 'attacking', label: 'Attacking', keys: ['goals', 'assists', 'shots_on', 'key_passes'] },
    { id: 'passing', label: 'Passing', keys: ['passes', 'passes_accuracy', 'crosses'] },
    { id: 'defense', label: 'Defense', keys: ['tackles', 'duels_won', 'fouls_committed'] },
    { id: 'general', label: 'General', keys: ['games', 'minutes', 'rating'] },
  ],

  // =============================================================================
  // TEAM CONFIGS
  // =============================================================================
  NBA_TEAM: [
    { id: 'record', label: 'Record', keys: ['wins', 'losses', 'win_pct'] },
    { id: 'scoring', label: 'Scoring', keys: ['points_per_game', 'opponent_ppg', 'point_differential'] },
    { id: 'shooting', label: 'Shooting', keys: ['fg_pct', 'tp_pct', 'ft_pct'] },
    { id: 'other', label: 'Other', keys: ['total_rebounds_per_game', 'assists_per_game', 'turnovers_per_game'] },
  ],
  NFL_TEAM: [
    { id: 'record', label: 'Record', keys: ['wins', 'losses', 'win_pct'] },
    { id: 'scoring', label: 'Scoring', keys: ['points_per_game', 'opponent_ppg'] },
    { id: 'offense', label: 'Offense', keys: ['yards_per_game', 'pass_yards_per_game', 'rush_yards_per_game'] },
    { id: 'turnovers', label: 'Turnovers', keys: ['takeaways', 'turnovers', 'turnover_differential'] },
  ],
  FOOTBALL_TEAM: [
    { id: 'record', label: 'Record', keys: ['matches_played', 'wins', 'draws', 'losses', 'points'] },
    { id: 'goals', label: 'Goals', keys: ['goals_for', 'goals_against', 'goal_difference', 'clean_sheets'] },
    { id: 'performance', label: 'Performance', keys: ['goals_per_game', 'goals_conceded_per_game'] },
  ],
};

/**
 * Get the config key based on sport and entity type
 */
function getConfigKey(sport: string, entityType?: 'player' | 'team'): string {
  const sportUpper = sport.toUpperCase();
  if (entityType === 'team') {
    return `${sportUpper}_TEAM`;
  }
  return sportUpper;
}

/**
 * Transform flat stats from API into categorized format
 *
 * @param stats - Flat stats object from API
 * @param percentiles - Optional percentile values for each stat
 * @param sport - Sport identifier (NBA, NFL, FOOTBALL)
 * @param entityType - Entity type ('player' or 'team')
 * @returns Array of categories with their stats, sorted by volume
 */
export function categorizeStats(
  stats: Record<string, unknown>,
  percentiles: Record<string, number> = {},
  sport: string,
  entityType: 'player' | 'team' = 'player'
): Category[] {
  const configKey = getConfigKey(sport, entityType);
  const config = CATEGORY_CONFIG[configKey] || CATEGORY_CONFIG[sport.toUpperCase()] || CATEGORY_CONFIG.NBA;
  const categories: Category[] = [];

  for (const cat of config) {
    const catStats: StatItem[] = [];

    for (const key of cat.keys) {
      const value = stats[key];
      if (value !== undefined && value !== null) {
        catStats.push({
          key: key,
          label: STAT_LABELS[key] || formatStatKey(key),
          value: value as number | string,
          percentile: percentiles[key] ?? null,
        });
      }
    }

    if (catStats.length > 0) {
      categories.push({
        id: cat.id,
        label: cat.label,
        volume: catStats.length,
        stats: catStats,
      });
    }
  }

  // Sort by volume (most stats first)
  return categories.sort((a, b) => b.volume - a.volume);
}

/**
 * Format a stat key into a readable label (fallback)
 */
function formatStatKey(key: string): string {
  return key
    .replace(/_/g, ' ')
    .replace(/([a-z])([A-Z])/g, '$1 $2')
    .replace(/\b\w/g, c => c.toUpperCase());
}

/**
 * Get a human-readable label for a stat key
 */
export function getStatLabel(key: string): string {
  return STAT_LABELS[key] || formatStatKey(key);
}

/**
 * Transform flat stats to simple label/value pairs (for comparison views)
 */
export function flattenStats(
  stats: Record<string, unknown>,
  sport?: string,
  entityType: 'player' | 'team' = 'player'
): Array<{ label: string; value: string | number }> {
  const result: Array<{ label: string; value: string | number }> = [];

  // Keys to exclude from display
  const excludeKeys = new Set(['season', 'player_id', 'team_id', 'id', 'form']);

  // Get ordered keys if sport is specified
  let orderedKeys: string[] = [];
  if (sport) {
    const configKey = getConfigKey(sport, entityType);
    const config = CATEGORY_CONFIG[configKey] || CATEGORY_CONFIG[sport.toUpperCase()] || CATEGORY_CONFIG.NBA;
    orderedKeys = config.flatMap(cat => cat.keys);
  }

  // Process stats in order
  const processedKeys = new Set<string>();

  // First add ordered keys that exist
  for (const key of orderedKeys) {
    if (stats[key] !== null && stats[key] !== undefined && !excludeKeys.has(key)) {
      result.push({
        label: STAT_LABELS[key] || formatStatKey(key),
        value: stats[key] as string | number,
      });
      processedKeys.add(key);
    }
  }

  // Then add any remaining keys
  for (const [key, value] of Object.entries(stats)) {
    if (value !== null && value !== undefined && !excludeKeys.has(key) && !processedKeys.has(key)) {
      result.push({
        label: STAT_LABELS[key] || formatStatKey(key),
        value: value as string | number,
      });
    }
  }

  return result;
}

/**
 * Get box score stats grouped for horizontal table display
 *
 * @param stats - Flat stats object from API
 * @param sport - Sport identifier (NBA, NFL, FOOTBALL)
 * @param entityType - Entity type ('player' or 'team')
 * @returns Array of groups, each containing stats for a row in the box score
 */
export function getBoxScoreGroups(
  stats: Record<string, unknown>,
  sport: string,
  entityType: 'player' | 'team' = 'player'
): BoxScoreGroup[] {
  const configKey = getConfigKey(sport, entityType);
  const config = BOX_SCORE_CONFIG[configKey] || BOX_SCORE_CONFIG[sport.toUpperCase()] || BOX_SCORE_CONFIG.NBA;
  const groups: BoxScoreGroup[] = [];

  for (const groupConfig of config) {
    const groupStats: BoxScoreStat[] = [];

    for (const key of groupConfig.keys) {
      const value = stats[key];
      if (value !== undefined && value !== null) {
        groupStats.push({
          key,
          abbrev: STAT_ABBREVS[key] || key.toUpperCase().slice(0, 3),
          value: formatStatValue(value),
        });
      }
    }

    // Only add groups that have at least one stat
    if (groupStats.length > 0) {
      groups.push({
        id: groupConfig.id,
        label: groupConfig.label,
        stats: groupStats,
      });
    }
  }

  return groups;
}

/**
 * Format stat value for display (round numbers, handle percentages)
 */
function formatStatValue(value: unknown): string | number {
  if (typeof value === 'number') {
    // Check if it's a percentage (usually 0-100 or 0-1)
    if (value > 0 && value < 1) {
      return (value * 100).toFixed(1);
    }
    // Round to 1 decimal for most stats
    if (!Number.isInteger(value)) {
      return value.toFixed(1);
    }
    return value;
  }
  return String(value);
}

/**
 * Get abbreviation for a stat key
 */
export function getStatAbbrev(key: string): string {
  return STAT_ABBREVS[key] || key.toUpperCase().slice(0, 3);
}
