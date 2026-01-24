/**
 * Profile Adapter
 *
 * Transforms raw backend profile data into the format components expect.
 * This is the SINGLE POINT OF CHANGE if the backend profile response format changes.
 *
 * Usage:
 * ```typescript
 * import { normalizeProfileResponse, isValidProfileResponse } from '../lib/adapters';
 *
 * const rawData = await fetch('/api/v1/profile/player/123?sport=NBA');
 * if (!isValidProfileResponse(rawData)) {
 *   showError();
 *   return;
 * }
 * const data = normalizeProfileResponse(rawData, 'player', 'NBA');
 * ```
 */

import type {
  RawProfileResponse,
  NormalizedProfileResponse,
  EntityType,
} from './types';

/**
 * Check if raw data is a valid profile response
 *
 * @param data - Raw data from API
 * @returns True if data has required fields
 */
export function isValidProfileResponse(data: unknown): data is RawProfileResponse {
  return (
    data !== null &&
    typeof data === 'object' &&
    'id' in data &&
    typeof (data as RawProfileResponse).id === 'number'
  );
}

/**
 * Transform raw profile data into normalized format
 *
 * @param rawData - Raw profile data from backend
 * @param entityType - Entity type ('player' or 'team')
 * @param sport - Sport code (e.g., 'NBA', 'NFL', 'FOOTBALL')
 * @returns Normalized profile response with wrapper structure
 */
export function normalizeProfileResponse(
  rawData: RawProfileResponse,
  entityType: EntityType,
  sport: string
): NormalizedProfileResponse {
  return {
    entity_id: rawData.id,
    entity_type: entityType,
    sport: sport.toUpperCase(),
    info: rawData,
  };
}

/**
 * Extract display name from profile data
 * Useful for getting a name regardless of player/team
 *
 * @param data - Raw or normalized profile data
 * @param entityType - Entity type to determine name field
 * @returns Display name string
 */
export function getProfileDisplayName(
  data: RawProfileResponse | NormalizedProfileResponse,
  entityType?: EntityType
): string {
  // Handle normalized response (has info wrapper)
  const profile = 'info' in data ? data.info : data;
  const type = entityType || ('entity_type' in data ? data.entity_type : 'player');

  if (type === 'team') {
    return profile.name || profile.full_name || 'Unknown Team';
  }

  return (
    profile.full_name ||
    `${profile.first_name || ''} ${profile.last_name || ''}`.trim() ||
    'Unknown Player'
  );
}
