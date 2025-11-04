import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Card, Title, Text, SegmentedControl, Stack } from '@mantine/core';
import { useSportContext } from '../context/SportContext';
import { searchEntities } from '../services/api'; // fallback search
import EntityAutocomplete from './EntityAutocomplete';
import { useThemeMode } from '../ThemeProvider';
import { getThemeColors } from '../theme';
import { useTranslation } from 'react-i18next';

function SearchForm() {
  const navigate = useNavigate();
  const { activeSport, sports } = useSportContext();
  const { t } = useTranslation();
  const [query, setQuery] = useState(''); // still track for fallback submit
  const [selected, setSelected] = useState(null);
  const [entityType, setEntityType] = useState('player');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const activeSportDisplay = sports.find((sport) => sport.id === activeSport)?.display || activeSport;
  const { colorScheme } = useThemeMode();
  const colors = getThemeColors(colorScheme);
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    
    try {
      if (!query.trim()) {
        throw new Error(t('search.enterTerm'));
      }
      // If user selected from autocomplete, trust that ID
      if (selected) {
        const plainName = (selected.name || selected.label || '').trim();
        navigate(`/mentions/${entityType}/${selected.id}?sport=${activeSport}&name=${encodeURIComponent(plainName)}`);
        return;
      }
      // Fallback: perform legacy search
      const results = await searchEntities(query, entityType, activeSport);
      if (results.results && results.results.length === 1) {
        const only = results.results[0];
        const plainName = (only.name || only.label || query).trim();
        navigate(`/mentions/${entityType}/${only.id}?sport=${activeSport}&name=${encodeURIComponent(plainName)}`);
      } else if (results.results && results.results.length > 1) {
        const firstResult = results.results[0];
        const plainName = (firstResult.name || firstResult.label || query).trim();
        navigate(`/mentions/${entityType}/${firstResult.id}?sport=${activeSport}&name=${encodeURIComponent(plainName)}`);
      } else {
        setError(t('search.noneFound', { entity: t(`common.entity.${entityType}`), query }));
      }
    } catch (err) {
      setError(err.message || t('search.errorGeneric'));
    } finally {
      setIsLoading(false);
    }
  };
  
  return (
    <Card shadow="sm" p="lg" radius="md" withBorder style={{ 
      backgroundColor: colors.background.secondary,
      borderColor: colors.ui.border
    }}>
      <form onSubmit={handleSubmit}>
        <Stack>
          <Title order={3} ta="center" style={{ color: colors.text.accent }}>
            {t('search.title', { sport: activeSportDisplay, entity: t(`common.entity.${entityType}`) })}
          </Title>
          
          <SegmentedControl
            value={entityType}
            onChange={setEntityType}
            data={[
              { label: t('common.entity.player'), value: 'player' },
              { label: t('common.entity.team'), value: 'team' },
            ]}
            styles={{
              root: {
                backgroundColor: colors.background.tertiary,
                borderColor: colors.ui.border
              }
            }}
            color={colors.ui.primary}
            fullWidth
          />
          
          <EntityAutocomplete
            entityType={entityType}
            placeholder={t('search.placeholder', { entity: t(`common.entity.${entityType}`) })}
            onSelect={(item) => { setSelected(item); setQuery(item.label); }}
          />
          
          {error && <Text c="red" ta="center">{error}</Text>}
          
          <Button 
            type="submit" 
            loading={isLoading}
            fullWidth
            size="md"
            style={{ 
              backgroundColor: colors.ui.primary,
              color: 'white'
            }}
          >
            {selected ? t('common.go') : t('common.search')}
          </Button>
        </Stack>
      </form>
    </Card>
  );
}

export default SearchForm;