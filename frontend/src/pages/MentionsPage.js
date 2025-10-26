import React, { useState, useEffect } from 'react';
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
  List
} from '@mantine/core';
import { useSportContext } from '../context/SportContext';
import ApiSportsWidget from '../components/ApiSportsWidget';
import BasicEntityCard from '../components/BasicEntityCard';
import { getEntityMentions } from '../services/api';
import { fetchEntitiesDump, buildSimpleIndex, aggregateCoMentions } from '../services/comentions';
import theme from '../theme';
import { useEntityCache } from '../context/EntityCacheContext';
import { useTranslation } from 'react-i18next';

function MentionsPage() {
  const { entityType, entityId } = useParams();
  const { activeSport } = useSportContext();
  const { putSummary } = useEntityCache();
  const { t } = useTranslation();
  const [mentions, setMentions] = useState([]);
  const [entityInfo, setEntityInfo] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [alongside, setAlongside] = useState([]);
  const [computedAlongside, setComputedAlongside] = useState([]);
  
  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      setError('');
      try {
        const data = await getEntityMentions(entityType, entityId, activeSport);
        const sortedMentions = (data.mentions || []).sort((a, b) => (
          new Date(b.pub_date) - new Date(a.pub_date)
        ));
        setMentions(sortedMentions);
        setEntityInfo(data.entity_info || null);
        setAlongside(data.alongside_entities || []);
      } catch (err) {
        setError(t('mentions.failedLoad'));
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchData();
  }, [entityType, entityId, activeSport, t]);

  // Compute co-mentions on the client using the entities dump
  useEffect(() => {
    const runCoMentions = async () => {
      try {
        // Only run when mentions and entityInfo are loaded
        if (!mentions || mentions.length === 0) {
          setComputedAlongside([]);
          return;
        }
        // Fetch minimal entities for this sport
        const [players, teams] = await Promise.all([
          fetchEntitiesDump(activeSport, 'player'),
          fetchEntitiesDump(activeSport, 'team')
        ]);
        const index = buildSimpleIndex(players, teams);
        const target = { entity_type: entityType, id: String(entityId) };
        const agg = aggregateCoMentions(mentions, index, target);
        setComputedAlongside(agg);
      } catch (e) {
        // Non-fatal; keep server-provided alongside if any
        console.warn('Co-mentions computation failed; using server-provided alongside', e);
        setComputedAlongside([]);
      }
    };
    runCoMentions();
  }, [mentions, entityType, entityId, activeSport]);
  
  // Format the entity name
  const getEntityName = () => {
    if (!entityInfo) return '';
    
    if (entityType === 'player') {
      return `${entityInfo.first_name} ${entityInfo.last_name}`;
    } else {
      return entityInfo.name;
    }
  };
  
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
        <Title order={3} c={theme.colors.status.error}>{error}</Title>
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
            <BasicEntityCard
              entityType={entityType}
              sport={activeSport}
              summary={entityType === 'player' ? (
                entityInfo ? {
                  id: String(entityInfo.id),
                  full_name: `${entityInfo.first_name || ''} ${entityInfo.last_name || ''}`.trim(),
                  first_name: entityInfo.first_name,
                  last_name: entityInfo.last_name,
                  position: entityInfo.position,
                  team_name: entityInfo.team?.name,
                  team_id: entityInfo.team?.id ? String(entityInfo.team.id) : null,
                  team_abbreviation: entityInfo.team?.abbreviation,
                  nationality: entityInfo.nationality,
                  age: entityInfo.age,
                  league: entityInfo.league,
                  years_pro: entityInfo.years_pro,
                } : null
              ) : (
                entityInfo ? {
                  id: String(entityInfo.id),
                  name: entityInfo.name,
                  abbreviation: entityInfo.abbreviation,
                  city: entityInfo.city,
                  conference: entityInfo.conference,
                  division: entityInfo.division,
                  league: entityInfo.league,
                } : null
              )}
              actions={
                <Button
                  component={Link}
                  to={entityType === 'player' ? `/player/${entityId}` : `/team/${entityId}`}
                  onClick={() => {
                    if (entityInfo) {
                      // Seed cache for smoother navigation
                      if (entityType === 'player') {
                        putSummary(activeSport, 'player', entityId, {
                          id: String(entityInfo.id),
                          sport: activeSport,
                          first_name: entityInfo.first_name,
                          last_name: entityInfo.last_name,
                          full_name: `${entityInfo.first_name || ''} ${entityInfo.last_name || ''}`.trim(),
                          position: entityInfo.position,
                          team_id: entityInfo.team?.id ? String(entityInfo.team.id) : null,
                          team_name: entityInfo.team?.name,
                          team_abbreviation: entityInfo.team?.abbreviation,
                        });
                      } else {
                        putSummary(activeSport, 'team', entityId, {
                          id: String(entityInfo.id),
                          sport: activeSport,
                          name: entityInfo.name,
                          abbreviation: entityInfo.abbreviation,
                          city: entityInfo.city,
                          conference: entityInfo.conference,
                          division: entityInfo.division,
                        });
                      }
                    }
                  }}
                  style={{ 
                    backgroundColor: theme.colors.ui.primary,
                    color: 'white'
                  }}
                  size="md"
                  fullWidth
                >
                  Statistical Profile
                </Button>
              }
            />
        
        {/* API-Sports Widgets (optional) */}
  <Card shadow="sm" p="lg" radius="md" withBorder>
          <Stack>
            <Title order={3}>{t('mentions.widgetPreview')}</Title>
            {/* Render a widget matching the entity type, when we have a numeric ID */}
            {entityType === 'team' && entityInfo?.id && (
              <>
                <ApiSportsWidget
                  type="team"
                  sport={activeSport}
                  data={{ teamId: entityInfo.id, targetPlayer: '#player-container' }}
                />
                <div id="player-container" />
              </>
            )}
            {entityType === 'player' && entityInfo?.id && (
              <>
                <ApiSportsWidget
                  type="player"
                  sport={activeSport}
                  data={{
                    playerId: entityInfo.id,
                    playerStatistics: 'true',
                    playerTrophies: 'true',
                    playerInjuries: 'true',
                    season: new Date().getFullYear().toString()
                  }}
                />
                {/* Container to receive clicked player details from other widgets via data-target-player */}
                <div id="player-container" />
              </>
            )}
            {/* If we don't have the apisports ID yet, show a hint */}
            {(!entityInfo?.id) && (
              <Text c="dimmed" size="sm">{t('mentions.noApisportsId', { entityType })}</Text>
            )}
          </Stack>
  </Card>

        {/* Recent Mentions */}
        <div>
          <Title order={3} mb="sm" style={{ color: theme.colors.text.accent }}>
            {t('mentions.recent')}
          </Title>
          <Text c="dimmed" mb="lg">{t('mentions.newsMentioning', { name: getEntityName() })}</Text>
          
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
                        color: theme.colors.ui.primary
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

        {/* Also mentioned (co-mentions) */}
        <div>
          <Title order={3} mb="sm" style={{ color: theme.colors.text.accent }}>
            {t('mentions.alsoMentioned')}
          </Title>
          <Text c="dimmed" mb="lg">{t('mentions.otherEntities', { sport: activeSport })}</Text>
          {(!(computedAlongside.length ? computedAlongside : alongside) || (computedAlongside.length ? computedAlongside : alongside).length === 0) ? (
            <Text c="dimmed">{t('mentions.noComentions')}</Text>
          ) : (
            <List spacing="sm" listStyleType="none">
              {(computedAlongside.length ? computedAlongside : alongside).slice(0, 20).map((e, idx) => (
                <List.Item key={`${e.entity_type}-${e.id}-${idx}`}>
                  <Group position="apart" noWrap>
                    <Text>
                      <Link to={`/mentions/${e.entity_type}/${e.id}?sport=${activeSport}`} style={{ textDecoration: 'none', color: theme.colors.text.primary }}>
                        {e.name || `${e.entity_type} ${e.id}`}
                      </Link>
                    </Text>
                    <Text c="dimmed" size="sm">{e.hits} {t('mentions.hits')}</Text>
                  </Group>
                  <Divider mt="xs"/>
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