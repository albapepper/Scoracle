import { useEffect, useState } from 'react';
import { http } from '../app/http';

// Re-implemented correlation ID hook in TypeScript (previous JS file removed).
// Exposes last correlation ID, updating when it changes via polling.
export default function useCorrelationId(refreshMs: number = 2000): string | null {
  const [cid, setCid] = useState<string | null>(http.getLastCorrelationId());
  useEffect(() => {
    let alive = true;
    const id = setInterval(() => {
      const current = http.getLastCorrelationId();
      if (!alive) return;
      setCid(current);
    }, refreshMs);
    return () => { alive = false; clearInterval(id); };
  }, [refreshMs]);
  return cid;
}
