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

// Raw API response types (no adapter transformation needed)
export interface PlayerProfileResponse {
  id?: string | number;
  name?: string;
  firstname?: string;
  lastname?: string;
  photo?: string;
  position?: string;
  team?: { name?: string };
}

export interface TeamProfileResponse {
  id?: string | number;
  name?: string;
  logo?: string;
  venue?: { name?: string; city?: string };
  country?: { name?: string };
}

export type ProfileResponse = PlayerProfileResponse | TeamProfileResponse;

// Type for profile data with metadata
export interface ProfileDataWithMeta {
  entityType: 'player' | 'team';
  data: ProfileResponse;
}

export interface EntityInfo {
  name: string | null;
  team: string | null;
  entityType: 'player' | 'team' | null;
}

/**
 * Extract entity name and team from profile data
 * Works with raw API response data
 */
export function extractEntityInfo(profileData: ProfileDataWithMeta | null | undefined): EntityInfo {
  if (!profileData?.data) {
    return { name: null, team: null, entityType: null };
  }

  const { entityType, data } = profileData;
  let name: string | null = null;
  let team: string | null = null;

  if (entityType === 'team') {
    const teamData = data as TeamProfileResponse;
    name = teamData.name || null;
  } else {
    const playerData = data as PlayerProfileResponse;
    name = playerData.name || `${playerData.firstname || ''} ${playerData.lastname || ''}`.trim() || null;
    team = playerData.team?.name || null;
  }

  return { name, team, entityType };
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

  // Try to get from cached page data first
  let profileData = getPageData(pageDataKey) as ProfileDataWithMeta | undefined;

  if (!profileData) {
    try {
      // Wait for another component to load the data
      profileData = await waitForPageData(pageDataKey, waitTimeout) as ProfileDataWithMeta;
    } catch {
      // Fetch it ourselves
      const url = `${apiUrl}/profile/${type}/${id}?sport=${sport.toUpperCase()}`;
      const { data } = await swrFetch<ProfileResponse>(url, CACHE_PRESETS.widget);
      
      if (data && typeof data === 'object') {
        profileData = { entityType: type as 'player' | 'team', data };
        setPageData(pageDataKey, profileData);
      }
    }
  }

  return extractEntityInfo(profileData);
}

/**
 * Format a display name from profile data
 * Useful for creating consistent name displays
 */
export function formatDisplayName(data: ProfileResponse | null | undefined, entityType: 'player' | 'team'): string {
  if (!data) return 'Unknown';

  if (entityType === 'team') {
    const teamData = data as TeamProfileResponse;
    return teamData.name || 'Unknown';
  }

  const playerData = data as PlayerProfileResponse;
  return playerData.name || `${playerData.firstname || ''} ${playerData.lastname || ''}`.trim() || 'Unknown';
}
