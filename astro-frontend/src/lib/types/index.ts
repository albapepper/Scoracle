// Entity Types
export type EntityType = 'player' | 'team';
export type SportId = 'nba' | 'nfl' | 'football';

export interface EntityInfo {
  id: string;
  name: string;
  type: EntityType;
  sport?: SportId;
}

export interface WidgetData {
  type: EntityType;
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

// Sport Configuration
export interface SportConfig {
  id: SportId;
  display: string;
  icon?: string;
}

export const SPORTS: readonly SportConfig[] = [
  { id: 'nba', display: 'NBA' },
  { id: 'nfl', display: 'NFL' },
  { id: 'football', display: 'Football' },
] as const;

// Autocomplete Types
export interface AutocompleteEntity {
  id: string;
  name: string;
  type?: string;
  team?: string;
  [key: string]: string | undefined;
}
