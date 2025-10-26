import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Container, Title, Text, Card, Group, Button, Loader, Stack, Select } from '@mantine/core';
import { useSportContext } from '../context/SportContext';
import { getPlayerDetails, getPlayerSeasons } from '../services/api';
import { useQuery } from '@tanstack/react-query';
import { useEntityCache } from '../context/EntityCacheContext';
import BasicEntityCard from '../components/BasicEntityCard';
import ApiSportsWidget from '../components/ApiSportsWidget';

// Import D3 visualization component
// Server-side stats visualizations removed in lean mode
import { useTranslation } from 'react-i18next';

function PlayerPage() {
  const { playerId } = useParams();
  const { activeSport } = useSportContext();
  const { getSummary, putSummary } = useEntityCache();
  const { t } = useTranslation();
  const [playerInfo, setPlayerInfo] = useState(() => getSummary(activeSport, 'player', playerId) || null); // seed from cache if exists
  // Server-provided stats/percentiles removed in lean mode; widgets provide visuals
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
  
  const { data: detailsData, isLoading: detailsLoading, error: detailsError } = useQuery({
    queryKey: ['playerSummary', playerId, activeSport],
    queryFn: () => getPlayerDetails(playerId, undefined, activeSport),
  });

  useEffect(() => {
    if (detailsData && detailsData.summary) {
      setPlayerInfo(detailsData.summary);
      putSummary(activeSport, 'player', playerId, detailsData.summary);
      setIsLoading(false);
    } else if (detailsLoading) {
      setIsLoading(true);
    }
  }, [detailsData, detailsLoading, playerId, activeSport, putSummary]);

  useEffect(() => {
    if (detailsError) {
      setError('Failed to load player data. Please try again later.');
    }
  }, [detailsError]);
  
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
        <Text mt="md">{t('player.loading')}</Text>
      </Container>
    );
  }
  
  if (error) {
    return (
      <Container size="md" py="xl" ta="center">
        <Title order={3} c="red">{t('player.failedLoad')}</Title>
        <Button component={Link} to="/" mt="md">
          {t('common.returnHome')}
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
            nationality: undefined,
            age: undefined,
            league: undefined,
            years_pro: undefined,
          } : null}
          footer={
            <Group position="apart">
              <Button component={Link} to={`/mentions/player/${playerId}`} variant="light">
                {t('mentions.recent')}
              </Button>
            </Group>
          }
        />

        {/* API-Sports Player Widget */}
        <Card withBorder p="lg">
          <Title order={3}>{t('player.widget')}</Title>
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
          <Title order={3}>{t('player.statistics')}</Title>
          
          <Select
            label={t('player.season')}
            placeholder={t('player.selectSeason')}
            value={selectedSeason}
            onChange={setSelectedSeason}
            data={availableSeasons.map(season => ({
              value: season,
              label: season
            }))}
            w={200}
          />
        </Group>
        
        {/* Stats content is provided by the widget in lean mode */}
      </Stack>
    </Container>
  );
}

export default PlayerPage;