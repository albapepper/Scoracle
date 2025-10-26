import React, { useState, useEffect, useRef } from 'react';
import { TextInput, Paper, Loader, ScrollArea, Text } from '@mantine/core';
import { IconSearch } from '@tabler/icons-react';
import { useSportContext } from '../context/SportContext';
import axios from 'axios';
import theme from '../theme';
import { useTranslation } from 'react-i18next';

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
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState([]);
  const [error, setError] = useState('');
  const debounced = useDebounce(query, 300);
  const abortRef = useRef();

  useEffect(() => {
    if (debounced.trim().length < 2) { setResults([]); setError(''); return; }

    const fetchData = async () => {
      if (abortRef.current) abortRef.current.abort();
      const controller = new AbortController();
      abortRef.current = controller;
      setLoading(true);
      setError('');
      try {
        const resp = await axios.get(`/api/v1/${activeSport}/autocomplete/${entityType}`, {
          params: { q: debounced },
          signal: controller.signal,
        });
        setResults(resp.data.results || []);
      } catch (err) {
        if (!axios.isCancel(err)) {
          setError(t('search.autocompleteFailed'));
        }
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [debounced, entityType, activeSport, t]);

  const handleSelect = (item) => {
    onSelect(item);
    setQuery(item.label);
    setResults([]);
  };

  return (
    <div style={{ position: 'relative' }}>
      <TextInput
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder={placeholder || t('search.searchEntity', { entity: t(`common.entity.${entityType}`) })}
        icon={loading ? <Loader size="xs" /> : <IconSearch size={16} />}
        styles={{ input: { backgroundColor: theme.colors.background.secondary } }}
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
                  background: theme.colors.background.secondary,
                  borderBottom: `1px solid ${theme.colors.ui.border}`
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
