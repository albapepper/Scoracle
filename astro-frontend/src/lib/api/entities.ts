/**
 * Entity API Functions
 * 
 * Connects to backend endpoints:
 * - GET /api/v1/widget/{type}/{id}?sport={sport}
 * - GET /api/v1/news/{entity_name}?hours={hours}
 */

import { api } from './client';
import type { EntityType, SportId, NewsData } from '../types';

// Raw API-Sports response for widgets
export interface WidgetResponse {
  // Team response
  team?: {
    id: number;
    name: string;
    logo?: string;
    country?: string;
  };
  venue?: {
    name?: string;
    city?: string;
  };
  // Player response
  player?: {
    id: number;
    name?: string;
    firstname?: string;
    lastname?: string;
    photo?: string;
  };
  statistics?: Array<{
    team?: { name: string };
  }>;
}

export interface GetEntityOptions {
  refresh?: boolean;
}

/**
 * Fetch entity widget data from API-Sports via backend
 * 
 * @param entityType - 'player' or 'team'
 * @param entityId - Entity ID
 * @param sport - Sport code: NBA, NFL, FOOTBALL
 */
export async function getWidget(
  entityType: EntityType,
  entityId: string,
  sport: SportId,
  options: GetEntityOptions = {}
): Promise<WidgetResponse> {
  const params = new URLSearchParams({ sport });
  
  if (options.refresh) {
    params.append('refresh', 'true');
  }

  return api.get<WidgetResponse>(`/widget/${entityType}/${entityId}?${params}`);
}

/**
 * Fetch news for an entity name
 * 
 * @param entityName - Name to search (e.g., "Detroit Pistons")
 * @param hours - Hours to look back (default 48)
 */
export async function getNews(
  entityName: string,
  hours: number = 48
): Promise<NewsData> {
  const encodedName = encodeURIComponent(entityName);
  return api.get<NewsData>(`/news/${encodedName}?hours=${hours}`);
}
