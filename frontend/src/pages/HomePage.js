import React from 'react';
import { Container, Title, Text, Stack, Paper, SegmentedControl, Box } from '@mantine/core';
import SearchForm from '../components/SearchForm';
import { useSportContext } from '../context/SportContext';
import theme from '../theme';
import { useTranslation } from 'react-i18next';

function HomePage() {
  const { activeSport, sports, changeSport } = useSportContext();
  const { t } = useTranslation();
  
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
            <Title order={2} align="center" mb="md" style={{ color: theme.colors.text.accent }}>
              {t('home.title')}
            </Title>
            
            <Text align="center" size="md" c="dimmed" mb="lg">
              {t('home.selectSport')}
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
              {t('home.findLatest', { sport: activeSport })}
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