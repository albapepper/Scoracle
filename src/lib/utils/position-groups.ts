/**
 * Position Groups Utility
 *
 * Normalizes raw positions from API into comparable groups.
 * This enables position-filtered comparison search where users
 * can only compare players of similar positions.
 *
 * Usage:
 *   import { getPositionGroup, getPositionGroupDisplay } from './position-groups';
 *   const group = getPositionGroup('NBA', 'PG'); // Returns 'guard'
 *   const display = getPositionGroupDisplay('guard'); // Returns 'Guard'
 */

type SportKey = 'nba' | 'nfl' | 'football';

/**
 * Position group mappings by sport.
 * Maps raw position strings to normalized group identifiers.
 */
const POSITION_GROUPS: Record<SportKey, Record<string, string>> = {
  nba: {
    // Guards
    'G': 'guard',
    'PG': 'guard',
    'SG': 'guard',
    'Point Guard': 'guard',
    'Shooting Guard': 'guard',
    'Guard': 'guard',
    // Forwards
    'F': 'forward',
    'SF': 'forward',
    'PF': 'forward',
    'Small Forward': 'forward',
    'Power Forward': 'forward',
    'Forward': 'forward',
    // Centers
    'C': 'center',
    'Center': 'center',
    // Combo positions
    'G-F': 'guard-forward',
    'F-G': 'guard-forward',
    'Guard-Forward': 'guard-forward',
    'F-C': 'forward-center',
    'C-F': 'forward-center',
    'Forward-Center': 'forward-center',
  },

  nfl: {
    // Quarterback
    'QB': 'quarterback',
    'Quarterback': 'quarterback',
    // Running Backs
    'RB': 'running-back',
    'FB': 'running-back',
    'HB': 'running-back',
    'Running Back': 'running-back',
    'Fullback': 'running-back',
    // Receivers
    'WR': 'receiver',
    'TE': 'receiver',
    'Wide Receiver': 'receiver',
    'Tight End': 'receiver',
    // Offensive Line
    'OT': 'offensive-line',
    'OG': 'offensive-line',
    'C': 'offensive-line',
    'OL': 'offensive-line',
    'T': 'offensive-line',
    'G': 'offensive-line',
    'Offensive Tackle': 'offensive-line',
    'Offensive Guard': 'offensive-line',
    'Center': 'offensive-line',
    // Defensive Line
    'DE': 'defensive-line',
    'DT': 'defensive-line',
    'NT': 'defensive-line',
    'DL': 'defensive-line',
    'Defensive End': 'defensive-line',
    'Defensive Tackle': 'defensive-line',
    'Nose Tackle': 'defensive-line',
    // Linebackers
    'LB': 'linebacker',
    'ILB': 'linebacker',
    'OLB': 'linebacker',
    'MLB': 'linebacker',
    'Linebacker': 'linebacker',
    'Inside Linebacker': 'linebacker',
    'Outside Linebacker': 'linebacker',
    'Middle Linebacker': 'linebacker',
    // Defensive Backs
    'CB': 'defensive-back',
    'S': 'defensive-back',
    'FS': 'defensive-back',
    'SS': 'defensive-back',
    'DB': 'defensive-back',
    'Cornerback': 'defensive-back',
    'Safety': 'defensive-back',
    'Free Safety': 'defensive-back',
    'Strong Safety': 'defensive-back',
    // Special Teams
    'K': 'special-teams',
    'P': 'special-teams',
    'LS': 'special-teams',
    'Kicker': 'special-teams',
    'Punter': 'special-teams',
    'Long Snapper': 'special-teams',
  },

  football: {
    // Goalkeeper
    'GK': 'goalkeeper',
    'Goalkeeper': 'goalkeeper',
    'G': 'goalkeeper',
    // Defenders
    'CB': 'defender',
    'LB': 'defender',
    'RB': 'defender',
    'LWB': 'defender',
    'RWB': 'defender',
    'SW': 'defender',
    'D': 'defender',
    'Defender': 'defender',
    'Centre-Back': 'defender',
    'Left-Back': 'defender',
    'Right-Back': 'defender',
    // Midfielders
    'CDM': 'midfielder',
    'CM': 'midfielder',
    'CAM': 'midfielder',
    'LM': 'midfielder',
    'RM': 'midfielder',
    'DM': 'midfielder',
    'AM': 'midfielder',
    'M': 'midfielder',
    'Midfielder': 'midfielder',
    'Defensive Midfield': 'midfielder',
    'Central Midfield': 'midfielder',
    'Attacking Midfield': 'midfielder',
    // Forwards/Attackers
    'LW': 'attacker',
    'RW': 'attacker',
    'CF': 'attacker',
    'ST': 'attacker',
    'SS': 'attacker',
    'F': 'attacker',
    'A': 'attacker',
    'Attacker': 'attacker',
    'Forward': 'attacker',
    'Left Winger': 'attacker',
    'Right Winger': 'attacker',
    'Centre-Forward': 'attacker',
    'Striker': 'attacker',
  },
};

