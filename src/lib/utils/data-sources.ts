/**
 * Data Sources — Multi-Backend Abstraction Layer
 *
 * Routes data requests to the correct backend service:
 * - PostgREST: profiles, stats (via Accept-Profile header per sport schema)
 * - Go API: news, twitter
 * - FastAPI: ML endpoints (vibe, predictions, transfers), similarity
 *
 * On the server (SSR), uses private Railway network URLs.
 * On the client, uses public URLs (PUBLIC_* env vars are inlined by Vite).
 *
 * Each URL builder returns a FetchTarget { url, headers } so callers
 * get both the endpoint and any required headers (e.g. Accept-Profile)
 * in a single call.
 */

import { getCurrentSeason } from './season';

// ─── Backend Source Types ────────────────────────────────────────────────────

export type BackendSource = 'fastapi' | 'postgrest' | 'go';

export interface DataSourceConfig {
  /** Which backend serves each data type */
  profile: BackendSource;
  stats: BackendSource;
  news: BackendSource;
  twitter: BackendSource;
  similarity: BackendSource;
  vibe: BackendSource;
  momentum: BackendSource;
}

/**
 * Current routing configuration.
 * Change individual entries as backends become available.
 */
export const DATA_SOURCES: DataSourceConfig = {
  profile: 'postgrest',   // PostgREST via Accept-Profile header
  stats: 'postgrest',     // PostgREST via Accept-Profile header
  news: 'go',             // Go API
  twitter: 'go',          // Go API
  similarity: 'fastapi',  // No PostgREST view yet
  vibe: 'fastapi',        // ML — stays on FastAPI
  momentum: 'fastapi',    // Future: 'postgrest'
};

// ─── FetchTarget ─────────────────────────────────────────────────────────────

/**
 * A fully-resolved fetch target: the URL to call plus any headers
 * required by the backend (e.g. Accept-Profile for PostgREST).
 */
export interface FetchTarget {
  url: string;
  headers: Record<string, string>;
}

// ─── URL Resolution ──────────────────────────────────────────────────────────

/**
 * Get the base URL for a backend source.
 *
 * Server-side (SSR): uses private Railway internal URLs for zero-latency calls.
 * Client-side: uses public URLs (PUBLIC_* vars inlined by Vite at build time).
 */
export function getBaseUrl(source: BackendSource): string {
  const isServer = typeof window === 'undefined';

  switch (source) {
    case 'fastapi':
      if (isServer) {
        return import.meta.env.FASTAPI_INTERNAL_URL
          || import.meta.env.PUBLIC_API_URL
          || 'http://localhost:8000/api/v1';
      }
      return import.meta.env.PUBLIC_API_URL || 'http://localhost:8000/api/v1';

    case 'postgrest':
      if (isServer) {
        return import.meta.env.POSTGREST_INTERNAL_URL
          || import.meta.env.PUBLIC_POSTGREST_URL
          || 'http://localhost:3000';
      }
      return import.meta.env.PUBLIC_POSTGREST_URL || 'http://localhost:3000';

    case 'go':
      if (isServer) {
        return import.meta.env.GO_INTERNAL_URL
          || import.meta.env.PUBLIC_GO_API_URL
          || 'http://localhost:8080/api/v1';
      }
      return import.meta.env.PUBLIC_GO_API_URL || 'http://localhost:8080/api/v1';
  }
}

// ─── Header Helpers ──────────────────────────────────────────────────────────

/**
 * Build PostgREST headers for a sport schema.
 *
 * Accept-Profile selects the DB schema (nba, nfl, football).
 * application/vnd.pgrst.object+json returns a single object instead of an array
 * for endpoints that query by primary key.
 */
function postgrestHeaders(sport: string, singular: boolean = false): Record<string, string> {
  const headers: Record<string, string> = {
    'Accept-Profile': sport.toLowerCase(),
  };
  if (singular) {
    headers['Accept'] = 'application/vnd.pgrst.object+json';
  }
  return headers;
}

// ─── URL Builders ────────────────────────────────────────────────────────────

/**
 * Build the FetchTarget for a profile request.
 *
 * PostgREST: GET /players?id=eq.{id} or /teams?id=eq.{id}
 *   with Accept-Profile header for sport schema selection.
 */
