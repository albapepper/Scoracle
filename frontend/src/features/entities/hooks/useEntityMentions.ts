import * as React from 'react';
import api from '../../entities/api';

export interface UseEntityMentionsState<T = any> {
  data: T | null;
  isLoading: boolean;
  error: unknown;
}

export function useEntityMentions<T = any>(entityType?: string, entityId?: string | number, sport?: string): UseEntityMentionsState<T> {
  const enabled = !!entityType && !!entityId && !!sport;
  const [state, setState] = React.useState<UseEntityMentionsState<T>>({ data: null, isLoading: enabled, error: null });

  React.useEffect(() => {
    let alive = true;
    async function run() {
      if (!enabled) return;
      try {
        const data = await api.getEntityMentions(entityType!, entityId!, sport!);
        if (!alive) return;
        setState({ data: (data as unknown) as T, isLoading: false, error: null });
      } catch (e) {
        if (!alive) return;
        setState({ data: null, isLoading: false, error: e });
      }
    }
    // Ensure state shape is preserved even if s is unexpectedly undefined in some test environments
    setState((s) => ({ ...(s ?? { data: null, error: null, isLoading: false }), isLoading: enabled }));
    run();
    return () => { alive = false; };
  }, [entityType, entityId, sport, enabled]);

  return state;
}

export default useEntityMentions;