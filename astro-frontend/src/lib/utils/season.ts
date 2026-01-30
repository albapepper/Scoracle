/**
 * Season Utility
 *
 * Provides current season year for API calls.
 * Centralized location for season logic that can be enhanced later
 * with sport-specific rules.
 */

/**
 * Get the current season year for a sport.
 *
 * @param sport - Optional sport identifier (for future sport-specific logic)
 * @returns The current season year
 *
 * TODO: Add sport-specific logic:
 * - NBA: Season spans calendar years (2024-25 season starts in Oct 2024)
 * - NFL: Season year is the year it starts (2024 season starts in Sep 2024)
 * - Football (Soccer): European season spans years (2024-25 starts Aug 2024)
 *
 * @example
 * ```ts
 * const season = getCurrentSeason('NBA'); // Returns 2025
 * const season = getCurrentSeason(); // Returns 2025 (default)
 * ```
 */
export function getCurrentSeason(_sport?: string): number {
  // Default to 2025 for all sports
  // Future: implement sport-specific logic based on current date
  return 2025;
}

/**
 * Get available seasons for a sport (for dropdowns, etc.)
 *
 * @param sport - Sport identifier
 * @returns Array of available season years
 */
export function getAvailableSeasons(_sport?: string): number[] {
  // Default available seasons
  // Future: could fetch from API or configure per sport
  return [2025, 2024, 2023];
}
