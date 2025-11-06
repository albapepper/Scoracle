import React, { useMemo, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Container, Title, Card, Group, Button, Stack } from '@mantine/core';
import ApiSportsConfig from '../components/ApiSportsConfig';
import { useTranslation } from 'react-i18next';
import { useSportContext } from '../context/SportContext';
import { useThemeMode } from '../ThemeProvider';

export default function EntityPage() {
  const { entityType, entityId } = useParams();
  const type = (entityType || '').toLowerCase() === 'team' ? 'team' : 'player';
  const { t } = useTranslation();
  const { activeSport, changeSport } = useSportContext();
  const { colorScheme } = useThemeMode();
  const season = useMemo(() => String(new Date().getFullYear()), []);

  useEffect(() => {
    const scriptId = 'api-sports-widget-script';
    document.getElementById(scriptId)?.remove();

    const script = document.createElement('script');
    script.id = scriptId;
    script.src = `https://widgets.api-sports.io/3.1.0/widgets.js?cb=${Date.now()}`;
    script.async = true;
    script.type = 'module';
    script.crossOrigin = 'anonymous';
    
    document.body.appendChild(script);

    return () => {
      document.getElementById(scriptId)?.remove();
    };
  }, [entityId, type]); // Re-run when the entity changes

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
            {type === 'player' ? (
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
            )}
            <ApiSportsConfig
              sport={activeSport}
              theme={colorScheme === 'dark' ? 'grey' : 'white'}
            />
          </div>
        </Card>
      </Stack>
    </Container>
  );
}
