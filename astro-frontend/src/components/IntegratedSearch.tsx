import { useState, useEffect } from 'react';
import { SPORTS, type SportId } from '../lib/types';
import SportSelector from './SportSelector';
import SearchForm from './SearchForm';

export default function IntegratedSearch() {
  const [activeSport, setActiveSport] = useState<SportId>('nba');

  useEffect(() => {
    // Load from localStorage on mount
    const saved = localStorage.getItem('activeSport') as SportId | null;
    if (saved && SPORTS.some(s => s.id === saved)) {
      setActiveSport(saved);
    }
  }, []);

  const handleSportChange = (sport: SportId) => {
    setActiveSport(sport);
    localStorage.setItem('activeSport', sport);
  };

  return (
    <>
      {/* Sport Selector */}
      <div>
        <h2 className="text-2xl font-semibold mb-4 text-center">Select a Sport</h2>
        <div className="flex justify-center">
          <SportSelector 
            initialSport={activeSport} 
            onSportChange={handleSportChange}
          />
        </div>
      </div>

      {/* Search Form */}
      <div>
        <h2 className="text-2xl font-semibold mb-4 text-center">Search</h2>
        <div className="flex justify-center">
          <SearchForm sport={activeSport} />
        </div>
        <p className="text-center text-sm text-slate-500 dark:text-slate-400 mt-2">
          Start typing to search for players or teams
        </p>
      </div>
    </>
  );
}
