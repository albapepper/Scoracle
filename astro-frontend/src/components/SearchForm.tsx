import { useState, useEffect, useRef } from 'react';
import { IconSearch } from '@tabler/icons-react';
import type { AutocompleteEntity, SportId } from '../lib/types';

interface SearchFormProps {
  sport: SportId;
}

const CACHE_KEY = 'scoracle_autocomplete_cache';
const CACHE_EXPIRY = 24 * 60 * 60 * 1000; // 24 hours

interface CachedData {
  data: AutocompleteEntity[];
  timestamp: number;
}

export default function SearchForm({ sport }: SearchFormProps) {
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState<AutocompleteEntity[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [allData, setAllData] = useState<AutocompleteEntity[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    // Load autocomplete data with caching
    const loadData = async () => {
      try {
        // Check cache first
        const cache = localStorage.getItem(CACHE_KEY);
        let cachedData: Record<string, CachedData> | null = null;
        
        if (cache) {
          try {
            cachedData = JSON.parse(cache);
            if (cachedData && cachedData[sport]) {
              const { data, timestamp } = cachedData[sport];
              if (Date.now() - timestamp < CACHE_EXPIRY) {
                setAllData(data);
                return; // Use cached data
              }
            }
          } catch (e) {
            console.warn('Cache parse error:', e);
          }
        }

        // Fetch fresh data if not cached
        const response = await fetch(`/data/${sport}.json`);
        if (!response.ok) throw new Error('Failed to fetch data');
        
        const json = await response.json();
        const items: AutocompleteEntity[] = [];
        
        // Add players
        if (json.players?.items) {
          items.push(...json.players.items.map((p: any) => ({
            id: String(p.id),
            name: p.name,
            type: 'player',
            team: p.currentTeam || p.team,
          })));
        }
        
        // Add teams
        if (json.teams?.items) {
          items.push(...json.teams.items.map((t: any) => ({
            id: String(t.id),
            name: t.name,
            type: 'team',
          })));
        }
        
        setAllData(items);
        
        // Update cache
        if (cachedData) {
          cachedData[sport] = { data: items, timestamp: Date.now() };
        } else {
          cachedData = { [sport]: { data: items, timestamp: Date.now() } };
        }
        localStorage.setItem(CACHE_KEY, JSON.stringify(cachedData));
      } catch (error) {
        console.error('Failed to load autocomplete data:', error);
      }
    };
    
    loadData();
  }, [sport]);

  useEffect(() => {
    if (query.length < 2) {
      setSuggestions([]);
      setShowSuggestions(false);
      return;
    }

    // Case-insensitive search
    const lowerQuery = query.toLowerCase();
    const filtered = allData
      .filter(item => item.name.toLowerCase().includes(lowerQuery))
      .slice(0, 10);

    setSuggestions(filtered);
    setShowSuggestions(filtered.length > 0);
  }, [query, allData]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (suggestions.length > 0) {
      handleSelect(suggestions[0]);
    }
  };

  const handleSelect = (entity: AutocompleteEntity) => {
    const type = entity.type || 'player';
    // Redirect to mentions page with query params
    window.location.href = `/mentions?sport=${sport}&type=${type}&id=${entity.id}`;
  };

  return (
    <form onSubmit={handleSubmit} className="relative w-full max-w-2xl">
      <div className="relative">
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => query.length >= 2 && setShowSuggestions(true)}
          onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
          placeholder={`Search for ${sport.toUpperCase()} players or teams...`}
          className="input pr-12"
          autoComplete="off"
        />
        <button
          type="submit"
          className="absolute right-2 top-1/2 -translate-y-1/2 p-2 text-slate-500 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
          aria-label="Search"
        >
          <IconSearch size={20} />
        </button>
      </div>

      {showSuggestions && suggestions.length > 0 && (
        <div className="absolute z-10 w-full mt-2 bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-600 rounded-lg shadow-lg max-h-96 overflow-y-auto">
          {suggestions.map((suggestion, index) => (
            <button
              key={`${suggestion.id}-${index}`}
              type="button"
              onClick={() => handleSelect(suggestion)}
              className="w-full text-left px-4 py-3 hover:bg-slate-100 dark:hover:bg-slate-700 border-b border-slate-200 dark:border-slate-700 last:border-b-0 transition-colors"
            >
              <div className="font-medium">{suggestion.name}</div>
              {suggestion.team && (
                <div className="text-sm text-slate-500 dark:text-slate-400">
                  {suggestion.team}
                </div>
              )}
            </button>
          ))}
        </div>
      )}
    </form>
  );
}
