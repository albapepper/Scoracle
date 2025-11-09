import React from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { TextInput, Paper, Loader, ScrollArea, Text } from '@mantine/core';
import { IconSearch } from '@tabler/icons-react';
import { useSportContext } from '../context/SportContext';
import apiEntities from '../features/entities/api';
import apiWidgets from '../features/widgets/api';
import { useThemeMode, getThemeColors } from '../theme';
import { useTranslation } from 'react-i18next';
import { useAutocomplete } from '../features/autocomplete/useAutocomplete';

// Debounce is handled inside useAutocomplete

export default function EntityAutocomplete({ entityType, onSelect, placeholder }) {
  const { activeSport } = useSportContext();
  const queryClient = useQueryClient();
  const { t } = useTranslation();
  const { colorScheme } = useThemeMode();
  const colors = getThemeColors(colorScheme);
  const { query, setQuery, results, loading, error } = useAutocomplete({ sport: activeSport, entityType, debounceMs: 300, limit: 15 });

  const handleSelect = (item) => {
    onSelect(item);
    const label = item.label || '';
    setQuery(label);
  };

  const handleChange = (e) => {
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
                onMouseEnter={() => {
                  // Prefetch entity basics and widget envelope to improve perceived speed
                  try {
                    if (r.entity_type === 'player') {
                      queryClient.prefetchQuery({
                        queryKey: ['entity','player', r.id, activeSport],
                        queryFn: () => apiEntities.getPlayerDetails(r.id, undefined, activeSport),
                        staleTime: 60_000,
                      });
                      queryClient.prefetchQuery({
                        queryKey: ['widget','player', r.id, activeSport],
                        queryFn: () => apiWidgets.getWidgetEnvelope('player', r.id, { sport: activeSport }),
                        staleTime: 60_000,
                      });
                    } else if (r.entity_type === 'team') {
                      queryClient.prefetchQuery({
                        queryKey: ['entity','team', r.id, activeSport],
                        queryFn: () => apiEntities.getTeamDetails(r.id, undefined, activeSport),
                        staleTime: 60_000,
                      });
                      queryClient.prefetchQuery({
                        queryKey: ['widget','team', r.id, activeSport],
                        queryFn: () => apiWidgets.getWidgetEnvelope('team', r.id, { sport: activeSport }),
                        staleTime: 60_000,
                      });
                    }
                  } catch (_) {}
                }}
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
      {!loading && query.length >= 2 && results.length === 0 && !error && (
        <Text size="xs" mt={4} c="dimmed">{t('search.noMatches')}</Text>
      )}
    </div>
  );
}
