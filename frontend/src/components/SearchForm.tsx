import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Card, Title, Text, SegmentedControl, Stack, Group, Flex } from '@mantine/core';
import { IconArrowRight } from '@tabler/icons-react';
import { useSportContext } from '../context/SportContext';
import apiSearch from '../features/search/api';
import EntityAutocomplete from './EntityAutocomplete';
import { useThemeMode, getThemeColors } from '../theme';
import { useTranslation } from 'react-i18next';
import type { AutocompleteResult } from '../features/autocomplete/types';
import './SearchForm.css';

interface SearchFormProps {
  inline?: boolean;
}

export default function SearchForm({ inline = false }: SearchFormProps) {
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
  
  const formContent = (
    <form onSubmit={handleSubmit}>
      <Stack style={{ overflow: 'visible' }}>
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
                border: 'none'
              },
              control: {
                borderLeft: 'none !important',
                borderRight: 'none !important',
                '&:not(:first-of-type)': { borderLeft: 'none !important' },
                '&:not(:last-of-type)': { borderRight: 'none !important' },
                '&[data-active]': colorScheme === 'light' 
                  ? { 
                      '& .mantine-SegmentedControl-label': { color: '#F5F5E8 !important' }
                    } 
                  : {},
              },
              label: {
                color: colors.text.primary,
                '&[data-active]': colorScheme === 'light' 
                  ? { color: '#F5F5E8 !important' } 
                  : {},
              },
              indicator: { border: 'none' },
            }}
            color={colors.ui.primary}
            fullWidth
          />
        
        <Group gap={0} wrap="nowrap" align="stretch">
          <Flex style={{ flex: 1 }} direction="column">
            <div className="search-form-input-wrapper">
              <div className="search-form-input-container">
                <EntityAutocomplete
                  entityType={entityType}
                  placeholder={t('search.placeholder')}
                  onSelect={(item) => { setSelected(item); setQuery(item.label); }}
                />
              </div>
              <Button 
                type="submit" 
                loading={isLoading}
                size="md"
                px="md"
                style={{ 
                  backgroundColor: colors.ui.primary,
                  color: 'white',
                  flexShrink: 0,
                  borderTopLeftRadius: 0,
                  borderBottomLeftRadius: 0
                }}
              >
                <IconArrowRight size={18} />
              </Button>
            </div>
            {error && <Text c="red" ta="center" size="sm" mt={4}>{error}</Text>}
          </Flex>
        </Group>
      </Stack>
    </form>
  );

  if (inline) {
    return formContent;
  }

  return (
    <Card shadow="sm" p="lg" radius="lg" withBorder={false} style={{ 
      backgroundColor: colors.background.tertiary,
      overflow: 'visible'
    }}>
      {formContent}
    </Card>
  );
}
