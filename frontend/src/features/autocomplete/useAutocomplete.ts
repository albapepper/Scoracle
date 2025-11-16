import { useEffect, useMemo, useRef, useState } from 'react';
import type { AutocompleteResult } from './types';
import { mapSportToBackendCode } from '../../utils/sportMapping';
import { searchPlayers as searchPlayersDB, searchTeams as searchTeamsDB } from '../../services/indexedDB';
import { mapResults } from './worker/map';

export interface UseAutocompleteOptions {
	sport: string;
	entityType?: 'player' | 'team' | 'both';
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

export function useAutocomplete({ sport, entityType = 'both', debounceMs = 200, limit = 15 }: UseAutocompleteOptions): UseAutocompleteState {
	const [query, setQuery] = useState('');
	const [results, setResults] = useState<AutocompleteResult[]>([]);
	const [loading, setLoading] = useState(false);
	const [error, setError] = useState('');
	const reqIdRef = useRef(0);
	const workerRef = useRef<Worker | null>(null);
	
	// Map frontend sport ID to backend sport code for IndexedDB search
	const backendSportCode = useMemo(() => mapSportToBackendCode(sport), [sport]);

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
			if (data.requestId !== reqIdRef.current) {
				if (process.env.NODE_ENV !== 'production') {
					console.log('[useAutocomplete] Stale result ignored:', data.requestId, 'current:', reqIdRef.current);
				}
				return; // stale
			}
			setLoading(false);
			if (data.error) {
				if (process.env.NODE_ENV !== 'production') {
					console.error('[useAutocomplete] Search error:', data.error);
				}
				setError(String(data.error));
				setResults([]);
			} else {
				if (process.env.NODE_ENV !== 'production') {
					console.log('[useAutocomplete] Received results:', data.results?.length || 0, 'results');
				}
				setError('');
				setResults((data.results || []) as AutocompleteResult[]);
			}
		};
		worker.addEventListener('message', onMsg);
		return () => worker.removeEventListener('message', onMsg);
	}, [worker]);

	useEffect(() => {
		if (!query || query.trim().length < 2) {
			setResults([]);
			setError('');
			setLoading(false);
			return;
		}
		
		const id = setTimeout(async () => {
			reqIdRef.current += 1;
			const currentReqId = reqIdRef.current;
			setLoading(true);
			
			if (process.env.NODE_ENV !== 'production') {
				console.log('[useAutocomplete] Searching:', { sport: backendSportCode, entityType, query, limit, hasWorker: !!worker });
			}
			
			try {
				if (worker) {
					// Use worker if available
					worker.postMessage({ type: 'search', sport: backendSportCode, entityType, query, limit, requestId: currentReqId });
				} else {
					// Fallback: search IndexedDB directly
					if (entityType === 'both') {
						// Search both players and teams, then combine and sort
						const [players, teams] = await Promise.all([
							searchPlayersDB(backendSportCode, query, Math.ceil(limit / 2)),
							searchTeamsDB(backendSportCode, query, Math.ceil(limit / 2))
						]);
						
						if (currentReqId !== reqIdRef.current) return; // Stale request
						
						const mappedPlayers = mapResults(players as any, 'player', backendSportCode);
						const mappedTeams = mapResults(teams as any, 'team', backendSportCode);
						
						// Combine and sort by relevance (simple: players first, then teams)
						const combined = [...mappedPlayers, ...mappedTeams].slice(0, limit);
						
						if (process.env.NODE_ENV !== 'production') {
							console.log('[useAutocomplete] Direct search results:', combined.length, `(${mappedPlayers.length} players, ${mappedTeams.length} teams)`);
						}
						setResults(combined);
						setError('');
						setLoading(false);
					} else {
						const raw = entityType === 'team'
							? await searchTeamsDB(backendSportCode, query, limit)
							: await searchPlayersDB(backendSportCode, query, limit);
						
						if (currentReqId !== reqIdRef.current) return; // Stale request
						
						const mapped = mapResults(raw as any, entityType, backendSportCode);
						if (process.env.NODE_ENV !== 'production') {
							console.log('[useAutocomplete] Direct search results:', mapped.length);
						}
						setResults(mapped);
						setError('');
						setLoading(false);
					}
				}
			} catch (err: any) {
				if (currentReqId !== reqIdRef.current) return; // Stale request
				console.error('[useAutocomplete] Search error:', err);
				setError(err?.message || 'Search failed');
				setResults([]);
				setLoading(false);
			}
		}, debounceMs);
		
		return () => clearTimeout(id);
	}, [query, backendSportCode, entityType, limit, debounceMs, worker]);

	return { query, setQuery, results, loading, error };
}

export default useAutocomplete;
