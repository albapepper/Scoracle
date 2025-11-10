import React, { useEffect, useMemo, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Container, Title, Text, Card, Group, Button, Loader, Stack, Image, Tabs, Box, Badge } from '@mantine/core';
import { useTranslation } from 'react-i18next';
import { useThemeMode, getThemeColors } from '../../theme';
import { useSportContext } from '../../context/SportContext';
import { useEntityMentions } from '../../features/entities/hooks/useEntityMentions';
import { useWidgetEnvelope } from '../../features/widgets/useWidgetEnvelope';
import { useFastNews } from '../../features/news/useFastNews';

type Params = { entityType?: string; entityId?: string };

function MentionsPage() {
  const { entityType, entityId } = useParams<Params>();
  const type = (entityType || '').toLowerCase();
    const { activeSport, changeSport: setSport } = useSportContext();
  const { t } = useTranslation();
  const { colorScheme } = useThemeMode();
  const colors = getThemeColors(colorScheme);
  const season = useMemo(() => String(new Date().getFullYear()), []);

  const [entityInfo, setEntityInfo] = useState<any>(null);
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

  const { data: widgetEnv, isLoading: widgetLoading, error: widgetErrorObj } = useWidgetEnvelope(
    entityType,
    entityId,
    { sport: activeSport, season } as any
  );
  const widgetError = widgetErrorObj ? (widgetErrorObj as any).message || 'Failed to load widget' : '';

  const { data: mentionsData, isLoading: mentionsLoading, error: mentionsError } = useEntityMentions(
    entityType,
    entityId,
    activeSport
  );

  useEffect(() => {
    if (mentionsError) setError(t('mentions.failedLoad'));
    else setError('');
    setEntityInfo((mentionsData as any)?.entity_info || null);
  }, [mentionsError, mentionsData, t]);

  const mentions = useMemo(() => {
    const arr = (mentionsData as any)?.mentions || [];
    return [...arr].sort((a, b) => new Date(b.pub_date).getTime() - new Date(a.pub_date).getTime());
  }, [mentionsData]);

  const displayName = entityName || (type === 'player'
    ? [entityInfo?.first_name, entityInfo?.last_name].filter(Boolean).join(' ').trim()
    : entityInfo?.name) || `${entityType} ${entityId}`;

  const { data: fastNews, isLoading: fastLoading } = useFastNews({
    query: displayName,
    mode: (type === 'player' ? 'player' : (type === 'team' ? 'team' : 'auto')) as any,
    hours: 48,
    enabled: !!displayName,
  });

  return (
    <Container size="md" py="xl">
      <Stack gap="xl">
        {(mentionsLoading || widgetLoading) && (
          <Stack gap="lg" align="center">
            <Loader size="xl" color={colors.ui.primary} />
            <Text mt="md">{t('mentions.loading')}</Text>
          </Stack>
        )}

        {error && !(mentionsLoading || widgetLoading) && (
          <Stack gap="lg" align="center">
            <Title order={3} c={colors.status.error}>{error}</Title>
            <Button component={Link} to="/" mt="md" style={{ backgroundColor: colors.ui.primary }}>
              {t('common.returnHome')}
            </Button>
          </Stack>
        )}

        {!(mentionsLoading || widgetLoading) && !error && (
          <>
            <Card shadow="sm" p="lg" radius="md" withBorder>
              <Stack gap="lg" align="center">
                <Title order={2} style={{ color: colors.text.primary, textAlign: 'center' }}>{displayName}</Title>
                <Box w="100%" style={{ display: 'flex', justifyContent: 'center' }}>
                  <div id="widget-container" style={{ width: '100%' }}>
                    {widgetError && <Text size="sm" c="red" ta="center">{widgetError}</Text>}
                    {!widgetError && !widgetEnv && <Loader size="sm" />}
                    {widgetEnv && (widgetEnv as any).payload && !(widgetEnv as any).payload.error && (
                      <Card withBorder shadow="xs" p="sm" radius="md" style={{ overflow: 'hidden' }}>
                        <Title order={4} ta="center" mb="xs">{displayName}</Title>
                        <Text size="xs" c="dimmed" ta="center">Widget v{(widgetEnv as any).version}</Text>
                        {(widgetEnv as any).payload.statistics && Object.keys((widgetEnv as any).payload.statistics).length > 0 ? (
                          <Stack gap={4} mt="sm">
                            {Object.entries((widgetEnv as any).payload.statistics).slice(0, 6).map(([k,v]) => (
                              <Group key={k} justify="space-between">
                                <Text size="xs" c="dimmed">{k}</Text>
                                <Text size="xs" fw={500}>{String(v)}</Text>
                              </Group>
                            ))}
                          </Stack>
                        ) : (
                          <Text size="xs" ta="center" c="dimmed" mt="sm">No statistics available.</Text>
                        )}
                      </Card>
                    )}
                    {widgetEnv && (widgetEnv as any).payload && (widgetEnv as any).payload.error && (
                      <Text size="sm" c="red" ta="center">{(widgetEnv as any).payload.error}</Text>
                    )}
                  </div>
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
            <Card shadow="sm" p="lg" radius="md" withBorder>
              <Tabs defaultValue="articles">
                <Tabs.List justify="center">
                  <Tabs.Tab value="articles">{t('mentions.articlesTab', 'Articles')}</Tabs.Tab>
                  <Tabs.Tab value="rankings">{t('mentions.rankingsTab', 'Rankings')}</Tabs.Tab>
                  <Tabs.Tab value="tweets">{t('mentions.tweetsTab', 'Tweets')}</Tabs.Tab>
                  <Tabs.Tab value="reddit">{t('mentions.redditTab', 'Reddit')}</Tabs.Tab>
                </Tabs.List>
                <Tabs.Panel value="articles" pt="md">
                  {mentions.length === 0 ? (
                    <Text>{t('mentions.none')}</Text>
                  ) : (
                    <Stack gap="lg">
                      {mentions.map((mention: any, index: number) => (
                        <Card key={`${mention.link || index}`} shadow="sm" p="lg" radius="md" withBorder>
                          <Stack gap="sm">
                            <Group align="flex-start" gap="lg">
                              {mention.image_url && (
                                <Image src={mention.image_url} alt={mention.title} radius="md" width={120} height={80} fit="cover" />
                              )}
                              <Stack gap="xs" style={{ flex: 1 }}>
                                <Text fw={600} size="lg" lineClamp={2}>{mention.title}</Text>
                                {mention.description && (
                                  <Text size="sm" c="dimmed" lineClamp={3}>{mention.description.replace(/<[^>]*>/g, '').replace(/\s+/g, ' ').trim()}</Text>
                                )}
                              </Stack>
                            </Group>
                            <Group justify="space-between" align="center" mt="xs" gap="md">
                              <Text size="sm" c="dimmed">{[mention.source, new Date(mention.pub_date).toLocaleDateString()].filter(Boolean).join(' • ')}</Text>
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
                  {fastLoading && <Loader size="sm" />}
                  {!fastLoading && fastNews && (
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
          </>
        )}
      </Stack>
    </Container>
  );
}

export default MentionsPage;
