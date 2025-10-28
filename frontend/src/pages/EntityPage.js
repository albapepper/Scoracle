import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { Container, Title, Card, Group, Button, Stack } from '@mantine/core';
import { useSportContext } from '../context/SportContext';
import ApiSportsWidget from '../components/ApiSportsWidget';
import { useTranslation } from 'react-i18next';

export default function EntityPage() {
  const { entityType, entityId } = useParams();
  const type = (entityType || '').toLowerCase() === 'team' ? 'team' : 'player';
  const { activeSport } = useSportContext();
  const { t } = useTranslation();

  return (
    <Container size="lg" py="xl">
      <Stack spacing="xl">
        <Card withBorder p="lg">
          <Group position="apart" align="center">
            <Title order={2}>{t('entity.statisticalProfile') || 'Statistical Profile'}</Title>
            <Button component={Link} to={`/mentions/${type}/${entityId}`} variant="light">
              {t('mentions.recent') || 'Recent Mentions'}
            </Button>
          </Group>
        </Card>

        <Card withBorder p="lg">
          {type === 'player' ? (
            <ApiSportsWidget
              type="player"
              sport={activeSport}
              data={{
                playerId: entityId,
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
                teamTab: 'statistics',
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
