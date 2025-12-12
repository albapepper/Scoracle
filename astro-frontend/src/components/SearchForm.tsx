import { useState, useEffect, useRef } from 'react';
import { IconSearch } from '@tabler/icons-react';
import type { AutocompleteEntity, SportId } from '../lib/types';

interface SearchFormProps {
  sport: SportId;
}

export default function SearchForm({ sport }: SearchFormProps) {
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState<AutocompleteEntity[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [allData, setAllData] = useState<AutocompleteEntity[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    // Load autocomplete data for the current sport
    const loadData = async () => {
      try {
        const response = await fetch(`/data/${sport}.json`);
        const data = await response.json();
        
        const items: AutocompleteEntity[] = [];
        
        // Add players
        if (data.players?.items) {
          items.push(...data.players.items.map((p: any) => ({
            id: String(p.id),
            name: p.name,
            type: 'player',
            team: p.currentTeam || p.team,
          })));
        }
        
        // Add teams
        if (data.teams?.items) {
          items.push(...data.teams.items.map((t: any) => ({
            id: String(t.id),
            name: t.name,
            type: 'team',
          })));
        }
        
        setAllData(items);
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

    const filtered = allData
      .filter(item =>
        item.name.toLowerCase().includes(query.toLowerCase())
      )
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
    window.location.href = `/${sport}/${type}/${entity.id}`;
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
        />
        <button
          type="submit"
          className="absolute right-2 top-1/2 -translate-y-1/2 p-2 text-slate-500 hover:text-blue-600"
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
              className="w-full text-left px-4 py-3 hover:bg-slate-100 dark:hover:bg-slate-700 border-b border-slate-200 dark:border-slate-700 last:border-b-0"
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