/**
 * Display names for position groups.
 */
const POSITION_GROUP_DISPLAY: Record<string, string> = {
  // NBA
  'guard': 'Guard',
  'forward': 'Forward',
  'center': 'Center',
  'guard-forward': 'Guard/Forward',
  'forward-center': 'Forward/Center',
  // NFL
  'quarterback': 'Quarterback',
  'running-back': 'Running Back',
  'receiver': 'Receiver',
  'offensive-line': 'Offensive Lineman',
  'defensive-line': 'Defensive Lineman',
  'linebacker': 'Linebacker',
  'defensive-back': 'Defensive Back',
  'special-teams': 'Special Teams',
  // Football/Soccer
  'goalkeeper': 'Goalkeeper',
  'defender': 'Defender',
  'midfielder': 'Midfielder',
  'attacker': 'Attacker',
};

/**
 * Get the normalized position group for a raw position string.
 *
 * @param sport - The sport (nba, nfl, football)
 * @param rawPosition - The raw position string from API
 * @returns The normalized position group identifier, or undefined if not found
 */
export function getPositionGroup(sport: string, rawPosition: string | undefined | null): string | undefined {
  if (!rawPosition) return undefined;

  const sportKey = sport.toLowerCase() as SportKey;
  const sportGroups = POSITION_GROUPS[sportKey];

  if (!sportGroups) return undefined;

  // Try exact match first
  if (sportGroups[rawPosition]) {
    return sportGroups[rawPosition];
  }

  // Try case-insensitive match
  const normalized = rawPosition.trim();
  for (const [key, group] of Object.entries(sportGroups)) {
    if (key.toLowerCase() === normalized.toLowerCase()) {
      return group;
    }
  }

  return undefined;
}

/**
 * Get the display name for a position group.
 *
 * @param groupId - The position group identifier
 * @returns The human-readable display name
 */
export function getPositionGroupDisplay(groupId: string | undefined | null): string {
  if (!groupId) return 'Unknown';
  return POSITION_GROUP_DISPLAY[groupId] || groupId;
}

/**
 * Check if two positions are in the same group.
 *
 * @param sport - The sport
 * @param position1 - First position
 * @param position2 - Second position
 * @returns True if both positions belong to the same group
 */
export function isSamePositionGroup(
  sport: string,
  position1: string | undefined | null,
  position2: string | undefined | null
): boolean {
  const group1 = getPositionGroup(sport, position1);
  const group2 = getPositionGroup(sport, position2);

  // If either position is unknown, allow comparison (don't filter)
  if (!group1 || !group2) return true;

  return group1 === group2;
}

/**
 * Get all position groups for a sport.
 *
 * @param sport - The sport
 * @returns Array of unique position group identifiers
 */
export function getPositionGroupsForSport(sport: string): string[] {
  const sportKey = sport.toLowerCase() as SportKey;
  const sportGroups = POSITION_GROUPS[sportKey];

  if (!sportGroups) return [];

  return [...new Set(Object.values(sportGroups))];
}
