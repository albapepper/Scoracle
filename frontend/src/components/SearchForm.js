import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  TextInput, 
  Button, 
  Group, 
  Card, 
  Title, 
  Text, 
  Container, 
  SegmentedControl,
  Stack,
  Center,
} from '@mantine/core';
import { useSportContext } from '../context/SportContext';
import { searchEntities } from '../services/api';

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
    <Card shadow="sm" p="lg" radius="md" withBorder>
      <form onSubmit={handleSubmit}>
        <Stack>
          <Title order={3} ta="center">Find a Player or Team</Title>
          
          <SegmentedControl
            value={entityType}
            onChange={setEntityType}
            data={[
              { label: 'Player', value: 'player' },
              { label: 'Team', value: 'team' },
            ]}
            fullWidth
          />
          
          <TextInput
            required
            placeholder={`Enter ${entityType} name`}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          
          {error && <Text c="red">{error}</Text>}
          
          <Button 
            type="submit" 
            loading={isLoading}
            fullWidth
          >
            Search
          </Button>
        </Stack>
      </form>
    </Card>
  );
}

export default SearchForm;