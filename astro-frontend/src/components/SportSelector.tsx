import { SPORTS, type SportId } from '../lib/types';

interface SportSelectorProps {
  initialSport?: SportId;
  onSportChange?: (sport: SportId) => void;
}

export default function SportSelector({ initialSport = 'nba', onSportChange }: SportSelectorProps) {
  const handleSportChange = (sportId: SportId) => {
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
            initialSport === sport.id ? 'btn-primary' : 'btn-secondary'
          }`}
        >
          {sport.display}
        </button>
      ))}
    </nav>
  );
}
