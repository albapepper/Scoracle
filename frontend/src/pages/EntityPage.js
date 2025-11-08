import React, { useMemo, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Container, Title, Card, Group, Button, Stack, Text } from '@mantine/core';
import ApiSportsConfig from '../components/ApiSportsConfig';
import PlayerWidgetServer from '../components/PlayerWidgetServer';
import { FEATURES } from '../config';
import { useTranslation } from 'react-i18next';
import { useSportContext } from '../context/SportContext';
import { useThemeMode } from '../ThemeProvider';

export default function EntityPage() {
  const { entityType, entityId } = useParams();
  const type = (entityType || '').toLowerCase() === 'team' ? 'team' : 'player';
  const { t } = useTranslation();
  const { activeSport } = useSportContext();
  const { colorScheme } = useThemeMode();
  const season = useMemo(() => String(new Date().getFullYear()), []);

  // Legacy widget script injection only if feature flag disables server widgets
  useEffect(() => {
    if (FEATURES.USE_SERVER_WIDGETS) return; // skip script path
    const scriptId = 'api-sports-widget-script';
    document.getElementById(scriptId)?.remove();
    const script = document.createElement('script');
    script.id = scriptId;
    script.src = `/widgets_3_1_0.js`; // use local copy for ORB/CORS avoidance
    script.async = true;
    script.type = 'module';
    document.body.appendChild(script);
    return () => { document.getElementById(scriptId)?.remove(); };
  }, [entityId, type]);

  return (
    <Container size="lg" py="xl">
      <Stack spacing="xl">
        <Card withBorder p="lg">
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

        <Card withBorder p="lg">
          <div id="widget-container">
            {FEATURES.USE_SERVER_WIDGETS ? (
              type === 'player' ? (
                <PlayerWidgetServer playerId={entityId} season={season} />
              ) : (
                <Text size="sm" color="dimmed">Team widget (server) coming soon.</Text>
              )
            ) : (
              // Fallback legacy widget path
              type === 'player' ? (
                <api-sports-widget
                  data-type="player"
                  data-player-id={entityId}
                  data-season={season}
                  data-player-statistics="true"
                  data-player-trophies="true"
                  data-player-injuries="true"
                ></api-sports-widget>
              ) : (
                <api-sports-widget
                  data-type="team"
                  data-team-id={entityId}
                  data-season={season}
                  data-team-squad="true"
                  data-team-statistics="true"
                ></api-sports-widget>
              )
            )}
            {!FEATURES.USE_SERVER_WIDGETS && (
              <ApiSportsConfig
                sport={activeSport}
                theme={colorScheme === 'dark' ? 'grey' : 'white'}
              />
            )}
          </div>
        </Card>
      </Stack>
    </Container>
  );
}
