import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  TextInput, 
  Button, 
  Group, 
  Card, 
  Title, 
  Text, 
  SegmentedControl,
  Stack,
} from '@mantine/core';
import { useSportContext } from '../context/SportContext';
import { searchEntities } from '../services/api';
import theme from '../theme';
import { IconSearch } from '@tabler/icons-react';

function SearchForm() {
  const navigate = useNavigate();
  const { activeSport } = useSportContext();
  const [query, setQuery] = useState('');
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
      
      const results = await searchEntities(query, entityType, activeSport);
      
      if (results.results && results.results.length > 0) {
        // Navigate to the first result's mentions page
        const firstResult = results.results[0];
        navigate(`/mentions/${entityType}/${firstResult.id}`);
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
      backgroundColor: theme.colors.background.primary,
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
          
          <TextInput
            required
            placeholder={`Search for a ${entityType} by name...`}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            size="lg"
            icon={<IconSearch size="1.2rem" />}
            styles={{
              input: {
                backgroundColor: theme.colors.background.secondary,
                '&:focus': {
                  borderColor: theme.colors.ui.primary
                }
              }
            }}
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
            Search
          </Button>
        </Stack>
      </form>
    </Card>
  );
}

export default SearchForm;