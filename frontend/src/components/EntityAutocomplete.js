import React, { useState, useEffect, useRef } from 'react';
import { TextInput, Paper, Loader, ScrollArea, Text } from '@mantine/core';
import { IconSearch } from '@tabler/icons-react';
import { useSportContext } from '../context/SportContext';
import axios from 'axios';
import { useThemeMode } from '../ThemeProvider';
import { getThemeColors } from '../theme';
import { useTranslation } from 'react-i18next';
import { searchPlayers as searchPlayersIDB, searchTeams as searchTeamsIDB, initializeIndexedDB } from '../services/indexedDB';

// Simple debounce hook
function useDebounce(value, delay) {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const h = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(h);
  }, [value, delay]);
  return debounced;
}

export default function EntityAutocomplete({ entityType, onSelect, placeholder }) {
  const { activeSport } = useSportContext();
  const { t } = useTranslation();
  const { colorScheme } = useThemeMode();
  const colors = getThemeColors(colorScheme);
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState([]);
  const [error, setError] = useState('');
  const [skipNextFetch, setSkipNextFetch] = useState(false);
  const [useIndexedDB, setUseIndexedDB] = useState(false);
  const debounced = useDebounce(query, 300);
  const abortRef = useRef();

  // Initialize IndexedDB on component mount
  useEffect(() => {
    initializeIndexedDB()
      .then(() => {
        console.log('[EntityAutocomplete] IndexedDB initialized');
        setUseIndexedDB(true);
      })
      .catch(err => {
        console.warn('[EntityAutocomplete] IndexedDB initialization failed, will use API:', err);
        setUseIndexedDB(false);
      });
  }, []);

  useEffect(() => {
    const trimmed = debounced.trim();

    if (skipNextFetch) {
      return;
    }

    if (trimmed.length < 2) {
      setResults([]);
      setError('');
      return;
    }

    const fetchData = async () => {
      if (abortRef.current) abortRef.current.abort();
      const controller = new AbortController();
      abortRef.current = controller;
      setLoading(true);
      setError('');
      try {
        let localResults = [];

        // Try IndexedDB first if available
        if (useIndexedDB) {
          try {
            if (entityType === 'player') {
              const idbResults = await searchPlayersIDB(activeSport, debounced, 15);
              localResults = idbResults.map(p => ({
                id: p.playerId,
                label: p.currentTeam ? `${p.fullName} (${p.currentTeam})` : p.fullName,
                name: p.fullName,
                entity_type: 'player',
                sport: activeSport,
                team: p.currentTeam || null,
                team_abbr: null,
                source: 'indexeddb',
              }));
            } else if (entityType === 'team') {
              const idbResults = await searchTeamsIDB(activeSport, debounced, 15);
              localResults = idbResults.map(t => ({
                id: t.teamId,
                label: t.name,
                name: t.name,
                entity_type: 'team',
                sport: activeSport,
                league: null,
                team_abbr: null,
                source: 'indexeddb',
              }));
            }
          } catch (idbErr) {
            console.warn('[EntityAutocomplete] IndexedDB search failed, falling back to API:', idbErr);
          }
        }

        // If no local results, fall back to API
        if (localResults.length === 0) {
          const resp = await axios.get(`/api/v1/${activeSport}/autocomplete/${entityType}`, {
            params: { q: debounced },
            signal: controller.signal,
          });
          localResults = resp.data.results || [];
        }

        setResults(localResults);
      } catch (err) {
        if (!axios.isCancel(err)) {
          setError(t('search.autocompleteFailed'));
        }
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [debounced, entityType, activeSport, t, skipNextFetch, useIndexedDB]);

  const handleSelect = (item) => {
    onSelect(item);
    if (abortRef.current) {
      abortRef.current.abort();
    }
    const label = item.label || '';
    setQuery(label);
    setResults([]);
    setSkipNextFetch(true);
  };

  const handleChange = (e) => {
    setSkipNextFetch(false);
    setQuery(e.target.value);
  };

  return (
    <div style={{ position: 'relative' }}>
      <TextInput
        value={query}
        onChange={handleChange}
        placeholder={placeholder || t('search.searchEntity', { entity: t(`common.entity.${entityType}`) })}
        icon={loading ? <Loader size="xs" /> : <IconSearch size={16} />}
        styles={{ input: { backgroundColor: colors.background.secondary } }}
        autoComplete="off"
      />
      {error && <Text size="xs" c="red" mt={4}>{error}</Text>}
      {results.length > 0 && (
        <Paper withBorder shadow="sm" p={0} style={{ position: 'absolute', zIndex: 20, width: '100%', top: '100%', marginTop: 4 }}>
          <ScrollArea.Autosize mah={250}>
            {results.map(r => (
              <div
                key={`${r.entity_type}-${r.id}`}
                onClick={() => handleSelect(r)}
                style={{
                  padding: '6px 10px',
                  cursor: 'pointer',
                  background: colors.background.secondary,
                  borderBottom: `1px solid ${colors.ui.border}`
                }}
              >
                <Text size="sm">{r.label}</Text>
              </div>
            ))}
          </ScrollArea.Autosize>
        </Paper>
      )}
      {!loading && debounced.length >= 2 && results.length === 0 && !error && (
        <Text size="xs" mt={4} c="dimmed">{t('search.noMatches')}</Text>
      )}
    </div>
  );
}
