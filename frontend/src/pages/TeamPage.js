import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Container, Title, Text, Card, Group, Button, Loader, Stack, Select, Avatar } from '@mantine/core';
import { useSportContext } from '../context/SportContext';
import { getTeamDetails, getTeamRoster } from '../services/api';
import { useQuery } from '@tanstack/react-query';
import { useEntityCache } from '../context/EntityCacheContext';
import BasicEntityCard from '../components/BasicEntityCard';
import ApiSportsWidget from '../components/ApiSportsWidget';
import { useTranslation } from 'react-i18next';

function TeamPage() {
  const { teamId } = useParams();
  const { activeSport } = useSportContext();
  const { getSummary, putSummary } = useEntityCache();
  const { t } = useTranslation();
  const [teamInfo, setTeamInfo] = useState(() => getSummary(activeSport, 'team', teamId) || null);
  const [teamRoster, setTeamRoster] = useState([]);
  const availableSeasons = ['2023-2024', '2022-2023', '2021-2022'];
  const [selectedSeason, setSelectedSeason] = useState('2023-2024'); // Default primarily for widget
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  // removed idSource badge in header refactor
  
  const { data: detailsData, isLoading: detailsLoading, error: detailsError } = useQuery({
    queryKey: ['teamSummary', teamId, activeSport],
    queryFn: () => getTeamDetails(teamId, undefined, activeSport),
  });

  useEffect(() => {
    const fetchRoster = async () => {
      if (!selectedSeason) return;
      try {
        const rosterData = await getTeamRoster(teamId, selectedSeason, activeSport);
        setTeamRoster(rosterData.roster || []);
      } catch (e) { /* ignore roster errors for now */ }
    };
    fetchRoster();
  }, [teamId, selectedSeason, activeSport]);

  useEffect(() => {
    if (detailsData && detailsData.summary) {
      setTeamInfo(detailsData.summary);
      putSummary(activeSport, 'team', teamId, detailsData.summary);
      setIsLoading(false);
    } else if (detailsLoading) {
      setIsLoading(true);
    }
  }, [detailsData, detailsLoading, teamId, activeSport, putSummary]);

  useEffect(() => {
    if (detailsError) {
      setError(t('team.failedLoad'));
    }
  }, [detailsError, t]);
  
  if (isLoading) {
    return (
      <Container size="md" py="xl" ta="center">
        <Loader size="xl" />
        <Text mt="md">{t('team.loading')}</Text>
      </Container>
    );
  }

  if (error) {
    return (
      <Container size="md" py="xl" ta="center">
        <Title order={3} c="red">{t('team.failedLoad')}</Title>
        <Button component={Link} to="/" mt="md">{t('common.returnHome')}</Button>
      </Container>
    );
  }

  return (
    <Container size="lg" py="xl">
      <Stack spacing="xl">
        {/* Team Header: Basic Entity Card */}
        <BasicEntityCard
          entityType="team"
          sport={activeSport}
          summary={teamInfo ? {
            id: String(teamInfo.id),
            name: teamInfo.name,
            abbreviation: teamInfo.abbreviation,
            city: teamInfo.city,
            conference: teamInfo.conference,
            division: teamInfo.division,
            league: teamInfo.league,
          } : null}
          footer={
            <Group position="apart">
              <Button component={Link} to={`/mentions/team/${teamId}`} variant="light">{t('mentions.recent')}</Button>
            </Group>
          }
        />

        {/* API-Sports Team Widget */}
        <Card withBorder p="lg">
          <Title order={3}>{t('team.widget')}</Title>
          <ApiSportsWidget
            type="team"
            sport={activeSport}
            data={{ teamId: teamId, teamStatistics: 'true', teamSquads: 'true' }}
          />
        </Card>

        {/* Season Selector (optional, primarily for widget control) */}
        <Group position="apart">
          <Title order={3}>{t('team.statistics')}</Title>
          <Select
            label={t('team.season')}
            placeholder={t('team.selectSeason')}
            value={selectedSeason}
            onChange={setSelectedSeason}
            data={availableSeasons.map(season => ({ value: season, label: season }))}
            w={200}
          />
        </Group>

        {/* Roster (if available) */}
        <Card withBorder p="md">
          <Title order={4} mb="sm">{t('team.tabs.roster')}</Title>
          {teamRoster.length > 0 ? (
            <Stack spacing="sm">
              {teamRoster.map((player) => (
                <Card key={player.id} withBorder>
                  <Group>
                    <Avatar size="md" radius="xl" color="blue">
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
                    <Button component={Link} to={`/player/${player.id}`} variant="subtle" size="sm">
                      {t('common.viewStats')}
                    </Button>
                  </Group>
                </Card>
              ))}
            </Stack>
          ) : (
            <Text>{t('team.noRosterInfo')}</Text>
          )}
        </Card>
      </Stack>
    </Container>
  );
}

export default TeamPage;