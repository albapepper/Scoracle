import React, { createContext, useState, useContext, useEffect } from 'react';

// Create context
const SportContext = createContext();

// Sport options
const SPORTS = [
  { id: 'NBA', name: 'Basketball', display: 'NBA' },
  { id: 'NFL', name: 'American Football', display: 'NFL' },
  { id: 'FOOTBALL', name: 'Soccer', display: 'Football' },
];

export const SportContextProvider = ({ children }) => {
  // Default to NBA
  const [activeSport, setActiveSport] = useState('NBA');
  
  // Load from localStorage on initial render
  useEffect(() => {
    const savedSport = localStorage.getItem('activeSport');
    if (savedSport && SPORTS.some(sport => sport.id === savedSport)) {
      setActiveSport(savedSport);
    }
  }, []);
  
  // Save to localStorage when sport changes
  useEffect(() => {
    localStorage.setItem('activeSport', activeSport);
  }, [activeSport]);
  
  // Change the active sport
  const changeSport = (sportId) => {
    if (SPORTS.some(sport => sport.id === sportId)) {
      setActiveSport(sportId);
    }
  };
  
  return (
    <SportContext.Provider 
      value={{ 
        activeSport, 
        changeSport, 
        sports: SPORTS 
      }}
    >
      {children}
    </SportContext.Provider>
  );
};

// Custom hook to use the sport context
export const useSportContext = () => useContext(SportContext);