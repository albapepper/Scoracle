import React, { useMemo } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Container, Title, Card, Group, Button, Stack, Text } from '@mantine/core';
import PlayerWidgetServer from '../components/PlayerWidgetServer';
import { useThemeMode, getThemeColors } from '../theme';
import { useTranslation } from 'react-i18next';
import { useSportContext } from '../context/SportContext';

export default function EntityPage() {
  const { entityType, entityId } = useParams();
  const type = (entityType || '').toLowerCase() === 'team' ? 'team' : 'player';
  const { t } = useTranslation();
  const { activeSport } = useSportContext();
  const season = useMemo(() => String(new Date().getFullYear()), []);
  const { colorScheme } = useThemeMode();
  const colors = getThemeColors(colorScheme);

  // Legacy client-side widgets removed; always use server-rendered widget envelope

  return (
    <Container size="lg" py="xl">
      <Stack spacing="xl">
  <Card withBorder p="lg" style={{ backgroundColor: colors.background.secondary }}>
          <Group position="apart" align="center">
            <Title order={2}>{t('entityPage.title', 'Statistical Profile')}</Title>
            <Button
              component={Link}
              to={`/mentions/${type}/${entityId}?sport=${encodeURIComponent(activeSport)}`}
              variant="light"
            >
              {t('entityPage.recentMentions', 'Recent Mentions')}
            </Button>
          </Group>
        </Card>

  <Card withBorder p="lg" style={{ backgroundColor: colors.background.secondary }}>
          <div id="widget-container">
            {type === 'player' ? (
              <PlayerWidgetServer playerId={entityId} season={season} />
            ) : (
              <Text size="sm" color="dimmed">Team widget (server) coming soon.</Text>
            )}
          </div>
        </Card>
      </Stack>
    </Container>
  );
}
