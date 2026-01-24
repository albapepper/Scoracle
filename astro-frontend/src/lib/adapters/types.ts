/**
 * Adapter Types
 *
 * Shared type definitions for API response adapters.
 * This is the SINGLE SOURCE OF TRUTH for data shapes between backend and frontend.
 *
 * When the backend response format changes (e.g., database migration),
 * update the Raw* types here. The Normalized* types should remain stable
 * as they represent what the frontend components expect.
 */

// =============================================================================
// Profile Types
// =============================================================================

/**
 * Team info nested in profile responses
 */
export interface TeamInfo {
  id: number;
  name: string;
  abbreviation?: string;
  logo_url?: string;
  conference?: string;
  division?: string;
  country?: string;
  city?: string;
}

/**
 * League info nested in profile responses (FOOTBALL)
 */
export interface LeagueInfo {
  id: number;
  name: string;
  country: string;
  logo_url: string | null;
}

/**
 * Raw profile response from backend (flat structure)
 * This matches what the /profile/ endpoint returns directly.
 */
export interface RawProfileResponse {
  id: number;
  sport_id?: string;
  first_name?: string;
  last_name?: string;
  full_name?: string;
  name?: string; // For teams
  position?: string;
  position_group?: string;
  nationality?: string;
  birth_date?: string;
  birth_place?: string;
  birth_country?: string;
  height_inches?: number;
  weight_lbs?: number;
  photo_url?: string;
  logo_url?: string; // For teams
  current_team_id?: number;
  current_league_id?: number;
  jersey_number?: number;
  college?: string;
  experience_years?: number;
  is_active?: boolean;
  team?: TeamInfo;
  league?: LeagueInfo;
  // Team-specific fields
  league_id?: number;
  abbreviation?: string;
  venue_name?: string;
  venue_address?: string;
  venue_capacity?: number;
  venue_city?: string;
  venue_surface?: string;
  venue_image?: string;
  founded?: number;
  is_national?: boolean;
  country?: string;
  city?: string;
}

/**
 * Normalized profile response (what components expect)
 * This wraps the raw data with metadata for consistent handling.
 */
export interface NormalizedProfileResponse {
  entity_id: number;
  entity_type: 'player' | 'team';
  sport: string;
  info: RawProfileResponse;
}

// =============================================================================
// Stats Types
// =============================================================================

/**
 * Raw stats response from backend
 * This matches what the /stats/ endpoint returns.
 */
export interface RawStatsResponse {
  entity_id: number;
  entity_type: 'player' | 'team';
  sport: string;
  season: number;
  stats: Record<string, unknown>;
  percentiles: Record<string, number> | Array<{ stat_key: string; percentile: number }>;
  percentile_metadata: unknown | null;
  league_id?: number;
}

/**
 * Normalized stats response (what components expect)
 * Percentiles are always normalized to an object format.
 */
export interface NormalizedStatsResponse {
  entity_id: number;
  entity_type: 'player' | 'team';
  sport: string;
  season: number;
  stats: Record<string, unknown>;
  percentiles: Record<string, number>;
}

// =============================================================================
// Utility Types
// =============================================================================

export type EntityType = 'player' | 'team';
