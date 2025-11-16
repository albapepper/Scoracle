/**
 * Autocomplete hook - currently uses backend API calls.
 * 
 * To switch back to IndexedDB (frontend local DB) for faster local searches:
 * 1. Import IndexedDB search functions from '../../services/indexedDB'
 * 2. Import mapSportToBackendCode and mapResults helpers
 * 3. Replace backend API calls with IndexedDB searches
 * 4. Re-enable useIndexedDBSync in SportContext.tsx
 * 
 * See README.md in this directory for detailed instructions.
 */
import { useEffect, useRef, useState } from 'react';
import type { AutocompleteResult } from './types';
import { http } from '../../app/http';

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
			setError('');
			
			try {
				if (entityType === 'both') {
					// Search both players and teams, then combine
					const [playersRes, teamsRes] = await Promise.all([
						http.get<{ results: AutocompleteResult[] }>(`${sport.toLowerCase()}/autocomplete/player`, { params: { q: query, limit: Math.ceil(limit / 2) } }),
						http.get<{ results: AutocompleteResult[] }>(`${sport.toLowerCase()}/autocomplete/team`, { params: { q: query, limit: Math.ceil(limit / 2) } })
					]);
					
					if (currentReqId !== reqIdRef.current) return; // Stale request
					
					const combined = [...(playersRes.results || []), ...(teamsRes.results || [])].slice(0, limit);
					setResults(combined);
					setLoading(false);
				} else {
					const res = await http.get<{ results: AutocompleteResult[] }>(`${sport.toLowerCase()}/autocomplete/${entityType}`, { params: { q: query, limit } });
					
					if (currentReqId !== reqIdRef.current) return; // Stale request
					
					setResults(res.results || []);
					setLoading(false);
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
	}, [query, sport, entityType, limit, debounceMs]);

	return { query, setQuery, results, loading, error };
}

export default useAutocomplete;
