import React, { createContext, useContext, useMemo, useState, useCallback } from 'react';
import { useIndexedDBSync } from '../hooks/useIndexedDBSync';
import { mapSportToBackendCode } from '../utils/sportMapping';

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

  // Get backend sport code for syncing
  const backendSportCode = mapSportToBackendCode(activeSport);
  
  // Auto-sync IndexedDB when sport changes (loads from bundled JSON files)
  const { isSyncing, syncError, hasData, playersCount, teamsCount } = useIndexedDBSync({
    sport: backendSportCode,
    autoSync: true,
  });

  const changeSport = useCallback((sportId: string) => {
    if (sports.some((s) => s.id === sportId)) {
      setActiveSport(sportId);
      // Sync will be triggered automatically by useIndexedDBSync hook
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
