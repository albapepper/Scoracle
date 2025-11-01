import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { Container, Title, Card, Group, Button, Stack } from '@mantine/core';
// Keep page independent of SportContext; use sport from URL only
import ApiSportsWidget from '../components/ApiSportsWidget';
import ApiSportsConfig from '../components/ApiSportsConfig';
import { useTranslation } from 'react-i18next';

export default function EntityPage() {
  const { entityType, entityId } = useParams();
  const type = (entityType || '').toLowerCase() === 'team' ? 'team' : 'player';
  const { t } = useTranslation();
  const [activeSport, setActiveSport] = React.useState('FOOTBALL');

  // Read sport from URL
  React.useEffect(() => {
    try {
      const usp = new URLSearchParams(window.location.search);
      const s = usp.get('sport');
      if (s) setActiveSport(s.toUpperCase());
    } catch (_) {}
  }, []);

  return (
    <Container size="lg" py="xl">
      <Stack spacing="xl">
        <Card withBorder p="lg">
          <Group position="apart" align="center">
            <Title order={2}>{t('mentions.statisticalProfile') || 'Statistical Profile'}</Title>
            <Button component={Link} to={`/mentions/${type}/${entityId}`} variant="light">
              {t('mentions.recent') || 'Recent Mentions'}
            </Button>
          </Group>
        </Card>

        {/* Per-page global config to provide key/host for current sport */}
        <ApiSportsConfig apiKey="4a5a713b507782a9b85c8c4d1d8427a4" sport={activeSport} />

        <Card withBorder p="lg">
          {type === 'player' ? (
            <ApiSportsWidget
              type="player"
              sport={activeSport}
              data={{
                playerId: entityId,
                season: '2025',
                playerStatistics: 'true',
                playerTrophies: 'true',
                playerInjuries: 'true',
              }}
            />
          ) : (
            <ApiSportsWidget
              type="team"
              sport={activeSport}
              data={{
                teamId: entityId,
                teamSquad: 'true',
                teamStatistics: 'true',
              }}
            />
          )}
        </Card>
      </Stack>
    </Container>
  );
}
