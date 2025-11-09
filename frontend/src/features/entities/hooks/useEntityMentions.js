import { useQuery } from '@tanstack/react-query';
import api from '../../entities/api';

export function useEntityMentions(entityType, entityId, sport) {
  return useQuery({
    queryKey: ['mentions', entityType, entityId, sport],
    queryFn: () => api.getEntityMentions(entityType, entityId, sport),
    enabled: !!entityType && !!entityId && !!sport,
    staleTime: 60_000,
  });
}
