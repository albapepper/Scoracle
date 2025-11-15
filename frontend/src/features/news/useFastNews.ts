import React from 'react';
import { fetchFastNews, fetchFastNewsByEntity, FastNewsResponse, FastNewsMode } from './api';
import { useSportContext } from '../../context/SportContext';

interface UseFastNewsOptions {
  query: string;
  mode?: FastNewsMode;
  hours?: number;
  enabled?: boolean;
}

interface UseFastNewsByEntityOptions {
  entityType: string;
  entityId: string;
  mode?: FastNewsMode;
  hours?: number;
  enabled?: boolean;
}

export function useFastNews(opts: UseFastNewsOptions): { data: FastNewsResponse | undefined; isLoading: boolean; error: any; refetch: () => void } {
  const { activeSport } = useSportContext();
  const { query, mode = 'auto', hours = 48, enabled = true } = opts;
  const canRun = enabled && !!query.trim();
  const [data, setData] = React.useState<FastNewsResponse | undefined>(undefined);
  const [isLoading, setIsLoading] = React.useState<boolean>(canRun);
  const [error, setError] = React.useState<any>(null);

  const run = React.useCallback(async () => {
    if (!canRun) return;
    setIsLoading(true);
    setError(null);
    try {
      const result = await fetchFastNews(query, activeSport, { mode, hours });
      setData(result);
    } catch (e) {
      setError(e);
    } finally {
      setIsLoading(false);
    }
  }, [canRun, query, activeSport, mode, hours]);

  React.useEffect(() => {
    run();
  }, [run]);

  return { data, isLoading, error, refetch: run };
}

export function useFastNewsByEntity(opts: UseFastNewsByEntityOptions): { data: FastNewsResponse | undefined; isLoading: boolean; error: any; refetch: () => void } {
  const { activeSport } = useSportContext();
  const { entityType, entityId, mode = 'auto', hours = 48, enabled = true } = opts;
  const canRun = enabled && !!entityType && !!entityId;
  const [data, setData] = React.useState<FastNewsResponse | undefined>(undefined);
  const [isLoading, setIsLoading] = React.useState<boolean>(canRun);
  const [error, setError] = React.useState<any>(null);

  const run = React.useCallback(async () => {
    if (!canRun) return;
    setIsLoading(true);
    setError(null);
    try {
      const result = await fetchFastNewsByEntity(entityType, entityId, activeSport, { mode, hours });
      setData(result);
    } catch (e) {
      setError(e);
    } finally {
      setIsLoading(false);
    }
  }, [canRun, entityType, entityId, activeSport, mode, hours]);

  React.useEffect(() => {
    run();
  }, [run]);

  return { data, isLoading, error, refetch: run };
}
