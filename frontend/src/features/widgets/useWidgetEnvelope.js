import { useQuery } from '@tanstack/react-query';
import api from './api';

export function useWidgetEnvelope(entityType, id, { sport, season, debug, enabled = true, staleTime = 60_000 } = {}) {
  return useQuery({
    queryKey: ['widget', entityType, id, sport, season, debug ? 1 : 0],
    queryFn: () => api.getWidgetEnvelope(entityType, id, { sport, season, debug }),
    enabled: enabled && !!entityType && !!id && !!sport,
    staleTime,
  });
}