export function profileUrl(sport: string, type: string, id: string): FetchTarget {
  const source = DATA_SOURCES.profile;
  const base = getBaseUrl(source);

  switch (source) {
    case 'postgrest': {
      const view = type === 'team' ? 'teams' : 'players';
      return {
        url: `${base}/${view}?id=eq.${id}`,
        headers: postgrestHeaders(sport, true),
      };
    }
    case 'go':
      return {
        url: `${base}/profile/${type}/${id}?sport=${sport.toUpperCase()}`,
        headers: {},
      };
    case 'fastapi':
    default:
      return {
        url: `${base}/profile/${type}/${id}?sport=${sport.toUpperCase()}`,
        headers: {},
      };
  }
}

/**
 * Build the FetchTarget for a stats request.
 *
 * PostgREST: GET /player_stats?player_id=eq.{id}&season=eq.{season}
 *            or  /team_stats?team_id=eq.{id}&season=eq.{season}
 *   with Accept-Profile header for sport schema selection.
 */
export function statsUrl(sport: string, type: string, id: string): FetchTarget {
  const source = DATA_SOURCES.stats;
  const base = getBaseUrl(source);

  switch (source) {
    case 'postgrest': {
      const season = getCurrentSeason(sport);
      if (type === 'team') {
        return {
          url: `${base}/team_stats?team_id=eq.${id}&season=eq.${season}`,
          headers: postgrestHeaders(sport, true),
        };
      }
      return {
        url: `${base}/player_stats?player_id=eq.${id}&season=eq.${season}`,
        headers: postgrestHeaders(sport, true),
      };
    }
    case 'fastapi':
    default:
      return {
        url: `${base}/stats/${type}/${id}?sport=${sport.toUpperCase()}`,
        headers: {},
      };
  }
}

/**
 * Build the FetchTarget for a news request.
 *
 * Go API: GET /news/{entityType}/{entityID}?sport={SPORT}
 *   Optionally includes limit param.
 */
export function newsUrl(sport: string, type: string, id: string, limit?: number): FetchTarget {
  const source = DATA_SOURCES.news;
  const base = getBaseUrl(source);

  const params = new URLSearchParams();
  params.set('sport', sport.toUpperCase());
  if (limit) params.set('limit', limit.toString());

  // Go and FastAPI share the same path structure
  return {
    url: `${base}/news/${type}/${id}?${params.toString()}`,
    headers: {},
  };
}

/**
 * Build the FetchTarget for a twitter status check.
 */
export function twitterStatusUrl(): FetchTarget {
  const source = DATA_SOURCES.twitter;
  const base = getBaseUrl(source);

  // Go and FastAPI share the same path structure
  return {
    url: `${base}/twitter/status`,
    headers: {},
  };
}

/**
 * Build the FetchTarget for a twitter journalist feed.
 *
 * Go API: GET /twitter/journalist-feed?q={query}&sport={SPORT}&limit={N}
 */
export function twitterFeedUrl(query: string, sport?: string, limit?: number): FetchTarget {
  const source = DATA_SOURCES.twitter;
  const base = getBaseUrl(source);

  const params = new URLSearchParams();
  params.set('q', encodeURIComponent(query));
  if (sport) params.set('sport', sport.toUpperCase());
  if (limit) params.set('limit', limit.toString());

  return {
    url: `${base}/twitter/journalist-feed?${params.toString()}`,
    headers: {},
  };
}

/**
 * Build the FetchTarget for a similarity request.
 * (Still on FastAPI — no PostgREST view exists yet.)
 */
export function similarityUrl(sport: string, type: string, id: string, season?: number, limit?: number): FetchTarget {
  const source = DATA_SOURCES.similarity;
  const base = getBaseUrl(source);

  const params = new URLSearchParams();
  params.set('sport', sport.toUpperCase());
  if (season) params.set('season', season.toString());
  if (limit) params.set('limit', limit.toString());

  return {
    url: `${base}/similarity/${type}/${id}?${params.toString()}`,
    headers: {},
  };
}

/**
 * Build the FetchTarget for a vibe request.
 * (ML — stays on FastAPI.)
 */
export function vibeUrl(sport: string, type: string, id: string): FetchTarget {
  const source = DATA_SOURCES.vibe;
  const base = getBaseUrl(source);

  return {
    url: `${base}/ml/vibe/${type}/${id}?sport=${sport.toUpperCase()}`,
    headers: {},
  };
}

/**
 * Build the FetchTarget for transfer predictions.
 * (ML — stays on FastAPI.)
 */
export function transfersUrl(id: string): FetchTarget {
  const source = DATA_SOURCES.vibe; // Same source as ML endpoints
  const base = getBaseUrl(source);

  return {
    url: `${base}/ml/transfers/predictions/${id}`,
    headers: {},
  };
}
