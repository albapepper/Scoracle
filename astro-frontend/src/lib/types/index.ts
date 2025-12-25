/**
 * Scoracle Type Definitions
 *
 * CENTRAL SPORT CONFIGURATION - All sport definitions live here.
 * Import from this file instead of hardcoding sport values elsewhere.
 *
 * To add a new sport:
 * 1. Add to SportId type
 * 2. Add to SPORTS array below
 * 3. Add JSON data file to /public/data/{id}.json
 * 4. Update backend config.py with API-Sports settings
 */

// Entity Types
export type EntityType = 'player' | 'team';
export type SportId = 'NBA' | 'NFL' | 'FOOTBALL';

// Sport Configuration - SINGLE SOURCE OF TRUTH
export interface SportConfig {
  id: SportId;
  idLower: string;        // Lowercase version for URLs/files
  display: string;        // Display name
  logo: string;           // Logo path
  dataFile: string;       // Path to JSON data file
}

export const SPORTS: readonly SportConfig[] = [
  { id: 'NBA', idLower: 'nba', display: 'NBA', logo: '/NBA logo.png', dataFile: '/data/nba.json' },
  { id: 'NFL', idLower: 'nfl', display: 'NFL', logo: '/NFL logo.png', dataFile: '/data/nfl.json' },
  { id: 'FOOTBALL', idLower: 'football', display: 'Football', logo: '/fifa logo.png', dataFile: '/data/football.json' },
] as const;

// Helper functions for sport lookups
export function getSportById(id: string): SportConfig | undefined {
  const normalized = id.toUpperCase();
  return SPORTS.find(s => s.id === normalized);
}

export function getSportByIdLower(idLower: string): SportConfig | undefined {
  const normalized = idLower.toLowerCase();
  return SPORTS.find(s => s.idLower === normalized);
}

export function getSportDisplay(sportId: string): string {
  const sport = getSportById(sportId) || getSportByIdLower(sportId);
  return sport?.display || sportId.toUpperCase();
}

export function getValidSportIds(): SportId[] {
  return SPORTS.map(s => s.id);
}

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

// Autocomplete Types (for client-side search from bundled JSON)
export interface AutocompleteEntity {
  id: string;
  name: string;
  type: 'player' | 'team';
  team?: string;
}
