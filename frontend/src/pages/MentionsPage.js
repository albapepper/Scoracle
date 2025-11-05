import React, { useEffect, useMemo, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  Container,
  Title,
  Text,
  Card,
  Group,
  Button,
  Loader,
  Stack,
  Image,
  Tabs,
  Box,
} from '@mantine/core';
import { useTranslation } from 'react-i18next';
import ApiSportsWidget from '../components/ApiSportsWidget';
import { useThemeMode } from '../ThemeProvider';
import { getThemeColors } from '../theme';
import { getEntityMentions as fetchEntityMentions } from '../services/api';
import ApiSportsConfig from '../components/ApiSportsConfig';
import { useSportContext } from '../context/SportContext';

function MentionsPage() {
  const { entityType, entityId } = useParams();
  // Read sport from query string only
  const { activeSport: contextSport, changeSport } = useSportContext();
  const [activeSport, setActiveSport] = useState(contextSport || 'FOOTBALL');
  const { t } = useTranslation();
  const { colorScheme } = useThemeMode();
  const colors = getThemeColors(colorScheme);
  const season = useMemo(() => String(new Date().getFullYear() - 1), []);

  const [mentions, setMentions] = useState([]);
  const [entityInfo, setEntityInfo] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [entityName, setEntityName] = useState('');

  useEffect(() => {
    try {
      const usp = new URLSearchParams(window.location.search);
      const n = usp.get('name');
      if (n) setEntityName(n);
      const s = usp.get('sport');
    if (s) {
      const upper = s.toUpperCase();
      setActiveSport(upper);
      changeSport(upper);
      return;
    }
    } catch (_) {}
  setActiveSport(contextSport || 'FOOTBALL');
}, [changeSport, contextSport]);

  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      setError('');
      try {
        const data = await fetchEntityMentions(entityType, entityId, activeSport);
        const sortedMentions = (data.mentions || []).sort(
          (a, b) => new Date(b.pub_date) - new Date(a.pub_date)
        );
        setMentions(sortedMentions);
        setEntityInfo(data.entity_info || null);
      } catch (err) {
        setError(t('mentions.failedLoad'));
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };
    fetchData();
  }, [entityType, entityId, activeSport, t]);

  const displayName = entityName || (entityType === 'player'
    ? [entityInfo?.first_name, entityInfo?.last_name].filter(Boolean).join(' ').trim()
    : entityInfo?.name) || `${entityType} ${entityId}`;

  return (
    <Container size="md" py="xl">
      <Stack spacing="xl">
        {isLoading && (
          <Stack spacing="lg" align="center">
            <Loader size="xl" color={colors.ui.primary} />
            <Text mt="md">{t('mentions.loading')}</Text>
          </Stack>
        )}

        {error && !isLoading && (
          <Stack spacing="lg" align="center">
            <Title order={3} c={colors.status.error}>
              {error}
            </Title>
            <Button
              component={Link}
              to="/"
              mt="md"
              style={{ backgroundColor: colors.ui.primary }}
            >
              {t('common.returnHome')}
            </Button>
          </Stack>
        )}

        {!isLoading && !error && (
          <>
        {/* Widget + profile card */}
        <Card shadow="sm" p="lg" radius="md" withBorder>
          <Stack spacing="lg" align="center">
            <Title order={2} style={{ color: colors.text.primary, textAlign: 'center' }}>
                {displayName}
              </Title>
            <Stack w="100%" align="center">
              {entityId && (
                <Box w="100%" style={{ display: 'flex', justifyContent: 'center' }}>
                  <ApiSportsWidget
                    type={entityType}
                    data={
                      entityType === 'team'
                        ? {
                            teamId: entityId,
                                teamSquad: 'true',
                                teamStatistics: 'true',
                          }
                        : {
                            playerId: entityId,
                            season,
                                playerStatistics: 'true',
                                playerTrophies: 'true',
                                playerInjuries: 'true',
                          }
                    }
                  />
                </Box>
              )}
            </Stack>
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

        {/* Content tabs */}
        <Card shadow="sm" p="lg" radius="md" withBorder>
          <Tabs defaultValue="articles">
            <Tabs.List justify="center">
              <Tabs.Tab value="articles">{t('mentions.articlesTab', 'Articles')}</Tabs.Tab>
              <Tabs.Tab value="tweets">{t('mentions.tweetsTab', 'Tweets')}</Tabs.Tab>
              <Tabs.Tab value="reddit">{t('mentions.redditTab', 'Reddit')}</Tabs.Tab>
            </Tabs.List>

            <Tabs.Panel value="articles" pt="md">
          {mentions.length === 0 ? (
            <Text>{t('mentions.none')}</Text>
          ) : (
                <Stack spacing="lg">
                  {mentions.map((mention, index) => {
                    const description = mention.description
                      ? mention.description.replace(/<[^>]*>/g, '').replace(/\s+/g, ' ').trim()
                      : '';
                    const formattedDate = mention.pub_date
                      ? new Date(mention.pub_date).toLocaleDateString()
                      : '';
                    const meta = [mention.source, formattedDate].filter(Boolean).join(' • ');

                    return (
                      <Card
                        key={`${mention.link || index}`}
                        shadow="sm"
                        p="lg"
                        radius="md"
                        withBorder
                      >
                        <Stack spacing="sm">
                          <Group align="flex-start" spacing="lg">
                            {mention.image_url && (
                              <Image
                                src={mention.image_url}
                                alt={mention.title}
                                radius="md"
                                width={120}
                                height={80}
                                fit="cover"
                                withPlaceholder
                              />
                            )}
                            <Stack spacing="xs" style={{ flex: 1 }}>
                      <Text weight={600} size="lg" lineClamp={2}>
                        {mention.title}
                      </Text>
                              {description && (
                                <Text size="sm" c="dimmed" lineClamp={3}>
                                  {description}
                                </Text>
                              )}
                            </Stack>
                          </Group>
                          <Group position="apart" align="center" mt="xs" spacing="md">
                            {meta && (
                        <Text size="sm" c="dimmed">
                                {meta}
                        </Text>
                            )}
                    <Button
                      component="a"
                      href={mention.link}
                      target="_blank"
                      rel="noopener noreferrer"
                      variant="outline"
                      size="compact-sm"
                      style={{
                                borderColor: colors.ui.primary,
                                color: colors.ui.primary,
                      }}
                    >
                      {t('common.link')}
                    </Button>
                  </Group>
                        </Stack>
                      </Card>
                    );
                  })}
                </Stack>
              )}
            </Tabs.Panel>

            <Tabs.Panel value="tweets" pt="md">
              <Text c="dimmed">
                {t('mentions.tweetsComingSoon', 'Twitter feed coming soon.')}
              </Text>
            </Tabs.Panel>

            <Tabs.Panel value="reddit" pt="md">
              <Text c="dimmed">
                {t('mentions.redditComingSoon', 'Reddit feed coming soon.')}
              </Text>
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