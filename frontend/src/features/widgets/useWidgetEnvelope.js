// Converted to local fetch without React Query; keeps same signature
import React from 'react';
import api from './api';

export function useWidgetEnvelope(entityType, id, { sport, season, debug, enabled = true } = {}) {
  const [state, setState] = React.useState({ data: null, isLoading: !!(enabled && entityType && id && sport), error: null });
  React.useEffect(() => {
    let alive = true;
    async function run() {
      if (!(enabled && entityType && id && sport)) return;
      try {
        const data = await api.getWidgetEnvelope(entityType, id, { sport, season, debug });
        if (alive) setState({ data, isLoading: false, error: null });
      } catch (e) {
        if (alive) setState({ data: null, isLoading: false, error: e });
      }
    }
    setState((s) => ({ ...s, isLoading: true }));
    run();
    return () => { alive = false; };
  }, [entityType, id, sport, season, debug, enabled]);
  return state;
}
