import React, { createContext, useContext, useRef } from 'react';

// Simple in-memory cache for entity summaries keyed by sport|type|id
const EntityCacheContext = createContext(null);

export function EntityCacheProvider({ children }) {
  const cacheRef = useRef(new Map());

  const makeKey = (sport, entityType, id) => `${(sport||'').toUpperCase()}|${entityType}|${id}`;

  const putSummary = (sport, entityType, id, summary) => {
    if (!sport || !entityType || !id || !summary) return;
    cacheRef.current.set(makeKey(sport, entityType, id), summary);
  };

  const getSummary = (sport, entityType, id) => {
    return cacheRef.current.get(makeKey(sport, entityType, id));
  };

  return (
    <EntityCacheContext.Provider value={{ putSummary, getSummary }}>
      {children}
    </EntityCacheContext.Provider>
  );
}

export const useEntityCache = () => useContext(EntityCacheContext);
