import React from 'react';
import api from '../../entities/api';

export function useEntitySummary(entityType, entityId, sport, opts = {}) {
  const enabled = !!entityType && !!entityId && !!sport;
  const [state, setState] = React.useState({ data: null, isLoading: enabled, error: null });
  React.useEffect(() => {
    let alive = true;
    async function run() {
      if (!enabled) return;
      try {
        const data = entityType === 'team'
          ? await api.getTeamDetails(entityId, undefined, sport)
          : await api.getPlayerDetails(entityId, undefined, sport);
        if (alive) setState({ data, isLoading: false, error: null });
      } catch (e) {
        if (alive) setState({ data: null, isLoading: false, error: e });
      }
    }
    setState((s) => ({ ...s, isLoading: enabled }));
    run();
    return () => { alive = false; };
  }, [entityType, entityId, sport, enabled]);
  return state;
}
