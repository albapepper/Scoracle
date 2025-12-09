/**
 * Autocomplete hook - uses in-memory search on bundled JSON data.
 * 
 * Data is loaded once per sport from /data/{sport}.json and cached in memory.
 * Fast, simple, no IndexedDB complexity.
 */
import { useEffect, useRef, useState, useMemo } from 'react';
import type { AutocompleteResult } from './types';
import { searchPlayers, searchTeams, preloadSport, type SearchResult } from './dataLoader';
import { mapSportToBackendCode } from '../../utils/sportMapping';

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

/**
 * Map search results to autocomplete format
 */
function mapToAutocomplete(
  results: SearchResult[],
  entityType: 'player' | 'team',
  sport: string
): AutocompleteResult[] {
  return results.map(r => ({
    id: r.id,
    label: entityType === 'player' && r.team 
      ? `${r.name} (${r.team})` 
      : r.name,
    name: r.name,
    entity_type: entityType,
    sport,
    team: r.team || null,
    source: 'memory',
  }));
}

export function useAutocomplete({ 
  sport, 
  entityType = 'both', 
  debounceMs = 200, 
  limit = 15 
}: UseAutocompleteOptions): UseAutocompleteState {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<AutocompleteResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const reqIdRef = useRef(0);
  
  // Map frontend sport ID to backend sport code
  const backendSportCode = useMemo(() => mapSportToBackendCode(sport), [sport]);

  // Preload data when sport changes
  useEffect(() => {
    preloadSport(backendSportCode);
  }, [backendSportCode]);

  // Search effect
  useEffect(() => {
    if (!query || query.trim().length < 2) {
      setResults([]);
      setError('');
      setLoading(false);
      return;
    }
    
    const timeoutId = setTimeout(async () => {
      reqIdRef.current += 1;
      const currentReqId = reqIdRef.current;
      setLoading(true);
      setError('');
      
      try {
        let combinedResults: AutocompleteResult[] = [];
        
        if (entityType === 'both') {
          // Search both players and teams in parallel
          const [players, teams] = await Promise.all([
            searchPlayers(backendSportCode, query, Math.ceil(limit / 2)),
            searchTeams(backendSportCode, query, Math.ceil(limit / 2))
          ]);
          
          if (currentReqId !== reqIdRef.current) return; // Stale request
          
          const mappedPlayers = mapToAutocomplete(players, 'player', backendSportCode);
          const mappedTeams = mapToAutocomplete(teams, 'team', backendSportCode);
          
          // Interleave results by score (players and teams are already sorted)
          combinedResults = [...mappedPlayers, ...mappedTeams].slice(0, limit);
        } else {
          const searchFn = entityType === 'team' ? searchTeams : searchPlayers;
          const raw = await searchFn(backendSportCode, query, limit);
          
          if (currentReqId !== reqIdRef.current) return; // Stale request
          
          combinedResults = mapToAutocomplete(raw, entityType, backendSportCode);
        }
        
        setResults(combinedResults);
        setError('');
      } catch (err: any) {
        if (currentReqId !== reqIdRef.current) return; // Stale request
        console.error('[useAutocomplete] Search error:', err);
        setError(err?.message || 'Search failed');
        setResults([]);
      } finally {
        if (currentReqId === reqIdRef.current) {
          setLoading(false);
        }
      }
    }, debounceMs);
    
    return () => clearTimeout(timeoutId);
  }, [query, backendSportCode, entityType, limit, debounceMs]);

  return { query, setQuery, results, loading, error };
}

export default useAutocomplete;
