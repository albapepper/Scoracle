import { useState, useEffect } from 'react';
import { SPORTS, type SportId } from '../lib/types';

interface SportSelectorProps {
  initialSport?: SportId;
  onSportChange?: (sport: SportId) => void;
}

export default function SportSelector({ initialSport = 'nba', onSportChange }: SportSelectorProps) {
  const [activeSport, setActiveSport] = useState<SportId>(initialSport);

  useEffect(() => {
    // Load from localStorage
    const saved = localStorage.getItem('activeSport') as SportId | null;
    if (saved && SPORTS.some(s => s.id === saved)) {
      setActiveSport(saved);
    }
  }, []);

  const handleSportChange = (sportId: SportId) => {
    setActiveSport(sportId);
    localStorage.setItem('activeSport', sportId);
    if (onSportChange) {
      onSportChange(sportId);
    }
  };

  return (
    <nav className="flex gap-2 flex-wrap">
      {SPORTS.map((sport) => (
        <button
          key={sport.id}
          onClick={() => handleSportChange(sport.id)}
          className={`btn ${
            activeSport === sport.id ? 'btn-primary' : 'btn-secondary'
          }`}
        >
          {sport.display}
        </button>
      ))}
    </nav>
  );
}
