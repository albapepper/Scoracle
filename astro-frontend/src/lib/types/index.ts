/**
 * Scoracle Type Definitions
 * 
 * These types match the backend API response schemas from:
 * - backend/app/routers/widgets.py - GET /api/v1/widget/{type}/{id}?sport=X
 * - backend/app/routers/news.py - GET /api/v1/news/{entity_name}
 */

// Entity Types
export type EntityType = 'player' | 'team';
export type SportId = 'NBA' | 'NFL' | 'FOOTBALL';

// News article from Google News RSS
export interface NewsArticle {
  title: string;
  link: string;
  pub_date: string | null;
  source: string;
}

// News response from GET /api/v1/news/{entity_name}
export interface NewsData {
  query: string;
  hours: number;
  count: number;
  articles: NewsArticle[];
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
