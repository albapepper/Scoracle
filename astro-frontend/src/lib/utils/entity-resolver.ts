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

export interface ProfileInfo {
  full_name?: string;
  first_name?: string;
  last_name?: string;
  name?: string;
  team?: { name: string };
}

export interface ProfileResponse {
  entity_id: number;
  entity_type: 'player' | 'team';
  info: ProfileInfo;
}

export interface EntityInfo {
  name: string | null;
  team: string | null;
  entityType: 'player' | 'team' | null;
}

/**
 * Extract entity name and team from profile info
 */
export function extractEntityInfo(data: ProfileResponse | null | undefined): EntityInfo {
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

  // Try to get from cached page data first
  let profileData = getPageData(pageDataKey) as ProfileResponse | undefined;

  if (!profileData) {
    try {
      // Wait for another component to load the data
      profileData = await waitForPageData(pageDataKey, waitTimeout) as ProfileResponse;
    } catch {
      // Fetch it ourselves
      const url = `${apiUrl}/widget/profile/${type}/${id}?sport=${sport.toUpperCase()}`;
      const { data } = await swrFetch<ProfileResponse>(url, CACHE_PRESETS.widget);
      profileData = data;
      if (data) {
        setPageData(pageDataKey, data);
      }
    }
  }

  return extractEntityInfo(profileData);
}

/**
 * Format a display name from profile info
 * Useful for creating consistent name displays
 */
export function formatDisplayName(info: ProfileInfo | null | undefined, entityType: 'player' | 'team'): string {
  if (!info) return 'Unknown';

  if (entityType === 'team') {
    return info.name || info.full_name || 'Unknown';
  }

  return info.full_name || `${info.first_name || ''} ${info.last_name || ''}`.trim() || 'Unknown';
}
