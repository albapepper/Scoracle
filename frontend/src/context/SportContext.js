import React, { createContext, useContext, useMemo, useState, useCallback } from 'react';

// Simple sport registry; expand as backend enumerations grow.
const DEFAULT_SPORTS = [
  { id: 'soccer', display: 'Soccer' },
  { id: 'basketball', display: 'Basketball' },
];

const SportContext = createContext(null);

export function SportContextProvider({ children }) {
  const [activeSport, setActiveSport] = useState('soccer');
  const sports = DEFAULT_SPORTS;

  const changeSport = useCallback((sportId) => {
    if (sports.some(s => s.id === sportId)) {
      setActiveSport(sportId);
    }
  }, [sports]);

  const value = useMemo(() => ({ activeSport, sports, changeSport }), [activeSport, sports, changeSport]);
  return <SportContext.Provider value={value}>{children}</SportContext.Provider>;
}

export function useSportContext() {
  const ctx = useContext(SportContext);
  if (!ctx) throw new Error('useSportContext must be used within SportContextProvider');
  return ctx;
}

export default SportContext;
