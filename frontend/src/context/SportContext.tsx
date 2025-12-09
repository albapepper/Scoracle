import React, { createContext, useContext, useMemo, useState, useCallback, useEffect } from 'react';
import { mapSportToBackendCode } from '../utils/sportMapping';
import { preloadSport } from '../features/autocomplete/dataLoader';

export interface SportInfo { id: string; display: string }
export interface SportContextValue { activeSport: string; sports: SportInfo[]; changeSport: (id: string) => void }

// Simple sport registry; expand as backend enumerations grow.
const DEFAULT_SPORTS: SportInfo[] = [
  { id: 'football', display: 'Football' },
  { id: 'nba', display: 'NBA' },
  { id: 'nfl', display: 'NFL' },
];

export const SportContext = createContext<SportContextValue | null>(null);

export function SportContextProvider({ children }: { children: React.ReactNode }) {
  const [activeSport, setActiveSport] = useState<string>('football');
  const sports = DEFAULT_SPORTS;

  // Preload autocomplete data when sport changes
  useEffect(() => {
    const backendCode = mapSportToBackendCode(activeSport);
    preloadSport(backendCode);
  }, [activeSport]);

  const changeSport = useCallback((sportId: string) => {
    if (sports.some((s) => s.id === sportId)) {
      setActiveSport(sportId);
    }
  }, [sports]);

  const value = useMemo(() => ({ activeSport, sports, changeSport }), [activeSport, sports, changeSport]);
  
  return <SportContext.Provider value={value}>{children}</SportContext.Provider>;
}

export function useSportContext(): SportContextValue {
  const ctx = useContext(SportContext);
  if (!ctx) throw new Error('useSportContext must be used within SportContextProvider');
  return ctx;
}

export default SportContext;
