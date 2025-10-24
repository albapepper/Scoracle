import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Container, Title, Text, Card, Group, Button, Loader, Stack, Tabs, Select } from '@mantine/core';
import { useSportContext } from '../context/SportContext';
import { getPlayerFull, getPlayerSeasons } from '../services/api';
import { useQuery } from '@tanstack/react-query';
import { useEntityCache } from '../context/EntityCacheContext';
import BasicEntityCard from '../components/BasicEntityCard';
import ApiSportsWidget from '../components/ApiSportsWidget';

// Import D3 visualization component
import GenericStatsBarChart from '../visualizations/GenericStatsBarChart';

function PlayerPage() {
  const { playerId } = useParams();
  const { activeSport } = useSportContext();
  const { getSummary, putSummary } = useEntityCache();
  const [playerInfo, setPlayerInfo] = useState(() => getSummary(activeSport, 'player', playerId) || null); // seed from cache if exists
  const [playerStats, setPlayerStats] = useState(null);
  // Percentiles removed
  const [playerProfile, setPlayerProfile] = useState(null);
  const [metricsGroups, setMetricsGroups] = useState({});
  const [selectedGroup, setSelectedGroup] = useState('base');
  const [availableSeasons, setAvailableSeasons] = useState([]);
  const [selectedSeason, setSelectedSeason] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  // removed idSource badge in header refactor
  
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
  
  const { data: fullData, isLoading: fullLoading, error: fullError } = useQuery({
    queryKey: ['playerFull', playerId, selectedSeason, activeSport],
    enabled: !!selectedSeason,
    queryFn: () => getPlayerFull(playerId, selectedSeason, activeSport, { includeMentions: false }),
  });

  useEffect(() => {
    if (fullData) {
      if (fullData.summary) {
        setPlayerInfo(fullData.summary);
        putSummary(activeSport, 'player', playerId, fullData.summary);
      }
      setPlayerStats(fullData.stats || null);
  // Percentiles removed
      setPlayerProfile(fullData.profile || null);
      const groups = fullData.metrics?.groups || {};
      setMetricsGroups(groups);
      // Default selected group: base if present; otherwise first available group
      const defaultKey = groups.base ? 'base' : Object.keys(groups)[0];
      if (defaultKey) setSelectedGroup(defaultKey);
      setIsLoading(false);
    } else if (fullLoading) {
      setIsLoading(true);
    }
  }, [fullData, fullLoading, playerId, activeSport, putSummary]);

  useEffect(() => {
    if (fullError) {
      setError('Failed to load player data. Please try again later.');
    }
  }, [fullError]);
  
  // Helper function to get color for percentile
  // Percentile color helpers removed
  
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
        {/* Player Header: Basic Entity Card */}
        <BasicEntityCard
          entityType="player"
          sport={activeSport}
          summary={playerInfo ? {
            id: String(playerInfo.id),
            full_name: getPlayerName(),
            first_name: playerInfo.first_name,
            last_name: playerInfo.last_name,
            position: playerInfo.position,
            team_name: playerInfo.team?.name,
            team_id: playerInfo.team_id || playerInfo.team?.id,
            team_abbreviation: playerInfo.team?.abbreviation || playerInfo.team_abbreviation,
            nationality: playerProfile?.country,
            age: playerProfile?.age,
            league: playerProfile?.league,
            years_pro: playerProfile?.years_pro,
          } : null}
          footer={
            <Group position="apart">
              <Button component={Link} to={`/mentions/player/${playerId}`} variant="light">
                Recent Mentions
              </Button>
            </Group>
          }
        />

        {/* API-Sports Player Widget */}
        <Card withBorder p="lg">
          <Title order={3}>Player Widget</Title>
          <ApiSportsWidget
            type="player"
            sport={activeSport}
            data={{
              playerId: playerId,
              playerStatistics: 'true',
              playerTrophies: 'true',
              playerInjuries: 'true',
              season: (selectedSeason && selectedSeason.includes('-')) ? selectedSeason.split('-')[0] : (selectedSeason || new Date().getFullYear().toString()),
            }}
          />
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
              {/* Show a second tab when there is at least one additional metrics group */}
              {Object.keys(metricsGroups).filter(k => k !== 'base').length > 0 && (
                <Tabs.Tab value="metrics">Metrics</Tabs.Tab>
              )}
              <Tabs.Tab value="shooting">Shooting</Tabs.Tab>
              <Tabs.Tab value="advanced">Advanced</Tabs.Tab>
              {Object.keys(metricsGroups).length > 0 && (
                <Tabs.Tab value="raw">Raw Groups</Tabs.Tab>
              )}
            </Tabs.List>

            <Tabs.Panel value="overview" pt="md">
              <Card withBorder p="lg">
                {/* Percentiles removed: radar chart and toggle eliminated */}
                
                <Stack spacing="md">
                  {/* Stats cards with percentile indicators */}
                  <Group grow>
                    <Card withBorder p="md" style={{ position: 'relative' }}>
                      <Text fw={700} size="lg" ta="center">{playerStats.points_per_game.toFixed(1)}</Text>
                      <Text size="sm" c="dimmed" ta="center">PPG</Text>
                      
                    </Card>
                    
                    <Card withBorder p="md" style={{ position: 'relative' }}>
                      <Text fw={700} size="lg" ta="center">{playerStats.rebounds_per_game.toFixed(1)}</Text>
                      <Text size="sm" c="dimmed" ta="center">RPG</Text>
                      
                    </Card>
                    
                    <Card withBorder p="md" style={{ position: 'relative' }}>
                      <Text fw={700} size="lg" ta="center">{playerStats.assists_per_game.toFixed(1)}</Text>
                      <Text size="sm" c="dimmed" ta="center">APG</Text>
                      
                    </Card>
                  </Group>
                  
                  <Group grow>
                    <Card withBorder p="md" style={{ position: 'relative' }}>
                      <Text fw={700} size="lg" ta="center">{playerStats.steals_per_game.toFixed(1)}</Text>
                      <Text size="sm" c="dimmed" ta="center">SPG</Text>
                      
                    </Card>
                    
                    <Card withBorder p="md" style={{ position: 'relative' }}>
                      <Text fw={700} size="lg" ta="center">{playerStats.blocks_per_game.toFixed(1)}</Text>
                      <Text size="sm" c="dimmed" ta="center">BPG</Text>
                      
                    </Card>
                    
                    <Card withBorder p="md" style={{ position: 'relative' }}>
                      <Text fw={700} size="lg" ta="center">{(playerStats.field_goal_percentage * 100).toFixed(1)}%</Text>
                      <Text size="sm" c="dimmed" ta="center">FG%</Text>
                      
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
                          
                        </div>
                      </Group>
                    </Card>
                    
                    <Card withBorder p="md">
                      <Group position="apart" align="center">
                        <div>
                          <Text fw={700} size="lg">{(playerStats.three_point_percentage * 100).toFixed(1)}%</Text>
                          <Text size="sm" c="dimmed">3P%</Text>
                          
                        </div>
                        
                        <div>
                          <Text fw={700} size="lg">{(playerStats.free_throw_percentage * 100).toFixed(1)}%</Text>
                          <Text size="sm" c="dimmed">FT%</Text>
                          
                        </div>
                      </Group>
                    </Card>
                  </Group>
                </Stack>
              </Card>
            </Tabs.Panel>

            {/* Generic metrics tab for additional groups (e.g., NFL/EPL) */}
            <Tabs.Panel value="metrics" pt="md">
              <Card withBorder p="lg">
                {Object.keys(metricsGroups).filter(k => k !== 'base').length === 0 ? (
                  <Text>No additional metrics available.</Text>
                ) : (
                  <>
                    <Group position="apart" mb="sm">
                      <Text fw={600}>Metric Group</Text>
                      <Select
                        value={selectedGroup}
                        onChange={setSelectedGroup}
                        data={Object.keys(metricsGroups).map(k => ({ value: k, label: k.replace(/_/g, ' ') }))}
                        w={240}
                      />
                    </Group>
                    {metricsGroups[selectedGroup] ? (
                      <GenericStatsBarChart
                        stats={metricsGroups[selectedGroup].stats}
                        title={`Metrics: ${selectedGroup.replace(/_/g, ' ')}`}
                      />
                    ) : (
                      <Text>No data for the selected group.</Text>
                    )}
                  </>
                )}
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
            {/* Debug: Render raw metrics groups stacked as cards */}
            {metricsGroups && Object.keys(metricsGroups).length > 0 && (
              <Tabs.Panel value="raw" pt="md">
                <Stack>
                  {Object.entries(metricsGroups).map(([groupKey, groupObj]) => (
                    <Card key={groupKey} withBorder p="md">
                      <Group position="apart" mb="sm">
                        <Text fw={600}>{groupKey.replace(/_/g, ' ')}</Text>
                        {groupObj?.meta?.mode && (
                          <Text size="sm" c="dimmed">mode: {groupObj.meta.mode}</Text>
                        )}
                      </Group>
                      {groupObj?.stats ? (
                        <Stack spacing="xs">
                          {Object.entries(groupObj.stats).map(([k, v]) => (
                            <Group key={k} position="apart">
                              <Text size="sm" c="dimmed">{k.replace(/_/g, ' ')}</Text>
                              <Text fw={500}>{typeof v === 'number' ? v.toFixed(3).replace(/\.000$/, '') : String(v)}</Text>
                            </Group>
                          ))}
                        </Stack>
                      ) : (
                        <Text size="sm" c="dimmed">No stats for this group.</Text>
                      )}
                    </Card>
                  ))}
                </Stack>
              </Tabs.Panel>
            )}
          </Tabs>
        ) : (
          <Text>No statistics available for this player in the selected season.</Text>
        )}
      </Stack>
    </Container>
  );
}

export default PlayerPage;