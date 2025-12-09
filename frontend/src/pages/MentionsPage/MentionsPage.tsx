import React, { useEffect, useMemo, useState } from 'react';
import { useParams, Link, useLocation } from 'react-router-dom';
import { Container, Title, Text, Card, Group, Button, Loader, Stack, Tabs, Box } from '@mantine/core';
import { useTranslation } from 'react-i18next';
import { useThemeMode, getThemeColors } from '../../theme';
import { useSportContext } from '../../context/SportContext';
import Widget from '../../components/Widget';
import { useEntity } from '../../features/entities/hooks/useEntity';
import { getEntityNameFromUrl, buildEntityUrl } from '../../utils/entityName';

type Params = { entityType?: string; entityId?: string };

function MentionsPage() {
  const { entityType, entityId } = useParams<Params>();
  const type = (entityType || '').toLowerCase() as 'player' | 'team';
  const { activeSport, changeSport: setSport } = useSportContext();
  const { t } = useTranslation();
  const { colorScheme } = useThemeMode();
  const colors = getThemeColors(colorScheme);

  const [entityName, setEntityName] = useState<string>('');
  const { search } = useLocation();
  
  useEffect(() => {
    try {
      const usp = new URLSearchParams(search);
      const n = getEntityNameFromUrl(search);
      if (n) setEntityName(n);
      const s = usp.get('sport');
      if (s) setSport(s.toUpperCase());
    } catch (_) {}
  }, [search, setSport]);

  // Use unified entity API - gets entity info, widget, and news in one call
  const { data: entityData, isLoading, error } = useEntity({
    entityType: type === 'team' ? 'team' : 'player',
    entityId: entityId || '',
    includeWidget: true,
    includeNews: true,
    enabled: !!entityType && !!entityId,
  });

  // Use entity name from API if available
  const displayName = entityData?.entity?.name || entityName || `${entityType} ${entityId}`;

  // Sort mentions by date
  const mentions = useMemo(() => {
    const arr = entityData?.news?.articles || [];
    return [...arr].sort((a, b) => {
      const dateA = a.pub_date ? new Date(a.pub_date).getTime() : 0;
      const dateB = b.pub_date ? new Date(b.pub_date).getTime() : 0;
      return dateB - dateA;
    });
  }, [entityData?.news?.articles]);

  return (
    <Container size="md" py="xl">
      <Stack gap="xl">
        {/* Entity Info Card */}
        <Card shadow="sm" p="lg" radius="md" withBorder>
          <Stack gap="lg" align="center">
            <Title order={2} style={{ color: colors.text.primary, textAlign: 'center' }}>
              {displayName}
            </Title>
            <Box w="100%" style={{ display: 'flex', justifyContent: 'center' }}>
              <Widget 
                data={entityData?.widget}
                loading={isLoading}
                error={error?.message}
              />
            </Box>
            <Button
              component={Link}
              to={buildEntityUrl('/entity', entityType || '', entityId || '', activeSport, displayName)}
              style={{ backgroundColor: colors.ui.primary, color: 'white' }}
              size="md"
              fullWidth
            >
              {t('mentions.profile', 'Profile')}
            </Button>
          </Stack>
        </Card>

        {/* Articles Card */}
        <Card shadow="sm" p="lg" radius="md" withBorder>
          <Tabs defaultValue="articles">
            <Tabs.List justify="center">
              <Tabs.Tab value="articles">{t('mentions.articlesTab', 'Articles')}</Tabs.Tab>
              <Tabs.Tab value="tweets">{t('mentions.tweetsTab', 'Tweets')}</Tabs.Tab>
              <Tabs.Tab value="reddit">{t('mentions.redditTab', 'Reddit')}</Tabs.Tab>
            </Tabs.List>
            <Tabs.Panel value="articles" pt="md">
              {isLoading ? (
                <Stack gap="md" align="center" py="xl">
                  <Loader size="md" color={colors.ui.primary} />
                  <Text c="dimmed">{t('mentions.loading')}</Text>
                </Stack>
              ) : error ? (
                <Stack gap="md" align="center" py="xl">
                  <Text c={colors.status.error}>{error.message}</Text>
                </Stack>
              ) : mentions.length === 0 ? (
                <Text>{t('mentions.none')}</Text>
              ) : (
                <Stack gap="lg">
                  {mentions.map((mention, index) => (
                    <Card key={`${mention.link || index}`} shadow="sm" p="lg" radius="md" withBorder>
                      <Stack gap="sm">
                        <Group align="flex-start" gap="lg">
                          <Stack gap="xs" style={{ flex: 1 }}>
                            <Text fw={600} size="lg" lineClamp={2}>{mention.title}</Text>
                          </Stack>
                        </Group>
                        <Group justify="space-between" align="center" mt="xs" gap="md">
                          <Text size="sm" c="dimmed">
                            {[mention.source, mention.pub_date ? new Date(mention.pub_date).toLocaleDateString() : ''].filter(Boolean).join(' • ')}
                          </Text>
                          <Button 
                            component="a" 
                            href={mention.link} 
                            target="_blank" 
                            rel="noopener noreferrer" 
                            variant="outline" 
                            size="compact-sm" 
                            style={{ borderColor: colors.ui.primary, color: colors.ui.primary }}
                          >
                            {t('common.link')}
                          </Button>
                        </Group>
                      </Stack>
                    </Card>
                  ))}
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
      </Stack>
    </Container>
  );
}

export default MentionsPage;
