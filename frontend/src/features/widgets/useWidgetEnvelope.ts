// Local fetch hook for widget envelope; replaces React Query usage with minimal state machine
import * as React from 'react';
import { getWidgetEnvelope } from './api';

export interface WidgetEnvelopeRequestOpts {
  sport?: string;
  season?: string;
  debug?: boolean;
  enabled?: boolean;
}

export interface WidgetEnvelopeState<T = any> {
  data: T | null;
  isLoading: boolean;
  error: unknown;
}

export function useWidgetEnvelope<T = any>(
  entityType: string | undefined,
  id: string | number | undefined,
  { sport, season, debug, enabled = true }: WidgetEnvelopeRequestOpts = {}
): WidgetEnvelopeState<T> {
  const [state, setState] = React.useState<WidgetEnvelopeState<T>>({
    data: null,
    isLoading: !!(enabled && entityType && id && sport),
    error: null,
  });

  React.useEffect(() => {
    let alive = true;
    async function run() {
      if (!(enabled && entityType && id && sport)) return;
      try {
        const data = await getWidgetEnvelope(entityType!, id!, { sport, season, debug });
        if (alive) setState({ data: data as T, isLoading: false, error: null });
      } catch (e) {
        if (alive) setState({ data: null, isLoading: false, error: e });
      }
    }
    setState((s) => ({ ...s, isLoading: !!(enabled && entityType && id && sport) }));
    void run();
    return () => {
      alive = false;
    };
  }, [entityType, id, sport, season, debug, enabled]);

  return state;
}

export default useWidgetEnvelope;
