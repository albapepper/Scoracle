import React, { useEffect, useState } from 'react';
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
  Divider,
  Box,
  List,
} from '@mantine/core';
import { useTranslation } from 'react-i18next';
import { useSportContext } from '../context/SportContext';
import ApiSportsWidget from '../components/ApiSportsWidget';
import { getEntityMentions } from '../services/api';
import theme from '../theme';

function MentionsPage() {
  const { entityType, entityId } = useParams();
  const { activeSport } = useSportContext();
  const { t } = useTranslation();

  const [mentions, setMentions] = useState([]);
  const [entityInfo, setEntityInfo] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [entityName, setEntityName] = useState('');

  useEffect(() => {
    // read optional name from query params
    try {
      const usp = new URLSearchParams(window.location.search);
      const n = usp.get('name');
      if (n) setEntityName(n);
    } catch (_) {}
  }, []);

  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      setError('');
      try {
        const data = await getEntityMentions(entityType, entityId, activeSport);
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

  if (isLoading) {
    return (
      <Container size="md" py="xl" ta="center">
        <Loader size="xl" color={theme.colors.ui.primary} />
        <Text mt="md">{t('mentions.loading')}</Text>
      </Container>
    );
  }

  if (error) {
    return (
      <Container size="md" py="xl" ta="center">
        <Title order={3} c={theme.colors.status.error}>
          {error}
        </Title>
        <Button
          component={Link}
          to="/"
          mt="md"
          style={{ backgroundColor: theme.colors.ui.primary }}
        >
          {t('common.returnHome')}
        </Button>
      </Container>
    );
  }

  return (
    <Container size="md" py="xl">
      <Stack spacing="xl">
        {/* Header */}
        <Card withBorder p="lg">
          <Group position="apart" align="center">
            <div>
              <Title order={2} style={{ color: theme.colors.text.primary }}>
                {displayName}
              </Title>
            </div>
            <Button
              component={Link}
              to={`/entity/${entityType}/${entityId}`}
              style={{ backgroundColor: theme.colors.ui.primary, color: 'white' }}
              size="md"
            >
              Statistical Profile
            </Button>
          </Group>
        </Card>

        {/* API-Sports Widget (minimal preview) */}
        <Card shadow="sm" p="lg" radius="md" withBorder>
          <Stack>
            <Title order={3}>{t('mentions.widgetPreview')}</Title>
            {entityType === 'team' && entityId && (
              <>
                <ApiSportsWidget
                  type="team"
                  sport={activeSport}
                  data={{ teamId: entityId, teamTab: 'statistics' }}
                />
                <div id="player-container" />
              </>
            )}
            {entityType === 'player' && entityId && (
              <>
                <ApiSportsWidget
                  type="player"
                  sport={activeSport}
                  data={{ playerId: entityId }}
                />
                <div id="player-container" />
              </>
            )}
          </Stack>
        </Card>

        {/* Recent Mentions */}
        <div>
          <Title order={3} mb="sm" style={{ color: theme.colors.text.accent }}>
            {t('mentions.recent')}
          </Title>
          <Text c="dimmed" mb="lg">
            {t('mentions.newsMentioning', { name: displayName })}
          </Text>

          <Divider mb="lg" />

          {mentions.length === 0 ? (
            <Text>{t('mentions.none')}</Text>
          ) : (
            <List spacing="md" listStyleType="none" center>
              {mentions.map((mention, index) => (
                <List.Item key={index}>
                  <Group position="apart" noWrap align="flex-start">
                    <Box style={{ flex: 1 }}>
                      <Text weight={600} size="lg" lineClamp={2}>
                        {mention.title}
                      </Text>
                      <Group spacing="xs" mt={5}>
                        <Text size="sm" c="dimmed">
                          {mention.source} • {new Date(mention.pub_date).toLocaleDateString()}
                        </Text>
                      </Group>
                    </Box>
                    <Button
                      component="a"
                      href={mention.link}
                      target="_blank"
                      rel="noopener noreferrer"
                      variant="outline"
                      compact
                      style={{
                        borderColor: theme.colors.ui.primary,
                        color: theme.colors.ui.primary,
                      }}
                    >
                      {t('common.link')}
                    </Button>
                  </Group>
                  <Divider mt="md" mb="md" />
                </List.Item>
              ))}
            </List>
          )}
        </div>
      </Stack>
    </Container>
  );
}

export default MentionsPage;