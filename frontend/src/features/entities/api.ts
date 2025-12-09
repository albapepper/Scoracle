/**
 * Unified Entity API
 * 
 * Single API module for all entity operations.
 * Uses the new /entity/{type}/{id} endpoint.
 */
import { http } from '../_shared/http';

export interface EntityInfo {
  id: string;
  name: string;
  entity_type: 'player' | 'team';
  sport: string;
  first_name?: string | null;
  last_name?: string | null;
  team?: string | null;
  league?: string | null;
}

export interface WidgetData {
  type: 'player' | 'team';
  id: string;
  name: string;
  display_name: string;
  subtitle: string;
  first_name?: string | null;
  last_name?: string | null;
  team?: string | null;
  league?: string | null;
  sport: string;
}

export interface NewsArticle {
  title: string;
  link: string;
  pub_date?: string | null;
  source?: string | null;
}

export interface NewsData {
  query: string;
  count: number;
  articles: NewsArticle[];
}

export interface EntityResponse {
  entity: EntityInfo;
  widget?: WidgetData;
  news?: NewsData;
}

/**
 * Get entity with optional widget and news data.
 * 
 * This single call replaces multiple legacy endpoints.
 */
export async function getEntity(
  entityType: 'player' | 'team',
  entityId: string,
  sport: string,
  options: { includeWidget?: boolean; includeNews?: boolean } = {}
): Promise<EntityResponse> {
  const { includeWidget = true, includeNews = true } = options;
  
  const includes: string[] = [];
  if (includeWidget) includes.push('widget');
  if (includeNews) includes.push('news');
  
  const params = new URLSearchParams({
    sport: sport.toUpperCase(),
    include: includes.join(','),
  });
  
  return http.get<EntityResponse>(`entity/${entityType}/${entityId}?${params.toString()}`);
}

/**
 * Get just entity info (no widget or news).
 */
export async function getEntityInfo(
  entityType: 'player' | 'team',
  entityId: string,
  sport: string
): Promise<EntityInfo> {
  const response = await getEntity(entityType, entityId, sport, {
    includeWidget: false,
    includeNews: false,
  });
  return response.entity;
}

/**
 * Get entity mentions (news articles).
 * 
 * Legacy compatibility function.
 */
export async function getEntityMentions(
  entityType: string,
  entityId: string,
  sport: string
): Promise<{ entity_info: EntityInfo; mentions: NewsArticle[] }> {
  const response = await getEntity(
    entityType as 'player' | 'team',
    entityId,
    sport,
    { includeWidget: false, includeNews: true }
  );
  
  return {
    entity_info: response.entity,
    mentions: response.news?.articles || [],
  };
}

// Export unified API
export const entityApi = {
  getEntity,
  getEntityInfo,
  getEntityMentions,
};

export default entityApi;
