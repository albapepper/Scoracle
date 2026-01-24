/**
 * Entity Resolver
 *
 * Utility for resolving entity names and info from profile data.
 * Consolidates the repeated entity name resolution logic used across components.
 *
 * Usage:
 * ```typescript
 * const entityInfo = await resolveEntityInfo(apiUrl, type, id, sport);
 * console.log(entityInfo.name, entityInfo.team);
 * ```
 */

import { swrFetch, waitForPageData, getPageData, setPageData, CACHE_PRESETS, type PageData } from './api-fetcher';
import {
  isValidProfileResponse,
  normalizeProfileResponse,
  type RawProfileResponse,
  type NormalizedProfileResponse,
} from '../adapters';

// Re-export types for backwards compatibility
// ProfileInfo uses RawProfileResponse since that's what's stored in the info field
export type ProfileInfo = RawProfileResponse;
export type ProfileResponse = NormalizedProfileResponse;

export interface EntityInfo {
  name: string | null;
  team: string | null;
  entityType: 'player' | 'team' | null;
}

/**
 * Extract entity name and team from profile info
 * Works with normalized profile response (after adapter transformation)
 */
export function extractEntityInfo(data: NormalizedProfileResponse | null | undefined): EntityInfo {
  if (!data?.info) {
    return { name: null, team: null, entityType: null };
  }

  const info = data.info;
  let name: string | null = null;
  let team: string | null = null;

  if (data.entity_type === 'team') {
    name = info.name || info.full_name || null;
  } else {
    name = info.full_name || `${info.first_name || ''} ${info.last_name || ''}`.trim() || null;
    team = info.team?.name || null;
  }

  return { name, team, entityType: data.entity_type };
}

/**
 * Resolve entity info from page data or fetch from API
 *
 * @param apiUrl - Base API URL
 * @param type - Entity type ('player' or 'team')
 * @param id - Entity ID
 * @param sport - Sport code
 * @param options - Optional configuration
 */
export async function resolveEntityInfo(
  apiUrl: string,
  type: string,
  id: string,
  sport: string,
  options: {
    /** Timeout in ms for waiting on page data (default: 1000) */
    waitTimeout?: number;
    /** Page data key to check (default: 'widget') */
    pageDataKey?: keyof PageData;
  } = {}
): Promise<EntityInfo> {
  const { waitTimeout = 1000, pageDataKey = 'widget' } = options;

  // Try to get from cached page data first (already normalized)
  let profileData = getPageData(pageDataKey) as NormalizedProfileResponse | undefined;

  if (!profileData) {
    try {
      // Wait for another component to load the data
      profileData = await waitForPageData(pageDataKey, waitTimeout) as NormalizedProfileResponse;
    } catch {
      // Fetch it ourselves
      const url = `${apiUrl}/profile/${type}/${id}?sport=${sport.toUpperCase()}`;
      const { data: rawData } = await swrFetch<RawProfileResponse>(url, CACHE_PRESETS.widget);
      
      // Transform raw data using adapter
      if (isValidProfileResponse(rawData)) {
        profileData = normalizeProfileResponse(rawData, type as 'player' | 'team', sport);
        setPageData(pageDataKey, profileData);
      }
    }
  }

  return extractEntityInfo(profileData);
}

/**
 * Format a display name from profile info
 * Useful for creating consistent name displays
 */
export function formatDisplayName(info: RawProfileResponse | null | undefined, entityType: 'player' | 'team'): string {
  if (!info) return 'Unknown';

  if (entityType === 'team') {
    return info.name || info.full_name || 'Unknown';
  }

  return info.full_name || `${info.first_name || ''} ${info.last_name || ''}`.trim() || 'Unknown';
}
