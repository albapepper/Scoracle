/**
 * Autocomplete hook - uses IndexedDB for fast local searches.
 * 
 * IndexedDB is seeded from bundled JSON files (frontend/public/data/*.json)
 * exported from backend SQLite. This avoids serverless SQLite issues while keeping
 * fast local autocomplete. See backend/scripts/export_sqlite_to_json.py
 */
import { useEffect, useRef, useState, useMemo } from 'react';
import type { AutocompleteResult } from './types';
import { searchPlayers as searchPlayersDB, searchTeams as searchTeamsDB } from '../../services/indexedDB';
import { mapSportToBackendCode } from '../../utils/sportMapping';
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
	
	// Map frontend sport ID to backend sport code for IndexedDB search
	const backendSportCode = useMemo(() => mapSportToBackendCode(sport), [sport]);

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
					
					setResults(combined);
					setError('');
					setLoading(false);
				} else {
					const raw = entityType === 'team'
						? await searchTeamsDB(backendSportCode, query, limit)
						: await searchPlayersDB(backendSportCode, query, limit);
					
					if (currentReqId !== reqIdRef.current) return; // Stale request
					
					const mapped = mapResults(raw as any, entityType, backendSportCode);
					setResults(mapped);
					setError('');
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
	}, [query, backendSportCode, entityType, limit, debounceMs]);

	return { query, setQuery, results, loading, error };
}

export default useAutocomplete;
