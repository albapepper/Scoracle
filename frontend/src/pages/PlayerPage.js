import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Container, Title, Text, Card, Group, Button, Loader, Stack, Tabs, Select } from '@mantine/core';
import { useSportContext } from '../context/SportContext';
import { getPlayerDetails, getPlayerSeasons } from '../services/api';

// Import D3 visualization component
import PlayerStatsRadarChart from '../visualizations/PlayerStatsRadarChart';

function PlayerPage() {
  const { playerId } = useParams();
  const { activeSport } = useSportContext();
  const [playerInfo, setPlayerInfo] = useState(null);
  const [playerStats, setPlayerStats] = useState(null);
  const [availableSeasons, setAvailableSeasons] = useState([]);
  const [selectedSeason, setSelectedSeason] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  
  // Fetch available seasons for player
  useEffect(() => {
    const fetchSeasons = async () => {
      try {
        const data = await getPlayerSeasons(playerId, activeSport);
        setAvailableSeasons(data.seasons || []);
        if (data.seasons && data.seasons.length > 0) {
          setSelectedSeason(data.seasons[0]);  // Default to most recent season
        }
      } catch (err) {
        console.error("Failed to fetch seasons:", err);
      }
    };
    
    fetchSeasons();
  }, [playerId, activeSport]);
  
  // Fetch player details and stats when season changes
  useEffect(() => {
    const fetchPlayerData = async () => {
      if (!selectedSeason) return;
      
      setIsLoading(true);
      setError('');
      
      try {
        const data = await getPlayerDetails(playerId, selectedSeason, activeSport);
        setPlayerInfo(data.info || null);
        setPlayerStats(data.statistics || null);
      } catch (err) {
        setError('Failed to load player data. Please try again later.');
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };
    
    if (selectedSeason) {
      fetchPlayerData();
    }
  }, [playerId, selectedSeason, activeSport]);
  
  // Format player name
  const getPlayerName = () => {
    if (!playerInfo) return '';
    return `${playerInfo.first_name} ${playerInfo.last_name}`;
  };
  
  if (isLoading) {
    return (
      <Container size="md" py="xl" ta="center">
        <Loader size="xl" />
        <Text mt="md">Loading player data...</Text>
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
        {/* Player Header */}
        <Card p="md" withBorder>
          <Group position="apart">
            <div>
              <Title order={2}>{getPlayerName()}</Title>
              {playerInfo?.team && (
                <Text>
                  {playerInfo.position} | {playerInfo.team.name}
                </Text>
              )}
            </div>
            
            <Group>
              <Button
                component={Link}
                to={`/mentions/player/${playerId}`}
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
          <Title order={3}>Player Statistics</Title>
          
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
        {playerStats ? (
          <Tabs defaultValue="overview">
            <Tabs.List>
              <Tabs.Tab value="overview">Overview</Tabs.Tab>
              <Tabs.Tab value="shooting">Shooting</Tabs.Tab>
              <Tabs.Tab value="advanced">Advanced</Tabs.Tab>
            </Tabs.List>

            <Tabs.Panel value="overview" pt="md">
              <Card withBorder>
                <Group position="center" mb="xl">
                  <PlayerStatsRadarChart stats={playerStats} />
                </Group>
                
                <Stack>
                  <Group grow>
                    <Card withBorder p="sm">
                      <Text fw={500} ta="center">{playerStats.games_played}</Text>
                      <Text size="sm" c="dimmed" ta="center">Games</Text>
                    </Card>
                    <Card withBorder p="sm">
                      <Text fw={500} ta="center">{playerStats.minutes_per_game}</Text>
                      <Text size="sm" c="dimmed" ta="center">MPG</Text>
                    </Card>
                    <Card withBorder p="sm">
                      <Text fw={500} ta="center">{playerStats.points_per_game}</Text>
                      <Text size="sm" c="dimmed" ta="center">PPG</Text>
                    </Card>
                  </Group>
                  
                  <Group grow>
                    <Card withBorder p="sm">
                      <Text fw={500} ta="center">{playerStats.rebounds_per_game}</Text>
                      <Text size="sm" c="dimmed" ta="center">RPG</Text>
                    </Card>
                    <Card withBorder p="sm">
                      <Text fw={500} ta="center">{playerStats.assists_per_game}</Text>
                      <Text size="sm" c="dimmed" ta="center">APG</Text>
                    </Card>
                    <Card withBorder p="sm">
                      <Text fw={500} ta="center">{playerStats.steals_per_game}</Text>
                      <Text size="sm" c="dimmed" ta="center">SPG</Text>
                    </Card>
                  </Group>
                </Stack>
              </Card>
            </Tabs.Panel>

            <Tabs.Panel value="shooting" pt="md">
              <Card withBorder p="md">
                <Group grow mb="md">
                  <div>
                    <Text fw={500} ta="center" size="xl">{(playerStats.field_goal_percentage * 100).toFixed(1)}%</Text>
                    <Text size="sm" c="dimmed" ta="center">FG%</Text>
                  </div>
                  <div>
                    <Text fw={500} ta="center" size="xl">{(playerStats.three_point_percentage * 100).toFixed(1)}%</Text>
                    <Text size="sm" c="dimmed" ta="center">3P%</Text>
                  </div>
                  <div>
                    <Text fw={500} ta="center" size="xl">{(playerStats.free_throw_percentage * 100).toFixed(1)}%</Text>
                    <Text size="sm" c="dimmed" ta="center">FT%</Text>
                  </div>
                </Group>
                
                {/* Here we could add more shooting visualizations with D3 */}
                <Text>More detailed shooting charts would be displayed here using D3.js visualizations.</Text>
              </Card>
            </Tabs.Panel>

            <Tabs.Panel value="advanced" pt="md">
              <Card withBorder p="md">
                <Text>Advanced statistics would be displayed here.</Text>
                <Text c="dimmed" mt="md">
                  This section would include metrics like Player Efficiency Rating (PER), 
                  True Shooting Percentage (TS%), and other advanced analytics.
                </Text>
              </Card>
            </Tabs.Panel>
          </Tabs>
        ) : (
          <Text>No statistics available for this player in the selected season.</Text>
        )}
      </Stack>
    </Container>
  );
}

export default PlayerPage;