import { api } from './client';
import type { EntityResponse, EntityType, SportId } from '../types';

export interface GetEntityOptions {
  includeWidget?: boolean;
  includeNews?: boolean;
  includeEnhanced?: boolean;
  includeStats?: boolean;
  refresh?: boolean;
}

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
