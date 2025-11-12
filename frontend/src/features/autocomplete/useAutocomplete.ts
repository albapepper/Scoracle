import { useEffect, useMemo, useRef, useState } from 'react';
import type { AutocompleteResult } from './types';

export interface UseAutocompleteOptions {
	sport: string;
	entityType: 'player' | 'team';
	debounceMs?: number;
	limit?: number;
}

export interface UseAutocompleteState {
	query: string;
	setQuery: (q: string) => void;
	results: AutocompleteResult[];
	loading: boolean;
	error: string;
}

export function useAutocomplete({ sport, entityType, debounceMs = 200, limit = 15 }: UseAutocompleteOptions): UseAutocompleteState {
	const [query, setQuery] = useState('');
	const [results, setResults] = useState<AutocompleteResult[]>([]);
	const [loading, setLoading] = useState(false);
	const [error, setError] = useState('');
	const reqIdRef = useRef(0);
	const workerRef = useRef<Worker | null>(null);

	const worker = useMemo(() => {
		if (typeof Worker === 'undefined') return null;
		if (!workerRef.current) {
			if (process.env.NODE_ENV === 'test') {
				// In tests, use a mock worker URL; the test replaces global.Worker
				// @ts-ignore - mock worker protocol
				workerRef.current = new Worker('mock://autocomplete');
			} else {
				try {
					// Access import.meta via eval to avoid Jest parser errors
					// eslint-disable-next-line no-eval
					const meta = (0, eval)('import.meta') as ImportMeta;
					// Module worker URL resolution
					// @ts-ignore - new URL with import.meta is supported by bundler
					workerRef.current = new Worker(new URL('./worker/autocomplete.worker.ts', (meta as any).url), { type: 'module' } as any);
				} catch {
					// Fallback: disable worker in environments that don't support module workers
					workerRef.current = null;
				}
			}
		}
		return workerRef.current;
	}, []);

	useEffect(() => {
		if (!worker) return;
		const onMsg = (e: MessageEvent) => {
			const data = (e.data || {}) as any;
			if (data.type !== 'results') return;
			if (data.requestId !== reqIdRef.current) return; // stale
			setLoading(false);
			if (data.error) {
				setError(String(data.error));
				setResults([]);
			} else {
				setError('');
				setResults((data.results || []) as AutocompleteResult[]);
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

export default useAutocomplete;
