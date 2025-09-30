import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Container, Title, Text, Card, Group, Button, Loader, Stack, Tabs, Select, Grid, Avatar } from '@mantine/core';
import { useSportContext } from '../context/SportContext';
import { getTeamDetails, getTeamRoster } from '../services/api';

// Import D3 visualization component
import TeamStatsBarChart from '../visualizations/TeamStatsBarChart';

function TeamPage() {
  const { teamId } = useParams();
  const { activeSport } = useSportContext();
  const [teamInfo, setTeamInfo] = useState(null);
  const [teamStats, setTeamStats] = useState(null);
  const [teamRoster, setTeamRoster] = useState([]);
  const availableSeasons = ['2023-2024', '2022-2023', '2021-2022'];
  const [selectedSeason, setSelectedSeason] = useState('2023-2024'); // Default to current season
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  
  // Fetch team details when season changes
  useEffect(() => {
    const fetchTeamData = async () => {
      setIsLoading(true);
      setError('');
      
      try {
        const data = await getTeamDetails(teamId, selectedSeason, activeSport);
        setTeamInfo(data.info || null);
        setTeamStats(data.statistics || null);
        
        // Fetch roster in the same season
        const rosterData = await getTeamRoster(teamId, selectedSeason, activeSport);
        setTeamRoster(rosterData.roster || []);
      } catch (err) {
        setError('Failed to load team data. Please try again later.');
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };
    
    if (selectedSeason) {
      fetchTeamData();
    }
  }, [teamId, selectedSeason, activeSport]);
  
  if (isLoading) {
    return (
      <Container size="md" py="xl" ta="center">
        <Loader size="xl" />
        <Text mt="md">Loading team data...</Text>
      </Container>
    );
  }
  
  if (error) {
    return (
      <Container size="md" py="xl" ta="center">
        <Title order={3} c="red">{error}</Title>
        <Button component={Link} to="/" mt="md">
          Return to Home
        </Button>
      </Container>
    );
  }
  
  return (
    <Container size="lg" py="xl">
      <Stack spacing="xl">
        {/* Team Header */}
        <Card p="md" withBorder>
          <Group position="apart">
            <div>
              <Title order={2}>{teamInfo?.name || 'Team'}</Title>
              <Group spacing="xs">
                {teamInfo?.city && <Text>{teamInfo.city}</Text>}
                {teamInfo?.conference && <Text>| {teamInfo.conference} Conference</Text>}
                {teamInfo?.division && <Text>| {teamInfo.division} Division</Text>}
              </Group>
            </div>
            
            <Group>
              <Button
                component={Link}
                to={`/mentions/team/${teamId}`}
                variant="outline"
              >
                View News
              </Button>
              <Button
                component={Link}
                to="/"
                variant="subtle"
              >
                Home
              </Button>
            </Group>
          </Group>
        </Card>
        
        {/* Season Selector */}
        <Group position="apart">
          <Title order={3}>Team Statistics</Title>
          
          <Select
            label="Season"
            placeholder="Select season"
            value={selectedSeason}
            onChange={setSelectedSeason}
            data={availableSeasons.map(season => ({
              value: season,
              label: season
            }))}
            w={200}
          />
        </Group>
        
        {/* Stats Content */}
        <Tabs defaultValue="overview">
          <Tabs.List>
            <Tabs.Tab value="overview">Overview</Tabs.Tab>
            <Tabs.Tab value="roster">Roster</Tabs.Tab>
            <Tabs.Tab value="advanced">Advanced</Tabs.Tab>
          </Tabs.List>

          <Tabs.Panel value="overview" pt="md">
            <Card withBorder>
              {teamStats ? (
                <>
                  <Group position="center" mb="xl">
                    <TeamStatsBarChart stats={teamStats} />
                  </Group>
                  
                  <Grid>
                    <Grid.Col span={6}>
                      <Card withBorder p="sm">
                        <Text fw={500} ta="center">{teamStats.wins}-{teamStats.losses}</Text>
                        <Text size="sm" c="dimmed" ta="center">Record</Text>
                      </Card>
                    </Grid.Col>
                    <Grid.Col span={6}>
                      <Card withBorder p="sm">
                        <Text fw={500} ta="center">
                          {teamStats.wins > 0 || teamStats.losses > 0 
                            ? (teamStats.wins / (teamStats.wins + teamStats.losses) * 100).toFixed(1) + '%'
                            : 'N/A'}
                        </Text>
                        <Text size="sm" c="dimmed" ta="center">Win Percentage</Text>
                      </Card>
                    </Grid.Col>
                    
                    <Grid.Col span={4}>
                      <Card withBorder p="sm">
                        <Text fw={500} ta="center">{teamStats.points_per_game}</Text>
                        <Text size="sm" c="dimmed" ta="center">PPG</Text>
                      </Card>
                    </Grid.Col>
                    <Grid.Col span={4}>
                      <Card withBorder p="sm">
                        <Text fw={500} ta="center">{teamStats.rebounds_per_game}</Text>
                        <Text size="sm" c="dimmed" ta="center">RPG</Text>
                      </Card>
                    </Grid.Col>
                    <Grid.Col span={4}>
                      <Card withBorder p="sm">
                        <Text fw={500} ta="center">{teamStats.assists_per_game}</Text>
                        <Text size="sm" c="dimmed" ta="center">APG</Text>
                      </Card>
                    </Grid.Col>
                  </Grid>
                </>
              ) : (
                <Text>No statistics available for this team in the selected season.</Text>
              )}
            </Card>
          </Tabs.Panel>

          <Tabs.Panel value="roster" pt="md">
            <Card withBorder p="md">
              {teamRoster.length > 0 ? (
                <Stack spacing="sm">
                  {teamRoster.map((player) => (
                    <Card key={player.id} withBorder>
                      <Group>
                        <Avatar
                          size="md"
                          radius="xl"
                          color="blue"
                        >
                          {player.first_name[0] + player.last_name[0]}
                        </Avatar>
                        <div style={{ flex: 1 }}>
                          <Text>
                            <Link to={`/player/${player.id}`}>
                              {player.first_name} {player.last_name}
                            </Link>
                          </Text>
                          <Text size="sm" color="dimmed">
                            {player.position} | #{player.jersey_number || 'N/A'}
                          </Text>
                        </div>
                        <Button
                          component={Link}
                          to={`/player/${player.id}`}
                          variant="subtle"
                          size="sm"
                        >
                          View Stats
                        </Button>
                      </Group>
                    </Card>
                  ))}
                </Stack>
              ) : (
                <Text>No roster information available for this team in the selected season.</Text>
              )}
            </Card>
          </Tabs.Panel>

          <Tabs.Panel value="advanced" pt="md">
            <Card withBorder p="md">
              <Text>Advanced team statistics would be displayed here.</Text>
              <Text c="dimmed" mt="md">
                This section would include metrics like Offensive Rating, Defensive Rating,
                Net Rating, Pace, and other advanced team analytics.
              </Text>
            </Card>
          </Tabs.Panel>
        </Tabs>
      </Stack>
    </Container>
  );
}

export default TeamPage;