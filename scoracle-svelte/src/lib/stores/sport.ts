/**
 * Sport store - replaces React SportContext
 */
import { writable, derived } from 'svelte/store';
import { browser } from '$app/environment';

export interface SportInfo {
  id: string;
  display: string;
}

export const sports: SportInfo[] = [
  { id: 'football', display: 'Football' },
  { id: 'nba', display: 'NBA' },
  { id: 'nfl', display: 'NFL' },
];

function createSportStore() {
  const { subscribe, set, update } = writable<string>('football');

  return {
    subscribe,
    change: (sportId: string) => {
      if (sports.some((s) => s.id === sportId)) {
        set(sportId);
        // Preload autocomplete data when sport changes
        if (browser) {
          import('$lib/data/dataLoader').then(({ preloadSport }) => {
            preloadSport(sportId);
          });
        }
      }
    },
    reset: () => set('football'),
  };
}

export const activeSport = createSportStore();

// Derived store for display name
export const activeSportDisplay = derived(activeSport, ($sport) => {
  const found = sports.find((s) => s.id === $sport);
  return found?.display || $sport;
});

/**
 * Map frontend sport ID to backend API code
 */
export function mapSportToBackendCode(sport: string): string {
  const mapping: Record<string, string> = {
    football: 'FOOTBALL',
    nba: 'NBA',
    nfl: 'NFL',
  };
  return mapping[sport.toLowerCase()] || sport.toUpperCase();
}

