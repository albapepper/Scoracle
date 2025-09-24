import React from 'react';
import { Container, Title, Text, Stack, Paper, Image, SimpleGrid } from '@mantine/core';
import SearchForm from '../components/SearchForm';
import { useSportContext } from '../context/SportContext';

function HomePage() {
  const { activeSport, sports } = useSportContext();
  const currentSport = sports.find(sport => sport.id === activeSport);
  
  // Content tailored to the selected sport
  const sportContent = {
    NBA: {
      title: "NBA Basketball",
      description: "Find the latest news and stats for NBA players and teams.",
      imagePath: "/images/nba-bg.jpg"
    },
    NFL: {
      title: "NFL Football",
      description: "Stay updated with NFL players and teams performance.",
      imagePath: "/images/nfl-bg.jpg"
    },
    EPL: {
      title: "English Premier League",
      description: "Follow your favorite EPL soccer players and clubs.",
      imagePath: "/images/epl-bg.jpg"
    }
  };
  
  const content = sportContent[activeSport];
  
  return (
    <Container size="md" py="xl">
      <Stack spacing="xl">
        <div>
          <Title order={1} align="center" mb="sm">{content.title}</Title>
          <Text align="center" size="lg" c="dimmed" mb="xl">
            {content.description}
          </Text>
        </div>
        
        <Paper
          shadow="md"
          p={{ base: 'md', sm: 'xl' }}
          radius="md"
          sx={theme => ({
            backgroundImage: `linear-gradient(rgba(0, 0, 0, 0.75), rgba(0, 0, 0, 0.75)), url(${content.imagePath})`,
            backgroundSize: 'cover',
            backgroundPosition: 'center',
            color: theme.white,
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            alignItems: 'center',
            height: '200px'
          })}
        >
          <Title order={2} mb="md">Welcome to Scoracle</Title>
          <Text size="lg" ta="center">
            Your one-stop destination for sports news and statistics
          </Text>
        </Paper>
        
        <SimpleGrid cols={{ base: 1, md: 2 }} spacing="md">
          <div>
            <Title order={3} mb="md">Latest News</Title>
            <Text>
              Scoracle brings you the most recent news about your favorite players and teams.
              Our RSS integration ensures you never miss important updates.
            </Text>
          </div>
          
          <div>
            <Title order={3} mb="md">Detailed Statistics</Title>
            <Text>
              Dive into comprehensive statistics with interactive visualizations.
              Analyze performance metrics and compare players and teams.
            </Text>
          </div>
        </SimpleGrid>
        
        <SearchForm />
      </Stack>
    </Container>
  );
}

export default HomePage;