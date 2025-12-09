/**
 * React hook for fetching entity data with caching and enhancement support.
 * 
 * Features:
 * - Instant display of cached data
 * - Support for basic, enhanced, and full data tiers
 * - Background refresh when stale
 * - Loading states for fresh fetches
 */
import { useState, useEffect, useCallback, useRef } from 'react';
import { getEntity, EntityResponse, GetEntityOptions } from '../api';
import { getCached } from '../cache';
import { useSportContext } from '../../../context/SportContext';

export interface UseEntityOptions {
  entityType: 'player' | 'team';
  entityId: string;
  /** Include widget display data (default: true) */
  includeWidget?: boolean;
  /** Include news articles (default: true for MentionsPage) */
  includeNews?: boolean;
  /** Include API-Sports enhanced data like photos (default: false) */
  includeEnhanced?: boolean;
  /** Include API-Sports statistics (default: false) */
  includeStats?: boolean;
  /** Enable/disable the hook */
  enabled?: boolean;
}

export interface UseEntityResult {
  data: EntityResponse | null;
  isLoading: boolean;
  isFetching: boolean;
  error: Error | null;
  refetch: (forceRefresh?: boolean) => void;
}

export function useEntity({
  entityType,
  entityId,
  includeWidget = true,
  includeNews = true,
  includeEnhanced = false,
  includeStats = false,
  enabled = true,
}: UseEntityOptions): UseEntityResult {
  const { activeSport } = useSportContext();
  const [data, setData] = useState<EntityResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isFetching, setIsFetching] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const mountedRef = useRef(true);

  const includes = [
    ...(includeWidget ? ['widget'] : []),
    ...(includeNews ? ['news'] : []),
    ...(includeEnhanced ? ['enhanced'] : []),
    ...(includeStats ? ['stats'] : []),
  ];

  const fetch = useCallback(async (forceRefresh = false) => {
    if (!enabled || !entityType || !entityId) {
      return;
    }

    // Check cache first (unless refreshing)
    if (!forceRefresh) {
      const cached = getCached(entityType, entityId, activeSport, includes);
      if (cached) {
        setData(cached);
        setIsLoading(false);
        setIsFetching(true);  // Still fetch in background
      } else {
        setIsLoading(true);
      }
    } else {
      setIsLoading(true);
    }

    setError(null);

    try {
      const options: GetEntityOptions = {
        includeWidget,
        includeNews,
        includeEnhanced,
        includeStats,
        refresh: forceRefresh,
        skipCache: forceRefresh,
      };
      
      const result = await getEntity(entityType, entityId, activeSport, options);
      
      if (mountedRef.current) {
        setData(result);
      }
    } catch (e) {
      if (mountedRef.current) {
        setError(e instanceof Error ? e : new Error('Failed to fetch entity'));
      }
    } finally {
      if (mountedRef.current) {
        setIsLoading(false);
        setIsFetching(false);
      }
    }
  }, [entityType, entityId, activeSport, includeWidget, includeNews, includeEnhanced, includeStats, enabled]);

  // Initial fetch
  useEffect(() => {
    mountedRef.current = true;
    fetch();
    return () => {
      mountedRef.current = false;
    };
  }, [fetch]);

  const refetch = useCallback((forceRefresh = false) => {
    fetch(forceRefresh);
  }, [fetch]);

  return {
    data,
    isLoading,
    isFetching,
    error,
    refetch,
  };
}

/**
 * Hook for fetching enhanced entity data (includes API-Sports profile)
 */
export function useEnhancedEntity(
  entityType: 'player' | 'team',
  entityId: string,
  options: Partial<UseEntityOptions> = {}
) {
  return useEntity({
    entityType,
    entityId,
    includeEnhanced: true,
    includeNews: false,
    ...options,
  });
}

/**
 * Hook for fetching full entity data (enhanced + stats + news)
 */
export function useFullEntity(
  entityType: 'player' | 'team',
  entityId: string,
  options: Partial<UseEntityOptions> = {}
) {
  return useEntity({
    entityType,
    entityId,
    includeEnhanced: true,
    includeStats: true,
    includeNews: true,
    ...options,
  });
}

export default useEntity;
