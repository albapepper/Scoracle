/**
 * Stats Categorizer Utility
 *
 * Transforms flat stats from the API into categorized format for display.
 * Handles NBA, NFL, and Football (soccer) sports with appropriate stat groupings.
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
 * Category configurations for each sport
 */
const CATEGORY_CONFIG: Record<string, { id: string; label: string; keys: string[] }[]> = {
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
};

/**
 * Human-readable labels for stat keys
 */
const STAT_LABELS: Record<string, string> = {
  // NBA
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

  // NFL
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

  // Football (Soccer)
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
};

/**
 * Short abbreviations for box score display
 */
const STAT_ABBREVS: Record<string, string> = {
  // NBA
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

  // NFL
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

  // Football (Soccer)
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
};

/**
 * Box score configuration - groups of stats for horizontal display
 * Each group becomes a row in the box score table
 */
const BOX_SCORE_CONFIG: Record<string, { id: string; label: string; keys: string[] }[]> = {
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
};

/**
 * Transform flat stats from API into categorized format
 *
 * @param stats - Flat stats object from API
 * @param percentiles - Optional percentile values for each stat
 * @param sport - Sport identifier (NBA, NFL, FOOTBALL)
 * @returns Array of categories with their stats, sorted by volume
 */
export function categorizeStats(
  stats: Record<string, unknown>,
  percentiles: Record<string, number> = {},
  sport: string
): Category[] {
  const config = CATEGORY_CONFIG[sport.toUpperCase()] || CATEGORY_CONFIG.NBA;
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
  sport?: string
): Array<{ label: string; value: string | number }> {
  const result: Array<{ label: string; value: string | number }> = [];

  // Keys to exclude from display
  const excludeKeys = new Set(['season', 'player_id', 'team_id', 'id']);

  // Get ordered keys if sport is specified
  let orderedKeys: string[] = [];
  if (sport) {
    const config = CATEGORY_CONFIG[sport.toUpperCase()] || CATEGORY_CONFIG.NBA;
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
 * @returns Array of groups, each containing stats for a row in the box score
 */
export function getBoxScoreGroups(
  stats: Record<string, unknown>,
  sport: string
): BoxScoreGroup[] {
  const config = BOX_SCORE_CONFIG[sport.toUpperCase()] || BOX_SCORE_CONFIG.NBA;
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
