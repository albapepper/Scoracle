import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Card, Title, Text, SegmentedControl, Stack } from '@mantine/core';
import { useSportContext } from '../context/SportContext';
import apiSearch from '../features/search/api';
import EntityAutocomplete from './EntityAutocomplete';
import { useThemeMode, getThemeColors } from '../theme';
import { useTranslation } from 'react-i18next';
import type { AutocompleteResult } from '../features/autocomplete/types';

export default function SearchForm() {
  const navigate = useNavigate();
  const { activeSport, sports } = useSportContext();
  const { t } = useTranslation();
  const [query, setQuery] = useState('');
  const [selected, setSelected] = useState<AutocompleteResult | null>(null);
  const [entityType, setEntityType] = useState<'player' | 'team'>('player');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const activeSportDisplay = sports.find((s) => s.id === activeSport)?.display || activeSport;
  const { colorScheme } = useThemeMode();
  const colors = getThemeColors(colorScheme);
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    try {
      if (!query.trim() && !selected) {
        throw new Error(t('search.enterTerm'));
      }
      if (selected) {
        const plainName = (selected.name || selected.label || '').trim();
        navigate(`/mentions/${entityType}/${selected.id}?sport=${activeSport}&name=${encodeURIComponent(plainName)}`);
        return;
      }
      const results = await (apiSearch as any).searchEntities(query, entityType, activeSport);
      if (results.results && results.results.length === 1) {
        const only = results.results[0];
        const plainName = (only.name || only.label || query).trim();
        navigate(`/mentions/${entityType}/${only.id}?sport=${activeSport}&name=${encodeURIComponent(plainName)}`);
      } else if (results.results && results.results.length > 1) {
        const first = results.results[0];
        const plainName = (first.name || first.label || query).trim();
        navigate(`/mentions/${entityType}/${first.id}?sport=${activeSport}&name=${encodeURIComponent(plainName)}`);
      } else {
        setError(t('search.noneFound', { entity: t(`common.entity.${entityType}`), query }));
      }
    } catch (err: any) {
      setError(err?.message || t('search.errorGeneric'));
    } finally {
      setIsLoading(false);
    }
  };
  
  return (
    <Card shadow="sm" p="lg" radius="lg" withBorder={false} style={{ 
      backgroundColor: colors.background.tertiary
    }}>
      <form onSubmit={handleSubmit}>
        <Stack>
          <Title order={3} ta="center" style={{ color: colors.text.accent }}>
            {t('search.title', { sport: activeSportDisplay, entity: t(`common.entity.${entityType}`) })}
          </Title>
          
          <SegmentedControl
            value={entityType}
            onChange={(v) => setEntityType(v as 'player' | 'team')}
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
