/**
 * Data Sources — Multi-Backend Abstraction Layer
 *
 * Routes data requests to the correct backend service:
 * - PostgREST: stats, percentiles, profiles (future)
 * - Go API: news, twitter (future)
 * - FastAPI: fallback for all endpoints until Go/PostgREST are stable
 *
 * On the server (SSR), uses private Railway network URLs.
 * On the client, uses public URLs.
 *
 * To swap a data source from FastAPI to PostgREST/Go:
 * 1. Update the relevant fetch function below
 * 2. Add any response shape transformation needed
 * 3. The rest of the app remains unchanged
 */

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
  profile: 'fastapi',     // Future: 'postgrest' or 'go'
  stats: 'fastapi',       // Future: 'postgrest'
  news: 'fastapi',        // Future: 'go'
  twitter: 'fastapi',     // Future: 'go'
  similarity: 'fastapi',  // Future: 'postgrest' or 'go'
  vibe: 'fastapi',        // ML — stays on FastAPI or migrates to Go
  momentum: 'fastapi',    // Future: 'postgrest'
};

// ─── URL Resolution ──────────────────────────────────────────────────────────

/**
 * Get the base URL for a backend source.
 *
 * Server-side (SSR): uses private Railway internal URLs for zero-latency calls.
 * Client-side: uses public URLs.
 *
 * import.meta.env.SSR is an Astro built-in that is true during SSR rendering
 * and false in client <script> blocks.
 */
export function getBaseUrl(source: BackendSource): string {
  const isServer = typeof window === 'undefined';

  switch (source) {
    case 'fastapi':
      if (isServer) {
        // Server: prefer private network URL, fall back to public
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
          || 'http://localhost:8080';
      }
      return import.meta.env.PUBLIC_GO_API_URL || 'http://localhost:8080';
  }
}

// ─── URL Builders ────────────────────────────────────────────────────────────

/**
 * Build the full URL for a profile request.
 */
export function profileUrl(sport: string, type: string, id: string): string {
  const source = DATA_SOURCES.profile;
  const base = getBaseUrl(source);

  switch (source) {
    case 'postgrest':
      // PostgREST: GET /rpc/entity_profile?sport=NBA&entity_type=player&entity_id=123
      return `${base}/rpc/entity_profile?sport=${sport.toUpperCase()}&entity_type=${type}&entity_id=${id}`;
    case 'go':
      return `${base}/api/v1/profile/${type}/${id}?sport=${sport.toUpperCase()}`;
    case 'fastapi':
    default:
      return `${base}/profile/${type}/${id}?sport=${sport.toUpperCase()}`;
  }
}

/**
 * Build the full URL for a stats request.
 */
export function statsUrl(sport: string, type: string, id: string): string {
  const source = DATA_SOURCES.stats;
  const base = getBaseUrl(source);

  switch (source) {
    case 'postgrest':
      // PostgREST: GET /rpc/entity_stats?sport=NBA&entity_type=player&entity_id=123
      return `${base}/rpc/entity_stats?sport=${sport.toUpperCase()}&entity_type=${type}&entity_id=${id}`;
    case 'fastapi':
    default:
      return `${base}/stats/${type}/${id}?sport=${sport.toUpperCase()}`;
  }
}

/**
 * Build the full URL for a news request.
 */
export function newsUrl(sport: string, type: string, id: string): string {
  const source = DATA_SOURCES.news;
  const base = getBaseUrl(source);

  switch (source) {
    case 'go':
      return `${base}/api/v1/news/${type}/${id}?sport=${sport.toUpperCase()}`;
    case 'fastapi':
    default:
      return `${base}/news/${type}/${id}?sport=${sport.toUpperCase()}`;
  }
}

/**
 * Build the full URL for a twitter status check.
 */
export function twitterStatusUrl(): string {
  const source = DATA_SOURCES.twitter;
  const base = getBaseUrl(source);

  switch (source) {
    case 'go':
      return `${base}/api/v1/twitter/status`;
    case 'fastapi':
    default:
      return `${base}/twitter/status`;
  }
}

/**
 * Build the full URL for a twitter feed.
 */
export function twitterFeedUrl(query: string): string {
  const source = DATA_SOURCES.twitter;
  const base = getBaseUrl(source);

  switch (source) {
    case 'go':
      return `${base}/api/v1/twitter/journalist-feed?q=${encodeURIComponent(query)}`;
    case 'fastapi':
    default:
      return `${base}/twitter/journalist-feed?q=${encodeURIComponent(query)}`;
  }
}

/**
 * Build the full URL for a similarity request.
 */
export function similarityUrl(sport: string, type: string, id: string): string {
  const source = DATA_SOURCES.similarity;
  const base = getBaseUrl(source);

  switch (source) {
    case 'postgrest':
      return `${base}/rpc/similar_entities?sport=${sport.toUpperCase()}&entity_type=${type}&entity_id=${id}`;
    case 'fastapi':
    default:
      return `${base}/similarity/${type}/${id}?sport=${sport.toUpperCase()}`;
  }
}

/**
 * Build the full URL for a vibe request.
 */
export function vibeUrl(sport: string, type: string, id: string): string {
  const source = DATA_SOURCES.vibe;
  const base = getBaseUrl(source);

  // Vibe is ML — always FastAPI-shaped for now
  return `${base}/ml/vibe/${type}/${id}?sport=${sport.toUpperCase()}`;
}

/**
 * Build the full URL for transfer predictions.
 */
export function transfersUrl(id: string): string {
  const source = DATA_SOURCES.vibe; // Same source as ML endpoints
  const base = getBaseUrl(source);
  return `${base}/ml/transfers/predictions/${id}`;
}
