import * as React from 'react';
import api from '../../entities/api';

export interface UseEntityMentionsState<T = any> {
  data: T | null;
  isLoading: boolean;
  error: unknown;
}

export type EntityMentionsFetcher<T = any> = (entityType: string, entityId: string | number, sport: string) => Promise<T>;

export function useEntityMentions<T = any>(
  entityType?: string,
  entityId?: string | number,
  sport?: string,
  fetcher?: EntityMentionsFetcher<T>
): UseEntityMentionsState<T> {
  const enabled = !!entityType && !!entityId && !!sport;
  const [state, setState] = React.useState<UseEntityMentionsState<T>>({ data: null, isLoading: enabled, error: null });

  React.useEffect(() => {
    let alive = true;
    async function run() {
      if (!enabled) return;
      try {
        const loader = fetcher || (api.getEntityMentions as EntityMentionsFetcher<T>);
        const data = await loader(entityType!, entityId!, sport!);
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
  }, [entityType, entityId, sport, enabled, fetcher]);

  return state;
}

export default useEntityMentions;