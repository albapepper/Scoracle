/**
 * Adapters Index
 *
 * Central export for all API response adapters.
 * Import from here for clean imports:
 *
 * ```typescript
 * import {
 *   normalizeProfileResponse,
 *   isValidProfileResponse,
 *   normalizeStatsResponse,
 *   isValidStatsResponse,
 * } from '../lib/adapters';
 * ```
 *
 * This adapter layer is the SINGLE POINT OF CHANGE when backend response
 * formats change (e.g., during database migrations).
 */

// Types
export type {
  RawProfileResponse,
  NormalizedProfileResponse,
  RawStatsResponse,
  NormalizedStatsResponse,
  TeamInfo,
  LeagueInfo,
  EntityType,
} from './types';

// Profile adapter
export {
  isValidProfileResponse,
  normalizeProfileResponse,
  getProfileDisplayName,
} from './profile-adapter';

// Stats adapter
export {
  isValidStatsResponse,
  normalizeStatsResponse,
  getStatValue,
  getStatPercentile,
} from './stats-adapter';
