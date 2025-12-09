/**
 * Entity Cache - Frontend in-memory caching for entity data.
 * 
 * Provides instant responses on re-navigation without API calls.
 * Works alongside browser HTTP caching for multi-layer performance.
 */

import type { EntityResponse } from './api';

interface CacheEntry {
  data: EntityResponse;
  timestamp: number;
  expiresAt: number;
}

// Cache configuration
const CACHE_TTL_MS = 5 * 60 * 1000;  // 5 minutes (matches backend)
const MAX_CACHE_SIZE = 50;            // Max entries to prevent memory bloat

// In-memory cache
const cache = new Map<string, CacheEntry>();

/**
 * Build cache key from entity parameters
 */
function buildKey(entityType: string, entityId: string, sport: string, includes: string[]): string {
  return `${entityType}:${entityId}:${sport.toUpperCase()}:${includes.sort().join(',')}`;
}

/**
 * Get cached entity response
 */
export function getCached(
  entityType: string,
  entityId: string,
  sport: string,
  includes: string[] = ['widget', 'news']
): EntityResponse | null {
  const key = buildKey(entityType, entityId, sport, includes);
  const entry = cache.get(key);
  
  if (!entry) {
    return null;
  }
  
  // Check if expired
  if (Date.now() > entry.expiresAt) {
    cache.delete(key);
    return null;
  }
  
  return entry.data;
}

/**
 * Store entity response in cache
 */
export function setCache(
  entityType: string,
  entityId: string,
  sport: string,
  includes: string[],
  data: EntityResponse
): void {
  const key = buildKey(entityType, entityId, sport, includes);
  
  // Evict oldest entries if cache is full
  if (cache.size >= MAX_CACHE_SIZE) {
    const oldestKey = cache.keys().next().value;
    if (oldestKey) {
      cache.delete(oldestKey);
    }
  }
  
  cache.set(key, {
    data,
    timestamp: Date.now(),
    expiresAt: Date.now() + CACHE_TTL_MS,
  });
}

/**
 * Clear all cached entries
 */
export function clearCache(): void {
  cache.clear();
}

/**
 * Get cache statistics
 */
export function getCacheStats(): { size: number; maxSize: number } {
  return {
    size: cache.size,
    maxSize: MAX_CACHE_SIZE,
  };
}

