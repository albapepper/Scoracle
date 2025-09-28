import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Container, Title, Text, Card, Group, Button, Loader, Stack, Tabs, Select, Switch, Badge, Tooltip } from '@mantine/core';
import { useSportContext } from '../context/SportContext';
import { getPlayerDetails, getPlayerSeasons, getPlayerPercentiles } from '../services/api';
import theme from '../theme';

// Import D3 visualization component
import PlayerStatsRadarChart from '../visualizations/PlayerStatsRadarChart';

function PlayerPage() {
  const { playerId } = useParams();
  const { activeSport } = useSportContext();
  const [playerInfo, setPlayerInfo] = useState(null);
  const [playerStats, setPlayerStats] = useState(null);
  const [playerPercentiles, setPlayerPercentiles] = useState(null);
  const [availableSeasons, setAvailableSeasons] = useState([]);
  const [selectedSeason, setSelectedSeason] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [showPercentiles, setShowPercentiles] = useState(true);
  
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
  
  // Fetch player details, stats and percentiles when season changes
  useEffect(() => {
    const fetchPlayerData = async () => {
      if (!selectedSeason) return;
      
      setIsLoading(true);
      setError('');
      
      try {
        // Fetch basic player details
        const detailsData = await getPlayerDetails(playerId, selectedSeason, activeSport);
        setPlayerInfo(detailsData.info || null);
        setPlayerStats(detailsData.statistics || null);
        
        // Fetch percentile data
        const percentilesData = await getPlayerPercentiles(playerId, selectedSeason, activeSport);
        setPlayerPercentiles(percentilesData.percentiles || null);
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
  
  // Helper function to get color for percentile
  const getPercentileColor = (percentile) => {
    if (!percentile && percentile !== 0) return theme.colors.ui.border;
    
    if (percentile >= 80) return theme.colors.visualization.percentiles[4];
    if (percentile >= 60) return theme.colors.visualization.percentiles[3];
    if (percentile >= 40) return theme.colors.visualization.percentiles[2];
    if (percentile >= 20) return theme.colors.visualization.percentiles[1];
    return theme.colors.visualization.percentiles[0];
  };
  
  // Helper function to get label for percentile
  const getPercentileLabel = (percentile) => {
    if (!percentile && percentile !== 0) return 'N/A';
    
    if (percentile >= 80) return 'Elite';
    if (percentile >= 60) return 'Above Avg';
    if (percentile >= 40) return 'Average';
    if (percentile >= 20) return 'Below Avg';
    return 'Low';
  };
  
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
              <Card withBorder p="lg">
                {/* Percentile toggle switch */}
                <Group position="right" mb="md">
                  <Group spacing="xs">
                    <Text size="sm">Raw Stats</Text>
                    <Switch 
                      checked={showPercentiles}
                      onChange={(event) => setShowPercentiles(event.currentTarget.checked)}
                      color="gray"
                    />
                    <Text size="sm">Percentiles</Text>
                  </Group>
                </Group>
                
                {/* Radar chart */}
                <Group position="center" mb="xl">
                  <PlayerStatsRadarChart 
                    stats={playerStats} 
                    percentiles={playerPercentiles}
                    showPercentiles={showPercentiles}
                  />
                </Group>
                
                <Stack spacing="md">
                  {/* Stats cards with percentile indicators */}
                  <Group grow>
                    <Card withBorder p="md" style={{ position: 'relative' }}>
                      <Text fw={700} size="lg" ta="center">{playerStats.points_per_game.toFixed(1)}</Text>
                      <Text size="sm" c="dimmed" ta="center">PPG</Text>
                      
                      {playerPercentiles && (
                        <Tooltip 
                          label={`${playerPercentiles.points_per_game.toFixed(1)}% percentile among all players`}
                          position="top"
                        >
                          <Badge 
                            style={{ 
                              position: 'absolute', 
                              top: '8px', 
                              right: '8px',
                              backgroundColor: getPercentileColor(playerPercentiles.points_per_game)
                            }}
                            size="sm"
                          >
                            {getPercentileLabel(playerPercentiles.points_per_game)}
                          </Badge>
                        </Tooltip>
                      )}
                    </Card>
                    
                    <Card withBorder p="md" style={{ position: 'relative' }}>
                      <Text fw={700} size="lg" ta="center">{playerStats.rebounds_per_game.toFixed(1)}</Text>
                      <Text size="sm" c="dimmed" ta="center">RPG</Text>
                      
                      {playerPercentiles && (
                        <Tooltip 
                          label={`${playerPercentiles.rebounds_per_game.toFixed(1)}% percentile among all players`}
                          position="top"
                        >
                          <Badge 
                            style={{ 
                              position: 'absolute', 
                              top: '8px', 
                              right: '8px',
                              backgroundColor: getPercentileColor(playerPercentiles.rebounds_per_game)
                            }}
                            size="sm"
                          >
                            {getPercentileLabel(playerPercentiles.rebounds_per_game)}
                          </Badge>
                        </Tooltip>
                      )}
                    </Card>
                    
                    <Card withBorder p="md" style={{ position: 'relative' }}>
                      <Text fw={700} size="lg" ta="center">{playerStats.assists_per_game.toFixed(1)}</Text>
                      <Text size="sm" c="dimmed" ta="center">APG</Text>
                      
                      {playerPercentiles && (
                        <Tooltip 
                          label={`${playerPercentiles.assists_per_game.toFixed(1)}% percentile among all players`}
                          position="top"
                        >
                          <Badge 
                            style={{ 
                              position: 'absolute', 
                              top: '8px', 
                              right: '8px',
                              backgroundColor: getPercentileColor(playerPercentiles.assists_per_game)
                            }}
                            size="sm"
                          >
                            {getPercentileLabel(playerPercentiles.assists_per_game)}
                          </Badge>
                        </Tooltip>
                      )}
                    </Card>
                  </Group>
                  
                  <Group grow>
                    <Card withBorder p="md" style={{ position: 'relative' }}>
                      <Text fw={700} size="lg" ta="center">{playerStats.steals_per_game.toFixed(1)}</Text>
                      <Text size="sm" c="dimmed" ta="center">SPG</Text>
                      
                      {playerPercentiles && (
                        <Tooltip 
                          label={`${playerPercentiles.steals_per_game.toFixed(1)}% percentile among all players`}
                          position="top"
                        >
                          <Badge 
                            style={{ 
                              position: 'absolute', 
                              top: '8px', 
                              right: '8px',
                              backgroundColor: getPercentileColor(playerPercentiles.steals_per_game)
                            }}
                            size="sm"
                          >
                            {getPercentileLabel(playerPercentiles.steals_per_game)}
                          </Badge>
                        </Tooltip>
                      )}
                    </Card>
                    
                    <Card withBorder p="md" style={{ position: 'relative' }}>
                      <Text fw={700} size="lg" ta="center">{playerStats.blocks_per_game.toFixed(1)}</Text>
                      <Text size="sm" c="dimmed" ta="center">BPG</Text>
                      
                      {playerPercentiles && (
                        <Tooltip 
                          label={`${playerPercentiles.blocks_per_game.toFixed(1)}% percentile among all players`}
                          position="top"
                        >
                          <Badge 
                            style={{ 
                              position: 'absolute', 
                              top: '8px', 
                              right: '8px',
                              backgroundColor: getPercentileColor(playerPercentiles.blocks_per_game)
                            }}
                            size="sm"
                          >
                            {getPercentileLabel(playerPercentiles.blocks_per_game)}
                          </Badge>
                        </Tooltip>
                      )}
                    </Card>
                    
                    <Card withBorder p="md" style={{ position: 'relative' }}>
                      <Text fw={700} size="lg" ta="center">{(playerStats.field_goal_percentage * 100).toFixed(1)}%</Text>
                      <Text size="sm" c="dimmed" ta="center">FG%</Text>
                      
                      {playerPercentiles && (
                        <Tooltip 
                          label={`${playerPercentiles.field_goal_percentage.toFixed(1)}% percentile among all players`}
                          position="top"
                        >
                          <Badge 
                            style={{ 
                              position: 'absolute', 
                              top: '8px', 
                              right: '8px',
                              backgroundColor: getPercentileColor(playerPercentiles.field_goal_percentage)
                            }}
                            size="sm"
                          >
                            {getPercentileLabel(playerPercentiles.field_goal_percentage)}
                          </Badge>
                        </Tooltip>
                      )}
                    </Card>
                  </Group>
                  
                  {/* Additional stats with percentile indicators */}
                  <Group grow>
                    <Card withBorder p="md">
                      <Group position="apart" align="center">
                        <div>
                          <Text fw={700} size="lg">{playerStats.games_played}</Text>
                          <Text size="sm" c="dimmed">Games</Text>
                        </div>
                        
                        <div>
                          <Text fw={700} size="lg">{playerStats.minutes_per_game.toFixed(1)}</Text>
                          <Text size="sm" c="dimmed">MPG</Text>
                          
                          {playerPercentiles && (
                            <Badge 
                              style={{ 
                                backgroundColor: getPercentileColor(playerPercentiles.minutes_per_game)
                              }}
                              size="xs"
                            >
                              {playerPercentiles.minutes_per_game.toFixed(0)}%
                            </Badge>
                          )}
                        </div>
                      </Group>
                    </Card>
                    
                    <Card withBorder p="md">
                      <Group position="apart" align="center">
                        <div>
                          <Text fw={700} size="lg">{(playerStats.three_point_percentage * 100).toFixed(1)}%</Text>
                          <Text size="sm" c="dimmed">3P%</Text>
                          
                          {playerPercentiles && (
                            <Badge 
                              style={{ 
                                backgroundColor: getPercentileColor(playerPercentiles.three_point_percentage)
                              }}
                              size="xs"
                            >
                              {playerPercentiles.three_point_percentage.toFixed(0)}%
                            </Badge>
                          )}
                        </div>
                        
                        <div>
                          <Text fw={700} size="lg">{(playerStats.free_throw_percentage * 100).toFixed(1)}%</Text>
                          <Text size="sm" c="dimmed">FT%</Text>
                          
                          {playerPercentiles && (
                            <Badge 
                              style={{ 
                                backgroundColor: getPercentileColor(playerPercentiles.free_throw_percentage)
                              }}
                              size="xs"
                            >
                              {playerPercentiles.free_throw_percentage.toFixed(0)}%
                            </Badge>
                          )}
                        </div>
                      </Group>
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