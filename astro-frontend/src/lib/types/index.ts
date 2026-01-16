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
  sport?: string | null;
  team?: string | null;
  hours: number;
  hours_requested?: number;
  extended?: boolean;
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

// ============================================
// ML API Types
// ============================================

// --- Transfer Types ---

/** Team transfer predictions from GET /api/v1/ml/transfers/predictions/{team_id} */
export interface TeamTransferPredictions {
  team_id: number;
  team_name: string;
  sport: string;
  transfer_window: string;
  predictions: TransferTarget[];
  last_updated: string;
}

export interface TransferTarget {
  player_id: number;
  player_name: string;
  current_team: string;
  probability: number;
  confidence_interval: [number, number];
  trend: 'up' | 'down' | 'stable';
  trend_change_7d: number;
  top_factors: string[];
  recent_headlines: string[];
}

/** Player transfer links from GET /api/v1/ml/transfers/predictions/player/{player_id} */
export interface PlayerTransferLinks {
  player_id: number;
  player_name: string;
  current_team: string;
  sport: string;
  linked_teams: LinkedTeam[];
  last_updated: string;
}

export interface LinkedTeam {
  team_id: number;
  team_name: string;
  probability: number;
  confidence_interval: [number, number];
  trend: 'up' | 'down' | 'stable';
}

/** Trending transfers from GET /api/v1/ml/transfers/trending */
export interface TrendingTransfers {
  sport: string;
  transfers: TrendingTransfer[];
  last_updated: string;
}

export interface TrendingTransfer {
  player_name: string;
  current_team: string;
  linked_team: string;
  probability: number;
  trend: 'up' | 'down' | 'stable';
  mention_count_24h: number;
  top_source: string;
}

// --- Vibe Types ---

/** Vibe score from GET /api/v1/ml/vibe/{entity_type}/{entity_id} */
export interface VibeScoreResponse {
  entity_id: number;
  entity_name: string;
  entity_type: EntityType;
  sport: string;
  vibe_score: number;
  vibe_label: string;
  breakdown: VibeBreakdown;
  trend: VibeTrend;
  themes: Record<string, number>;
  last_updated: string;
}

export interface VibeBreakdown {
  twitter?: number;
  news?: number;
  reddit?: number;
}

export interface VibeTrend {
  direction: 'up' | 'down' | 'stable';
  change_7d: number;
  change_30d: number;
}

/** Trending vibes from GET /api/v1/ml/vibe/trending/{sport} */
export interface TrendingVibes {
  sport: string;
  trending: TrendingVibe[];
  last_updated: string;
}

export interface TrendingVibe {
  entity_id: number;
  entity_name: string;
  entity_type: EntityType;
  current_score: number;
  change_7d: number;
  direction: 'up' | 'down' | 'stable';
}

// --- Similarity Types ---

/** Similar entities from GET /api/v1/ml/similar/{entity_type}/{entity_id} */
export interface SimilarityResponse {
  entity_id: number;
  entity_name: string;
  entity_type: EntityType;
  sport: string;
  similar_entities: SimilarEntity[];
}

export interface SimilarEntity {
  entity_id: number;
  entity_name: string;
  entity_type: EntityType;
  similarity_score: number;
  team?: string;
  position?: string;
}

/** Similarity comparison from GET /api/v1/ml/similar/compare/{entity_type}/{id1}/{id2} */
export interface SimilarityComparison {
  entity_1: { id: number; name: string };
  entity_2: { id: number; name: string };
  similarity_score: number;
  shared_traits: string[];
  key_differences: string[];
}

// --- Prediction Types ---

/** Game prediction from GET /api/v1/ml/predictions/{entity_type}/{entity_id}/next */
export interface GamePredictionResponse {
  entity_id: number;
  entity_name: string;
  entity_type: EntityType;
  opponent_id: number;
  opponent_name: string;
  game_date: string;
  sport: string;
  predictions: Record<string, StatPrediction>;
  confidence_score: number;
  context_factors: string[];
  key_factors: string[];
  model_version: string;
  last_updated: string;
}

export interface StatPrediction {
  stat_name: string;
  predicted_value: number;
  confidence_lower: number;
  confidence_upper: number;
  historical_avg: number;
}

/** Model accuracy from GET /api/v1/ml/predictions/accuracy/{model_version} */
export interface ModelAccuracy {
  model_type: string;
  model_version: string;
  sport: string;
  metrics: Record<string, number>;
  sample_size: number;
  period_start: string;
  period_end: string;
}
