/**
 * Entity API - fetches entity data from backend
 * Uses native fetch instead of axios for smaller bundle
 */

const API_BASE = import.meta.env.VITE_API_URL || '/api';

export interface WidgetData {
  type: 'player' | 'team';
  display_name: string;
  subtitle?: string;
  photo_url?: string;
  logo_url?: string;
  position?: string;
  age?: number;
  height?: string;
  conference?: string;
  division?: string;
}

export interface EntityInfo {
  id: string;
  name: string;
  type: 'player' | 'team';
  sport?: string;
}

export interface NewsArticle {
  id: string;
  title: string;
  url: string;
  source: string;
  published_at: string;
  summary?: string;
  image_url?: string;
}

export interface EntityResponse {
  entity: EntityInfo;
  widget?: WidgetData;
  news?: NewsArticle[];
  enhanced?: Record<string, unknown>;
  stats?: Record<string, unknown>;
}

export interface GetEntityOptions {
  includeWidget?: boolean;
  includeNews?: boolean;
  includeEnhanced?: boolean;
  includeStats?: boolean;
  refresh?: boolean;
  skipCache?: boolean;
}

/**
 * Fetch entity data from the API
 */
export async function getEntity(
  entityType: string,
  entityId: string,
  sport: string,
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

  const response = await fetch(
    `${API_BASE}/entity/${entityType}/${entityId}?${params}`
  );
  
  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`);
  }
  
  return response.json();
}

/**
 * Fetch news/mentions for an entity
 */
export async function getEntityMentions(
  entityType: string,
  entityId: string,
  sport: string,
  options: { limit?: number; offset?: number } = {}
): Promise<NewsArticle[]> {
  const params = new URLSearchParams({ sport });
  
  if (options.limit) params.append('limit', String(options.limit));
  if (options.offset) params.append('offset', String(options.offset));

  const response = await fetch(
    `${API_BASE}/entity/${entityType}/${entityId}/mentions?${params}`
  );
  
  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`);
  }
  
  const data = await response.json();
  return data.news || [];
}

// Simple in-memory cache
const entityCache = new Map<string, { data: EntityResponse; timestamp: number }>();
const CACHE_TTL = 5 * 60 * 1000; // 5 minutes

function getCacheKey(entityType: string, entityId: string, sport: string, includes: string[]): string {
  return `${sport}:${entityType}:${entityId}:${includes.sort().join(',')}`;
}

/**
 * Get cached entity data if available and fresh
 */
export function getCached(
  entityType: string,
  entityId: string,
  sport: string,
  includes: string[]
): EntityResponse | null {
  const key = getCacheKey(entityType, entityId, sport, includes);
  const cached = entityCache.get(key);
  
  if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
    return cached.data;
  }
  
  return null;
}

/**
 * Store entity data in cache
 */
export function setCache(
  entityType: string,
  entityId: string,
  sport: string,
  includes: string[],
  data: EntityResponse
): void {
  const key = getCacheKey(entityType, entityId, sport, includes);
  entityCache.set(key, { data, timestamp: Date.now() });
}

/**
 * Clear all cached data
 */
export function clearCache(): void {
  entityCache.clear();
}

