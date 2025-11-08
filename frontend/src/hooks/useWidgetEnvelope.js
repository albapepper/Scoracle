import { useQuery } from '@tanstack/react-query';
import { getWidgetEnvelope } from '../services/api';
import { FEATURES } from '../config';

export function useWidgetEnvelope(type, id, { sport, season, enabled = true, debug = false } = {}) {
  const useServer = FEATURES.USE_SERVER_WIDGETS;
  const hasSport = Boolean(sport);
  return useQuery({
    queryKey: ['widget', type, sport || 'none', id, season || 'current', 'v1'],
    queryFn: () => getWidgetEnvelope(type, id, { sport, season, debug }),
    enabled: enabled && useServer && !!id && hasSport,
    staleTime: 300 * 1000,
    refetchOnWindowFocus: false,
  });
}

export default useWidgetEnvelope;