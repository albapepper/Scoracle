import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Card, Text, Stack, Group, Flex } from '@mantine/core';
import { IconArrowUp } from '@tabler/icons-react';
import { useSportContext } from '../context/SportContext';
import EntityAutocomplete from './EntityAutocomplete';
import { useThemeMode, getThemeColors } from '../theme';
import { useTranslation } from 'react-i18next';
import type { AutocompleteResult } from '../features/autocomplete/types';
import { searchData } from '../features/autocomplete/dataLoader';
import './SearchForm.css';

interface SearchFormProps {
  inline?: boolean;
}

export default function SearchForm({ inline = false }: SearchFormProps) {
  const navigate = useNavigate();
  const { activeSport } = useSportContext();
  const { t } = useTranslation();
  const [query, setQuery] = useState('');
  const [selected, setSelected] = useState<AutocompleteResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
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
      
      // If user selected from autocomplete, navigate directly
      if (selected) {
        const plainName = (selected.name || selected.label || '').trim();
        const entityType = selected.entity_type || 'player';
        navigate(`/mentions/${entityType}/${selected.id}?sport=${activeSport}&name=${encodeURIComponent(plainName)}`);
        return;
      }
      
      // Fallback: search local bundled data
      const results = await searchData(activeSport, query.trim(), 10);
      
      if (results.length === 1) {
        const only = results[0];
        const plainName = (only.name || only.label || query).trim();
        const entityType = only.entity_type || 'player';
        navigate(`/mentions/${entityType}/${only.id}?sport=${activeSport}&name=${encodeURIComponent(plainName)}`);
      } else if (results.length > 1) {
        const first = results[0];
        const plainName = (first.name || first.label || query).trim();
        const entityType = first.entity_type || 'player';
        navigate(`/mentions/${entityType}/${first.id}?sport=${activeSport}&name=${encodeURIComponent(plainName)}`);
      } else {
        setError(t('search.noneFound', { entity: t('common.entity.all'), query }));
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
        <Group gap={0} wrap="nowrap" align="stretch">
          <Flex style={{ flex: 1 }} direction="column">
            <div className="search-form-input-wrapper">
              <div className="search-form-input-container">
                <EntityAutocomplete
                  placeholder="Search for player or team..."
                  onSelect={(item) => { setSelected(item); setQuery(item.label); }}
                />
              </div>
              <Button 
                type="submit" 
                loading={isLoading}
                size="md"
                px={0}
                style={{ 
                  backgroundColor: colors.ui.primary,
                  color: 'white',
                  flexShrink: 0,
                  width: '36px',
                  height: '36px',
                  borderRadius: '50%',
                  padding: 0,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  marginLeft: '4px'
                }}
              >
                <IconArrowUp size={18} />
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
