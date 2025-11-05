import React, { useMemo } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Container, Title, Card, Group, Button, Stack } from '@mantine/core';
import ApiSportsWidget from '../components/ApiSportsWidget';
import { useTranslation } from 'react-i18next';
import { useSportContext } from '../context/SportContext';

export default function EntityPage() {
  const { entityType, entityId } = useParams();
  const type = (entityType || '').toLowerCase() === 'team' ? 'team' : 'player';
  const { t } = useTranslation();
  const { changeSport } = useSportContext();
  const season = useMemo(() => String(new Date().getFullYear() - 1), []);

  // Read sport from URL
  React.useEffect(() => {
    try {
      const usp = new URLSearchParams(window.location.search);
      const s = usp.get('sport');
      if (s) {
        changeSport(s.toUpperCase());
        return;
      }
    } catch (_) {}
  }, [changeSport]);

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

        <Card withBorder p="lg">
          <ApiSportsWidget
            type={type}
            data={
              type === 'player'
                ? {
                    playerId: entityId,
                    season,
                    playerStatistics: 'true',
                    playerTrophies: 'true',
                    playerInjuries: 'true',
                  }
                : {
                    teamId: entityId,
                    season,
                    teamSquad: 'true',
                    teamStatistics: 'true',
                  }
            }
          />
        </Card>
      </Stack>
    </Container>
  );
}
