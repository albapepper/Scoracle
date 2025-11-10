import * as React from 'react';
import api from '../../entities/api';

export interface UseEntitySummaryState<T = any> {
  data: T | null;
  isLoading: boolean;
  error: unknown;
}

export function useEntitySummary<T = any>(
  entityType?: 'player' | 'team' | string,
  entityId?: string | number,
  sport?: string,
): UseEntitySummaryState<T> {
  const enabled = !!entityType && !!entityId && !!sport;
  const [state, setState] = React.useState<UseEntitySummaryState<T>>({ data: null, isLoading: enabled, error: null });

  React.useEffect(() => {
    let alive = true;
    async function run() {
      if (!enabled) return;
      try {
        const data = entityType === 'team'
          ? await api.getTeamDetails(entityId!, undefined, sport!)
          : await api.getPlayerDetails(entityId!, undefined, sport!);
        if (alive) setState({ data: data as T, isLoading: false, error: null });
      } catch (e) {
        if (alive) setState({ data: null, isLoading: false, error: e });
      }
    }
    setState((s) => ({ ...s, isLoading: enabled }));
    void run();
    return () => { alive = false; };
  }, [entityType, entityId, sport, enabled]);

  return state;
}

export default useEntitySummary;