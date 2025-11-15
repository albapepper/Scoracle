import React, { useEffect, useMemo, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Container, Title, Text, Card, Group, Button, Loader, Stack, Tabs, Box, Badge } from '@mantine/core';
import { useTranslation } from 'react-i18next';
import { useThemeMode, getThemeColors } from '../../theme';
import { useSportContext } from '../../context/SportContext';
import Widget from '../../components/Widget';
import { useFastNewsByEntity } from '../../features/news/useFastNews';

type Params = { entityType?: string; entityId?: string };

function MentionsPage() {
  const { entityType, entityId } = useParams<Params>();
  const type = (entityType || '').toLowerCase();
    const { activeSport, changeSport: setSport } = useSportContext();
  const { t } = useTranslation();
  const { colorScheme } = useThemeMode();
  const colors = getThemeColors(colorScheme);

  const [error, setError] = useState<string>('');
  const [entityName, setEntityName] = useState<string>('');

  useEffect(() => {
    try {
      const usp = new URLSearchParams(window.location.search);
      const n = usp.get('name');
      if (n) setEntityName(n);
    const s = usp.get('sport');
        if (s) setSport(s.toUpperCase());
    } catch (_) {}
  }, [setSport]);

  // Use fast news endpoint for both articles and rankings - uses entity-based endpoint
  const { data: fastNews, isLoading: fastLoading, error: fastError } = useFastNewsByEntity({
    entityType: type,
    entityId: entityId || '',
    mode: (type === 'player' ? 'player' : (type === 'team' ? 'team' : 'auto')) as any,
    hours: 48,
    enabled: !!entityType && !!entityId,
  });

  // Build widget URL for basic widget
  const widgetUrl = entityType && entityId 
    ? `/api/v1/${activeSport}/${entityType}s/${entityId}/widget/basic`
    : '';

  useEffect(() => {
    if (fastError) setError(t('mentions.failedLoad'));
    else setError('');
  }, [fastError, t]);

  const displayName = entityName || `${entityType} ${entityId}`;

  const mentions = useMemo(() => {
    const arr = (fastNews as any)?.articles || [];
    return [...arr].sort((a, b) => {
      const dateA = a.pub_date ? new Date(a.pub_date).getTime() : 0;
      const dateB = b.pub_date ? new Date(b.pub_date).getTime() : 0;
      return dateB - dateA;
    });
  }, [fastNews]);

  return (
    <Container size="md" py="xl">
      <Stack gap="xl">
        {/* Entity Info Card - Always visible, loads immediately */}
        <Card shadow="sm" p="lg" radius="md" withBorder>
          <Stack gap="lg" align="center">
            <Title order={2} style={{ color: colors.text.primary, textAlign: 'center' }}>{displayName}</Title>
            <Box w="100%" style={{ display: 'flex', justifyContent: 'center' }}>
              {widgetUrl && <Widget url={widgetUrl} />}
            </Box>
            <Button
              component={Link}
              to={`/entity/${entityType}/${entityId}?sport=${encodeURIComponent(activeSport)}`}
              style={{ backgroundColor: colors.ui.primary, color: 'white' }}
              size="md"
              fullWidth
            >
              {t('mentions.statisticalProfile')}
            </Button>
          </Stack>
        </Card>

        {/* Articles Card - Shows immediately with loading state inside */}
        <Card shadow="sm" p="lg" radius="md" withBorder>
          <Tabs defaultValue="articles">
            <Tabs.List justify="center">
              <Tabs.Tab value="articles">{t('mentions.articlesTab', 'Articles')}</Tabs.Tab>
              <Tabs.Tab value="rankings">{t('mentions.rankingsTab', 'Rankings')}</Tabs.Tab>
              <Tabs.Tab value="tweets">{t('mentions.tweetsTab', 'Tweets')}</Tabs.Tab>
              <Tabs.Tab value="reddit">{t('mentions.redditTab', 'Reddit')}</Tabs.Tab>
            </Tabs.List>
            <Tabs.Panel value="articles" pt="md">
              {fastLoading ? (
                <Stack gap="md" align="center" py="xl">
                  <Loader size="md" color={colors.ui.primary} />
                  <Text c="dimmed">{t('mentions.loading')}</Text>
                </Stack>
              ) : error ? (
                <Stack gap="md" align="center" py="xl">
                  <Text c={colors.status.error}>{error}</Text>
                </Stack>
              ) : mentions.length === 0 ? (
                <Text>{t('mentions.none')}</Text>
              ) : (
                <Stack gap="lg">
                  {mentions.map((mention: any, index: number) => (
                    <Card key={`${mention.link || index}`} shadow="sm" p="lg" radius="md" withBorder>
                      <Stack gap="sm">
                        <Group align="flex-start" gap="lg">
                          <Stack gap="xs" style={{ flex: 1 }}>
                            <Text fw={600} size="lg" lineClamp={2}>{mention.title}</Text>
                          </Stack>
                        </Group>
                        <Group justify="space-between" align="center" mt="xs" gap="md">
                          <Text size="sm" c="dimmed">{[mention.source, mention.pub_date ? new Date(mention.pub_date).toLocaleDateString() : ''].filter(Boolean).join(' • ')}</Text>
                          <Button component="a" href={mention.link} target="_blank" rel="noopener noreferrer" variant="outline" size="compact-sm" style={{ borderColor: colors.ui.primary, color: colors.ui.primary }}>
                            {t('common.link')}
                          </Button>
                        </Group>
                      </Stack>
                    </Card>
                  ))}
                </Stack>
              )}
            </Tabs.Panel>
            <Tabs.Panel value="rankings" pt="md">
              {fastLoading ? (
                <Stack gap="md" align="center" py="xl">
                  <Loader size="sm" color={colors.ui.primary} />
                </Stack>
              ) : fastNews ? (
                <Stack gap="sm">
                  {type === 'player' && (
                    <>
                      <Title order={5}>{t('mentions.linkedTeams', 'Linked Teams')}</Title>
                      <Stack gap={6}>
                        {(fastNews as any).linked_teams?.slice(0, 12).map((row: any) => (
                          <Group key={row[0]} justify="space-between">
                            <Text>{row[0]}</Text>
                            <Badge>{row[1]}</Badge>
                          </Group>
                        )) || <Text c="dimmed">{t('mentions.none')}</Text>}
                      </Stack>
                    </>
                  )}
                  {type === 'team' && (
                    <>
                      <Title order={5}>{t('mentions.linkedPlayers', 'Linked Players')}</Title>
                      <Stack gap={6}>
                        {(fastNews as any).linked_players?.slice(0, 12).map((row: any) => (
                          <Group key={row[0]} justify="space-between">
                            <Text>{row[0]}</Text>
                            <Badge>{row[1]}</Badge>
                          </Group>
                        )) || <Text c="dimmed">{t('mentions.none')}</Text>}
                      </Stack>
                    </>
                  )}
                </Stack>
              ) : (
                <Text c="dimmed">{t('mentions.none')}</Text>
              )}
            </Tabs.Panel>
            <Tabs.Panel value="tweets" pt="md">
              <Text c="dimmed">{t('mentions.tweetsComingSoon', 'Twitter feed coming soon.')}</Text>
            </Tabs.Panel>
            <Tabs.Panel value="reddit" pt="md">
              <Text c="dimmed">{t('mentions.redditComingSoon', 'Reddit feed coming soon.')}</Text>
            </Tabs.Panel>
          </Tabs>
        </Card>
      </Stack>
    </Container>
  );
}

export default MentionsPage;
