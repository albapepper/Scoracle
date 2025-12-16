/**
 * Scoracle Type Definitions
 * 
 * These types match the backend API response schemas from:
 * - backend/app/routers/entities.py
 * - backend/app/services/entity_service.py
 */

// Entity Types
export type EntityType = 'player' | 'team';
export type SportId = 'NBA' | 'NFL' | 'FOOTBALL';

// Backend entity info (matches EntityInfo.to_dict())
export interface EntityInfo {
  id: string;
  name: string;
  entity_type: EntityType;
  sport: SportId;
  // Player-specific
  first_name?: string;
  last_name?: string;
  team?: string;
  // Team-specific
  league?: string;
}

// Widget data returned by _build_widget_data()
export interface WidgetData {
  type: EntityType;
  id: string;
  name: string;
  sport: SportId;
  display_name: string;
  subtitle?: string;
  // Player fields
  first_name?: string;
  last_name?: string;
  team?: string;
  // Team fields
  league?: string;
  // Enhanced data (from API-Sports)
  photo_url?: string;
  logo_url?: string;
  position?: string;
  age?: number;
  height?: string;
  weight?: string;
  nationality?: string;
  conference?: string;
  division?: string;
  profile?: Record<string, unknown>;
  stats?: Record<string, unknown>;
  enhanced: boolean;
}

// News article from Google News RSS
export interface NewsArticle {
  title: string;
  link: string;
  pub_date: string | null;
  source: string;
}

// News response wrapper
export interface NewsData {
  query: string;
  count: number;
  articles: NewsArticle[];
}

// Full entity endpoint response
export interface EntityResponse {
  entity: EntityInfo | Record<string, unknown>;
  widget?: WidgetData;
  news?: NewsData;
  stats?: Record<string, unknown>;
}

// Search result response
export interface SearchResponse {
  query: string;
  sport: SportId;
  count: number;
  results: EntityInfo[];
}

// Mentions endpoint response (legacy)
export interface MentionsResponse {
  entity_type: string;
  entity_id: string;
  sport: SportId;
  entity_info: EntityInfo;
  mentions: NewsArticle[];
}

// Sport Configuration
export interface SportConfig {
  id: SportId;
  display: string;
  icon?: string;
}

export const SPORTS: readonly SportConfig[] = [
  { id: 'NBA', display: 'NBA' },
  { id: 'NFL', display: 'NFL' },
  { id: 'FOOTBALL', display: 'Football' },
] as const;

// Autocomplete Types (for client-side search from bundled JSON)
export interface AutocompleteEntity {
  id: string;
  name: string;
  type?: string;
  team?: string;
  [key: string]: string | undefined;
}
