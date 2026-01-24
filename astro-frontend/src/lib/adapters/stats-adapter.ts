/**
 * Stats Adapter
 *
 * Transforms raw backend stats data into the format components expect.
 * This is the SINGLE POINT OF CHANGE if the backend stats response format changes.
 *
 * The stats endpoint already returns a well-structured response, so this adapter
 * mainly normalizes the percentiles format (array vs object).
 *
 * Usage:
 * ```typescript
 * import { normalizeStatsResponse, isValidStatsResponse } from '../lib/adapters';
 *
 * const rawData = await fetch('/api/v1/stats/player/123?sport=NBA');
 * if (!isValidStatsResponse(rawData)) {
 *   showError();
 *   return;
 * }
 * const data = normalizeStatsResponse(rawData);
 * ```
 */

import type { RawStatsResponse, NormalizedStatsResponse } from './types';

/**
 * Check if raw data is a valid stats response
 *
 * @param data - Raw data from API
 * @returns True if data has required fields
 */
export function isValidStatsResponse(data: unknown): data is RawStatsResponse {
  return (
    data !== null &&
    typeof data === 'object' &&
    'entity_id' in data &&
    'stats' in data &&
    typeof (data as RawStatsResponse).stats === 'object'
  );
}

/**
 * Transform raw stats data into normalized format
 *
 * Main transformation: normalizes percentiles to always be an object
 * (backend may return array or object format)
 *
 * @param rawData - Raw stats data from backend
 * @returns Normalized stats response
 */
export function normalizeStatsResponse(
  rawData: RawStatsResponse
): NormalizedStatsResponse {
  // Normalize percentiles to always be an object
  let percentiles: Record<string, number> = {};

  if (Array.isArray(rawData.percentiles)) {
    // Convert array format to object
    for (const p of rawData.percentiles) {
      if (p.stat_key && typeof p.percentile === 'number') {
        percentiles[p.stat_key] = p.percentile;
      }
    }
  } else if (rawData.percentiles && typeof rawData.percentiles === 'object') {
    // Already an object, use as-is
    percentiles = rawData.percentiles as Record<string, number>;
  }

  return {
    entity_id: rawData.entity_id,
    entity_type: rawData.entity_type,
    sport: rawData.sport,
    season: rawData.season,
    stats: rawData.stats,
    percentiles,
  };
}

/**
 * Get a specific stat value from stats response
 *
 * @param data - Normalized stats response
 * @param statKey - Key of the stat to retrieve
 * @returns Stat value or null if not found
 */
export function getStatValue(
  data: NormalizedStatsResponse,
  statKey: string
): number | string | null {
  const value = data.stats[statKey];
  if (value === undefined || value === null) {
    return null;
  }
  return value as number | string;
}

/**
 * Get percentile for a specific stat
 *
 * @param data - Normalized stats response
 * @param statKey - Key of the stat
 * @returns Percentile value (0-100) or null if not available
 */
export function getStatPercentile(
  data: NormalizedStatsResponse,
  statKey: string
): number | null {
  return data.percentiles[statKey] ?? null;
}
