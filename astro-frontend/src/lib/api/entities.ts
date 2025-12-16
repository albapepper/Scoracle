/**
 * Entity API Functions
 * 
 * Connects to backend endpoints:
 * - GET /api/v1/entity/{type}/{id}?sport={sport}&include={widget,news,enhanced,stats}
 * - GET /api/v1/entity/search?query={q}&sport={sport}
 */

import { api } from './client';
import type { EntityResponse, EntityType, SportId, SearchResponse, MentionsResponse } from '../types';

export interface GetEntityOptions {
  includeWidget?: boolean;
  includeNews?: boolean;
  includeEnhanced?: boolean;
  includeStats?: boolean;
  refresh?: boolean;
}

/**
 * Fetch entity data with optional widget, news, and stats
 * 
 * @param entityType - 'player' or 'team'
 * @param entityId - Entity ID
 * @param sport - Sport code: NBA, NFL, FOOTBALL
 * @param options - What data to include
 */
export async function getEntity(
  entityType: EntityType,
  entityId: string,
  sport: SportId,
  options: GetEntityOptions = {}
): Promise<EntityResponse> {
  const params = new URLSearchParams({ sport });
  
  const includes: string[] = [];
  if (options.includeWidget !== false) includes.push('widget');
  if (options.includeNews) includes.push('news');
  if (options.includeEnhanced) includes.push('enhanced');
  if (options.includeStats) includes.push('stats');
  
  if (includes.length > 0) {
    params.append('include', includes.join(','));
  }
  
  if (options.refresh) {
    params.append('refresh', 'true');
  }

  return api.get<EntityResponse>(`/entity/${entityType}/${entityId}?${params}`);
}

/**
 * Search for entities by name
 */
export async function searchEntities(
  query: string,
  sport: SportId,
  entityType?: EntityType,
  limit: number = 10
): Promise<SearchResponse> {
  const params = new URLSearchParams({ 
    query, 
    sport,
    limit: String(limit)
  });
  
  if (entityType) {
    params.append('entity_type', entityType);
  }

  return api.get<SearchResponse>(`/entity/search?${params}`);
}

/**
 * Get entity mentions/news (legacy endpoint)
 */
export async function getEntityMentions(
  entityType: EntityType,
  entityId: string,
  sport: SportId,
  hours: number = 48
): Promise<MentionsResponse> {
  const params = new URLSearchParams({ 
    sport,
    hours: String(hours)
  });

  return api.get<MentionsResponse>(`/entity/${entityType}/${entityId}/mentions?${params}`);
}
