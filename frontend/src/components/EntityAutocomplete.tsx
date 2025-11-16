import React from 'react';
import './EntityAutocomplete.css';
import { TextInput, Paper, Loader, ScrollArea, Text } from '@mantine/core';
import { IconSearch } from '@tabler/icons-react';
import { useSportContext } from '../context/SportContext';
// React Query prefetch removed to decouple from react-query
import { useThemeMode, getThemeColors } from '../theme';
import { useTranslation } from 'react-i18next';
import { useAutocomplete } from '../features/autocomplete/useAutocomplete';

export interface EntityAutocompleteProps {
  entityType?: 'player' | 'team' | 'both';
  onSelect: (item: any) => void;
  placeholder?: string;
}

export default function EntityAutocomplete({ entityType = 'both', onSelect, placeholder }: EntityAutocompleteProps) {
  const { activeSport } = useSportContext();
  const { t } = useTranslation();
  const { colorScheme } = useThemeMode();
  const colors = getThemeColors(colorScheme);
  const { query, setQuery, results, loading, error } = useAutocomplete({ sport: activeSport, entityType, debounceMs: 300, limit: 15 });
  const [showNoMatches, setShowNoMatches] = React.useState(false);
  
  // Delay showing "No matches found" to prevent flash during search
  React.useEffect(() => {
    if (loading || query.length < 2 || results.length > 0 || error) {
      setShowNoMatches(false);
      return;
    }
    
    // Only show "No matches" after a short delay to avoid flash
    const timer = setTimeout(() => {
      setShowNoMatches(true);
    }, 200);
    
    return () => clearTimeout(timer);
  }, [loading, query.length, results.length, error]);
  
  // Show dropdown when there are results OR when showing "no matches"
  const showDropdown = query.length >= 2 && (results.length > 0 || showNoMatches) && !error;
  
  // Debug logging
  React.useEffect(() => {
    if (process.env.NODE_ENV !== 'production') {
      console.log('[EntityAutocomplete]', { activeSport, entityType, query, resultsCount: results.length, loading, error });
    }
  }, [activeSport, entityType, query, results.length, loading, error]);

  const handleSelect = (item: any) => {
    onSelect(item);
    const label = item.label || '';
    setQuery(label);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setQuery(e.target.value);
  };

  return (
    <div className="entity-autocomplete-root">
      <TextInput
        value={query}
        onChange={handleChange}
        placeholder={placeholder || (entityType === 'both' ? t('search.searchEntity', { entity: t('common.entity.all') }) : t('search.searchEntity', { entity: t(`common.entity.${entityType}`) }))}
        leftSection={loading ? <Loader size="xs" /> : <IconSearch size={16} />}
        styles={{ 
          input: { 
            backgroundColor: colors.background.secondary,
            borderTopRightRadius: 0,
            borderBottomRightRadius: 0,
            border: 'none',
            color: colors.text.primary,
            caretColor: colorScheme === 'dark' ? '#FFFFFF' : '#1A1A1A'
          } 
        }}
        autoComplete="off"
      />
      {error && <Text size="xs" c="red" mt={4}>{String(error)}</Text>}
      {showDropdown && (
        <Paper withBorder shadow="sm" p={0} className="entity-autocomplete-menu">
          {results.length > 0 ? (
            <ScrollArea.Autosize mah={250}>
              {results.map((r: any) => (
                <div
                  key={`${r.entity_type}-${r.id}`}
                  onClick={() => handleSelect(r)}
                  onMouseEnter={() => { /* no-op: prefetch removed */ }}
                  className="entity-autocomplete-item"
                >
                  <Text size="sm">{r.label}</Text>
                </div>
              ))}
            </ScrollArea.Autosize>
          ) : (
            <div style={{ padding: '12px 16px' }}>
              <Text size="xs" c="dimmed" ta="center">{t('search.noMatches')}</Text>
            </div>
          )}
        </Paper>
      )}
    </div>
  );
}
