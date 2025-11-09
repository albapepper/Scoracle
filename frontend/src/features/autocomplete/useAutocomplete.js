import { useEffect, useMemo, useRef, useState } from 'react';

export function useAutocomplete({ sport, entityType, debounceMs = 200, limit = 15 }) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const reqIdRef = useRef(0);
  const workerRef = useRef(null);

  const worker = useMemo(() => {
    if (typeof Worker === 'undefined') return null;
    if (!workerRef.current) {
      if (process.env.NODE_ENV === 'test') {
        // In tests, use a mock worker URL; the test replaces global.Worker
        workerRef.current = new Worker('mock://autocomplete');
      } else {
        try {
          // Access import.meta via eval to avoid Jest parser errors
          // eslint-disable-next-line no-eval
          const meta = (0, eval)('import.meta');
          workerRef.current = new Worker(new URL('./worker/autocomplete.worker.js', meta.url));
        } catch (_) {
          // Fallback: disable worker in environments that don't support module workers
          workerRef.current = null;
        }
      }
    }
    return workerRef.current;
  }, []);

  useEffect(() => {
    if (!worker) return;
    const onMsg = (e) => {
      const data = e.data || {};
      if (data.type !== 'results') return;
      if (data.requestId !== reqIdRef.current) return; // stale
      setLoading(false);
      if (data.error) {
        setError(data.error);
        setResults([]);
      } else {
        setError('');
        setResults(data.results || []);
      }
    };
    worker.addEventListener('message', onMsg);
    return () => worker.removeEventListener('message', onMsg);
  }, [worker]);

  useEffect(() => {
    if (!worker) return;
    if (!query || query.trim().length < 2) {
      setResults([]);
      setError('');
      setLoading(false);
      return;
    }
    const id = setTimeout(() => {
      reqIdRef.current += 1;
      setLoading(true);
      worker.postMessage({ type: 'search', sport, entityType, query, limit, requestId: reqIdRef.current });
    }, debounceMs);
    return () => clearTimeout(id);
  }, [query, sport, entityType, limit, debounceMs, worker]);

  return { query, setQuery, results, loading, error };
}
