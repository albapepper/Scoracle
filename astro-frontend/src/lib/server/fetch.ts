/**
 * Server-Side Fetch Utilities
 *
 * Used ONLY in Astro frontmatter (server context) for SSR pages.
 * Fetches data over Railway's private network during server rendering.
 *
 * DO NOT import this file from client-side <script> blocks.
 * Astro's tree-shaking ensures this code never reaches the browser
 * when imported only in frontmatter.
 *
 * These functions return the same data shapes as the client-side API,
 * so components can work with the data regardless of where it was fetched.
 */

import { profileUrl, statsUrl, newsUrl } from '../utils/data-sources';

// ─── Types ───────────────────────────────────────────────────────────────────

/** Player profile shape from backend */
export interface PlayerProfileData {
  id: number;
  first_name?: string;
  last_name?: string;
  full_name?: string;
  position?: string;
  photo_url?: string;
  jersey_number?: number;
  height_inches?: number;
  weight_lbs?: number;
  college?: string;
  experience_years?: number;
  nationality?: string;
  birth_date?: string;
  birth_country?: string;
  team?: {
    id: number;
    name: string;
    logo_url?: string;
  };
}

/** Team profile shape from backend */
export interface TeamProfileData {
  id: number;
  name?: string;
  full_name?: string;
  abbreviation?: string;
  logo_url?: string;
  city?: string;
  country?: string;
  venue_name?: string;
  venue_capacity?: number;
  founded?: number;
  league?: {
    id: number;
    name: string;
    country: string;
  };
}

/** Stats response shape from backend */
export interface StatsResponse {
  entity_id: number;
  entity_type: 'player' | 'team';
  sport: string;
  season: number;
  stats: Record<string, number | string>;
  percentiles: Record<string, number> | Array<{ stat_key: string; percentile: number }>;
  percentile_metadata?: unknown;
}

/** News response shape from backend */
export interface NewsResponse {
  query: string;
  sport?: string | null;
  team?: string | null;
  hours: number;
  hours_requested?: number;
  extended?: boolean;
  count: number;
  articles: Array<{
    title: string;
    url: string;
    published_at: string | null;
    source: string;
    description?: string;
    image_url?: string | null;
  }>;
}

/** Wrapper for SSR fetch results */
export interface SSRFetchResult<T> {
  data: T | null;
  error: string | null;
}

// ─── Server Fetch with timeout ───────────────────────────────────────────────

const DEFAULT_TIMEOUT = 5000; // 5 seconds

async function serverFetch<T>(url: string, timeout = DEFAULT_TIMEOUT): Promise<SSRFetchResult<T>> {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    const response = await fetch(url, {
      signal: controller.signal,
      headers: {
        'Accept': 'application/json',
      },
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      return { data: null, error: `HTTP ${response.status}: ${response.statusText}` };
    }

    const data = await response.json() as T;
    return { data, error: null };
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Unknown error';
    return { data: null, error: message };
  }
}

// ─── Public API ──────────────────────────────────────────────────────────────

/**
 * Fetch entity profile server-side (over private network in production).
 */
export async function fetchProfile(
  sport: string,
  type: string,
  id: string
): Promise<SSRFetchResult<PlayerProfileData | TeamProfileData>> {
  const url = profileUrl(sport, type, id);
  return serverFetch(url);
}

/**
 * Fetch entity stats server-side.
 */
export async function fetchStats(
  sport: string,
  type: string,
  id: string
): Promise<SSRFetchResult<StatsResponse>> {
  const url = statsUrl(sport, type, id);
  return serverFetch(url);
}

/**
 * Fetch entity news server-side.
 */
export async function fetchNews(
  sport: string,
  type: string,
  id: string
): Promise<SSRFetchResult<NewsResponse>> {
  const url = newsUrl(sport, type, id);
  return serverFetch(url);
}

/**
 * Fetch profile + stats in parallel for a stats page SSR.
 * Returns both results, individually error-handled.
 */
export async function fetchStatsPageData(
  sport: string,
  type: string,
  id: string
): Promise<{
  profile: SSRFetchResult<PlayerProfileData | TeamProfileData>;
  stats: SSRFetchResult<StatsResponse>;
}> {
  const [profile, stats] = await Promise.all([
    fetchProfile(sport, type, id),
    fetchStats(sport, type, id),
  ]);

  return { profile, stats };
}

/**
 * Fetch profile + news in parallel for a news page SSR.
 * Returns both results, individually error-handled.
 */
export async function fetchNewsPageData(
  sport: string,
  type: string,
  id: string
): Promise<{
  profile: SSRFetchResult<PlayerProfileData | TeamProfileData>;
  news: SSRFetchResult<NewsResponse>;
}> {
  const [profile, news] = await Promise.all([
    fetchProfile(sport, type, id),
    fetchNews(sport, type, id),
  ]);

  return { profile, news };
}
