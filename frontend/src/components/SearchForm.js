import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Card, Title, Text, SegmentedControl, Stack } from '@mantine/core';
import { useSportContext } from '../context/SportContext';
import { searchEntities } from '../services/api'; // fallback search
import EntityAutocomplete from './EntityAutocomplete';
import theme from '../theme';

function SearchForm() {
  const navigate = useNavigate();
  const { activeSport } = useSportContext();
  const [query, setQuery] = useState(''); // still track for fallback submit
  const [selected, setSelected] = useState(null);
  const [entityType, setEntityType] = useState('player');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    
    try {
      if (!query.trim()) {
        throw new Error('Please enter a search term');
      }
      // If user selected from autocomplete, trust that ID
      if (selected) {
        navigate(`/mentions/${entityType}/${selected.id}?sport=${activeSport}`);
        return;
      }
      // Fallback: perform legacy search
      const results = await searchEntities(query, entityType, activeSport);
      if (results.results && results.results.length === 1) {
        const only = results.results[0];
        navigate(`/mentions/${entityType}/${only.id}?sport=${activeSport}`);
      } else if (results.results && results.results.length > 1) {
        const firstResult = results.results[0];
        navigate(`/mentions/${entityType}/${firstResult.id}?sport=${activeSport}`);
      } else {
        setError(`No ${entityType}s found matching "${query}"`);
      }
    } catch (err) {
      setError(err.message || 'An error occurred during search');
    } finally {
      setIsLoading(false);
    }
  };
  
  return (
    <Card shadow="sm" p="lg" radius="md" withBorder style={{ 
      backgroundColor: theme.colors.background.secondary,
      borderColor: theme.colors.ui.border
    }}>
      <form onSubmit={handleSubmit}>
        <Stack>
          <Title order={3} ta="center" style={{ color: theme.colors.text.accent }}>
            Find a {activeSport} {entityType}
          </Title>
          
          <SegmentedControl
            value={entityType}
            onChange={setEntityType}
            data={[
              { label: 'Player', value: 'player' },
              { label: 'Team', value: 'team' },
            ]}
            styles={{
              root: {
                backgroundColor: theme.colors.background.tertiary,
                borderColor: theme.colors.ui.border
              }
            }}
            color={theme.colors.ui.primary}
            fullWidth
          />
          
          <EntityAutocomplete
            entityType={entityType}
            placeholder={`Start typing a ${entityType} name...`}
            onSelect={(item) => { setSelected(item); setQuery(item.label); }}
          />
          
          {error && <Text c="red" ta="center">{error}</Text>}
          
          <Button 
            type="submit" 
            loading={isLoading}
            fullWidth
            size="md"
            style={{ 
              backgroundColor: theme.colors.ui.primary,
              color: 'white'
            }}
          >
            {selected ? 'Go' : 'Search'}
          </Button>
        </Stack>
      </form>
    </Card>
  );
}

export default SearchForm;