/**
 * API Fetcher with SWR (Stale-While-Revalidate) pattern
 *
 * Features:
 * - Request deduplication (prevents duplicate in-flight requests)
 * - SWR caching (serves stale data instantly, revalidates in background)
 * - Parallel fetching support
 * - TTL-based cache expiration
 */

interface CacheEntry<T> {
  data: T;
  timestamp: number;
  expiresAt: number;
}

interface FetcherOptions {
  /** Time in ms before data is considered stale (default: 60000 = 1 min) */
  staleTime?: number;
  /** Time in ms before cache entry is removed (default: 300000 = 5 min) */
  cacheTime?: number;
  /** Skip cache and force fresh fetch */
  forceRefresh?: boolean;
}

// In-memory cache store
const cache = new Map<string, CacheEntry<unknown>>();

// In-flight request tracking for deduplication
const inFlight = new Map<string, Promise<unknown>>();

// Default timings
const DEFAULT_STALE_TIME = 60 * 1000; // 1 minute
const DEFAULT_CACHE_TIME = 5 * 60 * 1000; // 5 minutes

/**
 * Fetch with SWR pattern
 * - Returns cached data immediately if available (even if stale)
 * - Revalidates in background if data is stale
 * - Deduplicates concurrent requests for the same URL
 */
export async function swrFetch<T>(
  url: string,
  options: FetcherOptions = {}
): Promise<{ data: T; isStale: boolean; fromCache: boolean }> {
  const {
    staleTime = DEFAULT_STALE_TIME,
    cacheTime = DEFAULT_CACHE_TIME,
    forceRefresh = false,
  } = options;

  const now = Date.now();
  const cacheKey = url;

  // Check cache first
  const cached = cache.get(cacheKey) as CacheEntry<T> | undefined;

  if (cached && !forceRefresh) {
    const isExpired = now > cached.expiresAt;
    const isStale = now > cached.timestamp + staleTime;

    // If not expired, return cached data
    if (!isExpired) {
      // If stale, trigger background revalidation
      if (isStale) {
        revalidate<T>(url, cacheTime);
      }
      return { data: cached.data, isStale, fromCache: true };
    }
  }

  // No valid cache, fetch fresh data
  const data = await dedupedFetch<T>(url, cacheTime);
  return { data, isStale: false, fromCache: false };
}

/**
 * Fetch that deduplicates concurrent requests
 */
async function dedupedFetch<T>(url: string, cacheTime: number): Promise<T> {
  // Check if request is already in-flight
  const existing = inFlight.get(url);
  if (existing) {
    return existing as Promise<T>;
  }

  // Create new fetch promise
  const fetchPromise = (async () => {
    try {
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const data = await response.json();

      // Store in cache
      const now = Date.now();
      cache.set(url, {
        data,
        timestamp: now,
        expiresAt: now + cacheTime,
      });

      return data as T;
    } finally {
      // Remove from in-flight tracking
      inFlight.delete(url);
    }
  })();

  // Track in-flight request
  inFlight.set(url, fetchPromise);

  return fetchPromise;
}

/**
 * Background revalidation (fire and forget)
 */
function revalidate<T>(url: string, cacheTime: number): void {
  // Don't revalidate if already in-flight
  if (inFlight.has(url)) return;

  dedupedFetch<T>(url, cacheTime).catch(() => {
    // Silently fail background revalidation
  });
}

/**
 * Fetch multiple URLs in parallel with SWR
 */
export async function swrFetchAll<T extends Record<string, string>>(
  urls: T,
  options: FetcherOptions = {}
): Promise<{ [K in keyof T]: { data: unknown; isStale: boolean; fromCache: boolean } }> {
  const entries = Object.entries(urls);
  const results = await Promise.all(
    entries.map(([, url]) => swrFetch(url, options))
  );

  return Object.fromEntries(
    entries.map(([key], index) => [key, results[index]])
  ) as { [K in keyof T]: { data: unknown; isStale: boolean; fromCache: boolean } };
}

/**
 * Simple parallel fetch without SWR (just deduplication)
 */
export async function fetchParallel<T extends Record<string, string>>(
  urls: T,
  cacheTime = DEFAULT_CACHE_TIME
): Promise<{ [K in keyof T]: unknown }> {
  const entries = Object.entries(urls);
  const results = await Promise.all(
    entries.map(([, url]) => dedupedFetch(url, cacheTime))
  );

  return Object.fromEntries(
    entries.map(([key], index) => [key, results[index]])
  ) as { [K in keyof T]: unknown };
}

/**
 * Pre-warm cache for anticipated requests
 */
export function prefetch(url: string, cacheTime = DEFAULT_CACHE_TIME): void {
  // Don't prefetch if already cached or in-flight
  if (cache.has(url) || inFlight.has(url)) return;

  dedupedFetch(url, cacheTime).catch(() => {
    // Silently fail prefetch
  });
}

/**
 * Clear cache (useful for testing or manual refresh)
 */
export function clearCache(): void {
  cache.clear();
}

/**
 * Get cache stats (useful for debugging)
 */
export function getCacheStats(): { size: number; inFlight: number } {
  return {
    size: cache.size,
    inFlight: inFlight.size,
  };
}

// Page-level data store for sharing between components
interface PageData {
  widget?: unknown;
  news?: unknown;
  stats?: unknown;
}

const pageDataStore: PageData = {};
const pageDataCallbacks: Map<keyof PageData, Array<(data: unknown) => void>> = new Map();

/**
 * Store page-level data for sharing between components
 */
export function setPageData<K extends keyof PageData>(key: K, data: PageData[K]): void {
  pageDataStore[key] = data;

  // Notify any waiting callbacks
  const callbacks = pageDataCallbacks.get(key);
  if (callbacks) {
    callbacks.forEach(cb => cb(data));
    pageDataCallbacks.delete(key);
  }
}

/**
 * Get page-level data, optionally waiting for it
 */
export function getPageData<K extends keyof PageData>(key: K): PageData[K] | undefined {
  return pageDataStore[key];
}

/**
 * Wait for page-level data to be available
 */
export function waitForPageData<K extends keyof PageData>(
  key: K,
  timeout = 5000
): Promise<PageData[K]> {
  // If data already exists, return immediately
  if (pageDataStore[key] !== undefined) {
    return Promise.resolve(pageDataStore[key] as PageData[K]);
  }

  // Wait for data with timeout
  return new Promise((resolve, reject) => {
    const timeoutId = setTimeout(() => {
      const callbacks = pageDataCallbacks.get(key);
      if (callbacks) {
        const index = callbacks.indexOf(callback);
        if (index > -1) callbacks.splice(index, 1);
      }
      reject(new Error(`Timeout waiting for ${key} data`));
    }, timeout);

    const callback = (data: unknown) => {
      clearTimeout(timeoutId);
      resolve(data as PageData[K]);
    };

    if (!pageDataCallbacks.has(key)) {
      pageDataCallbacks.set(key, []);
    }
    pageDataCallbacks.get(key)!.push(callback);
  });
}

/**
 * Clear page-level data (call on navigation)
 */
export function clearPageData(): void {
  Object.keys(pageDataStore).forEach(key => {
    delete pageDataStore[key as keyof PageData];
  });
  pageDataCallbacks.clear();
}
