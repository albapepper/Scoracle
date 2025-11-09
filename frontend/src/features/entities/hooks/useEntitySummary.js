import { useQuery } from '@tanstack/react-query';
import api from '../../entities/api';

export function useEntitySummary(entityType, entityId, sport, opts = {}) {
  const fn = entityType === 'team'
    ? () => api.getTeamDetails(entityId, undefined, sport)
    : () => api.getPlayerDetails(entityId, undefined, sport);
  return useQuery({
    queryKey: ['entity', entityType, entityId, sport],
    queryFn: fn,
    enabled: !!entityType && !!entityId && !!sport,
    staleTime: opts.staleTime ?? 60_000,
  });
}
