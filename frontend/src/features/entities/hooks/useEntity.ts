/**
 * React hook for fetching entity data.
 * 
 * Fetches entity info, widget data, and news in one call.
 */
import { useState, useEffect, useCallback } from 'react';
import { getEntity, EntityResponse } from '../api';
import { useSportContext } from '../../../context/SportContext';

export interface UseEntityOptions {
  entityType: 'player' | 'team';
  entityId: string;
  includeWidget?: boolean;
  includeNews?: boolean;
  enabled?: boolean;
}

export interface UseEntityResult {
  data: EntityResponse | null;
  isLoading: boolean;
  error: Error | null;
  refetch: () => void;
}

export function useEntity({
  entityType,
  entityId,
  includeWidget = true,
  includeNews = true,
  enabled = true,
}: UseEntityOptions): UseEntityResult {
  const { activeSport } = useSportContext();
  const [data, setData] = useState<EntityResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const fetch = useCallback(async () => {
    if (!enabled || !entityType || !entityId) {
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const result = await getEntity(entityType, entityId, activeSport, {
        includeWidget,
        includeNews,
      });
      setData(result);
    } catch (e) {
      setError(e instanceof Error ? e : new Error('Failed to fetch entity'));
    } finally {
      setIsLoading(false);
    }
  }, [entityType, entityId, activeSport, includeWidget, includeNews, enabled]);

  useEffect(() => {
    fetch();
  }, [fetch]);

  return {
    data,
    isLoading,
    error,
    refetch: fetch,
  };
}

export default useEntity;

