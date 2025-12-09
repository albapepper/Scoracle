/**
 * Unified Entity API with Tiered Data Support
 * 
 * Data Tiers:
 * - Basic: From bundled JSON (instant, free)
 * - Widget: Display-ready entity data
 * - Enhanced: Includes API-Sports profile (photo, position, etc.)
 * - Stats: Includes API-Sports statistics
 * - News: Recent news articles
 * 
 * Security:
 * - API key never exposed to frontend
 * - All external API calls happen on backend
 */
import { http } from '../_shared/http';
import { getCached, setCache } from './cache';

// ============ Types ============

export interface EntityInfo {
  id: string;
  name: string;
  entity_type: 'player' | 'team';
  sport: string;
  first_name?: string | null;
  last_name?: string | null;
  team?: string | null;
  league?: string | null;
  // Enhanced fields (from API-Sports)
  photo_url?: string | null;
  logo_url?: string | null;
  position?: string | null;
  height?: string | null;
  weight?: string | null;
  age?: number | null;
  nationality?: string | null;
  conference?: string | null;
  division?: string | null;
  enhanced?: boolean;
}

export interface WidgetData {
  type: 'player' | 'team';
  id: string;
  name: string;
  display_name: string;
  subtitle: string;
  sport: string;
  // Basic
  first_name?: string | null;
  last_name?: string | null;
  team?: string | null;
  league?: string | null;
  // Enhanced
  photo_url?: string | null;
  logo_url?: string | null;
  position?: string | null;
  age?: number | null;
  height?: string | null;
  conference?: string | null;
  division?: string | null;
  enhanced: boolean;
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
  stats?: Record<string, any>;
}

// ============ Options ============

export interface GetEntityOptions {
  /** Include widget display data (default: true) */
  includeWidget?: boolean;
  /** Include news articles (default: false for performance) */
  includeNews?: boolean;
  /** Include API-Sports enhanced data like photos (default: false) */
  includeEnhanced?: boolean;
  /** Include API-Sports statistics (default: false) */
  includeStats?: boolean;
  /** Force refresh from API-Sports, skip cache (default: false) */
  refresh?: boolean;
  /** Skip frontend cache (default: false) */
  skipCache?: boolean;
}

// ============ API Functions ============

/**
 * Get entity with optional widget, enhanced data, stats, and news.
 * 
 * Uses tiered data:
 * - Basic/widget: Instant from bundled JSON
 * - Enhanced/stats: From API-Sports (cached on backend)
 * - News: From RSS (cached on backend)
 */
export async function getEntity(
  entityType: 'player' | 'team',
  entityId: string,
  sport: string,
  options: GetEntityOptions = {}
): Promise<EntityResponse> {
  const {
    includeWidget = true,
    includeNews = false,
    includeEnhanced = false,
    includeStats = false,
    refresh = false,
    skipCache = false,
  } = options;
  
  // Build include string
  const includes: string[] = [];
  if (includeWidget) includes.push('widget');
  if (includeNews) includes.push('news');
  if (includeEnhanced) includes.push('enhanced');
  if (includeStats) includes.push('stats');
  
  // Check frontend cache (for non-enhanced, non-refreshed requests)
  const cacheKey = includes.join(',');
  if (!skipCache && !refresh) {
    const cached = getCached(entityType, entityId, sport, includes);
    if (cached) {
      console.debug('[EntityAPI] Cache hit:', entityType, entityId);
      return cached;
    }
  }
  
  // Build URL params
  const params = new URLSearchParams({
    sport: sport.toUpperCase(),
    include: includes.join(','),
  });
  if (refresh) {
    params.set('refresh', 'true');
  }
  
  // Fetch from backend
  const response = await http.get<EntityResponse>(`entity/${entityType}/${entityId}?${params.toString()}`);
  
  // Store in frontend cache
  setCache(entityType, entityId, sport, includes, response);
  console.debug('[EntityAPI] Fetched:', entityType, entityId, response.entity.enhanced ? '(enhanced)' : '');
  
  return response;
}

/**
 * Get entity with enhanced profile data (photo, position, etc.)
 */
export async function getEnhancedEntity(
  entityType: 'player' | 'team',
  entityId: string,
  sport: string
): Promise<EntityResponse> {
  return getEntity(entityType, entityId, sport, {
    includeWidget: true,
    includeEnhanced: true,
    includeNews: false,
  });
}

/**
 * Get entity with full data (enhanced + stats + news)
 */
export async function getFullEntity(
  entityType: 'player' | 'team',
  entityId: string,
  sport: string
): Promise<EntityResponse> {
  return getEntity(entityType, entityId, sport, {
    includeWidget: true,
    includeEnhanced: true,
    includeStats: true,
    includeNews: true,
  });
}

/**
 * Get just entity info (minimal, fast)
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
 * Prefetch entity data (for hover preloading, etc.)
 */
export function prefetchEntity(
  entityType: 'player' | 'team',
  entityId: string,
  sport: string
): void {
  const cached = getCached(entityType, entityId, sport, ['widget']);
  if (cached) return;
  
  getEntity(entityType, entityId, sport, { includeNews: false }).catch(() => {});
}

// Export unified API
export const entityApi = {
  getEntity,
  getEnhancedEntity,
  getFullEntity,
  getEntityInfo,
  prefetchEntity,
};

export default entityApi;
