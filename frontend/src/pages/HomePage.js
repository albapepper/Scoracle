import React from 'react';
import { Container, Title, Text, Stack, Paper, SegmentedControl, Box } from '@mantine/core';
import SearchForm from '../components/SearchForm';
import { useSportContext } from '../context/SportContext';
import theme from '../theme';

function HomePage() {
  const { activeSport, sports, changeSport } = useSportContext();
  
  return (
    <Container size="lg" py="xl">
      <Stack spacing="xl" align="center">
        <Box style={{ width: '100%', maxWidth: '600px' }}>
          <Paper
            shadow="xs"
            p="md"
            radius="md"
            withBorder
            style={{ 
              backgroundColor: theme.colors.background.secondary,
              borderColor: theme.colors.ui.border
            }}
          >
            <Title order={2} align="center" mb="md" 
              style={{ color: theme.colors.text.accent }}>
              Welcome to Scoracle
            </Title>
            
            <Text align="center" size="md" c="dimmed" mb="lg">
              Select your sport to get started
            </Text>
            
            <SegmentedControl
              value={activeSport}
              onChange={changeSport}
              data={sports.map(sport => ({
                label: sport.display,
                value: sport.id
              }))}
              fullWidth
              mb="md"
              color={theme.colors.ui.primary}
              styles={{
                root: {
                  backgroundColor: theme.colors.background.tertiary,
                  border: `1px solid ${theme.colors.ui.border}`
                },
                label: {
                  fontSize: '1rem',
                  padding: '8px 0'
                }
              }}
            />
            
            <Text align="center" size="sm" mt="md" mb="xl" c="dimmed">
              Find the latest news and statistics for your favorite {activeSport} players and teams
            </Text>
          </Paper>
        </Box>
        
        <Box style={{ width: '100%', maxWidth: '600px' }}>
          <SearchForm />
        </Box>
      </Stack>
    </Container>
  );
}

export default HomePage;