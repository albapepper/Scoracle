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
import theme from '../theme';
import { useEntityCache } from '../context/EntityCacheContext';

function MentionsPage() {
  const { entityType, entityId } = useParams();
  const { activeSport } = useSportContext();
  const { putSummary } = useEntityCache();
  const [mentions, setMentions] = useState([]);
  const [entityInfo, setEntityInfo] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [alongside, setAlongside] = useState([]);
  
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
        setError('Failed to load mentions. Please try again later.');
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchData();
  }, [entityType, entityId, activeSport]);
  
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
        <Text mt="md">Loading mentions...</Text>
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
          Return to Home
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
            <Title order={3}>Widget Preview</Title>
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
              <Text c="dimmed" size="sm">No API-Sports ID mapped for this {entityType}. Add apisports_id to enable widgets.</Text>
            )}
          </Stack>
  </Card>

        {/* Recent Mentions */}
        <div>
          <Title order={3} mb="sm" style={{ color: theme.colors.text.accent }}>
            Recent Mentions
          </Title>
          <Text c="dimmed" mb="lg">News articles mentioning {getEntityName()}</Text>
          
          <Divider mb="lg" />
          
          {mentions.length === 0 ? (
            <Text>No recent mentions found.</Text>
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
                      Link
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
            Also mentioned
          </Title>
          <Text c="dimmed" mb="lg">Other entities from {activeSport} that appeared in these articles</Text>
          {(!alongside || alongside.length === 0) ? (
            <Text c="dimmed">No co-mentions detected.</Text>
          ) : (
            <List spacing="sm" listStyleType="none">
              {alongside.slice(0, 20).map((e, idx) => (
                <List.Item key={`${e.entity_type}-${e.id}-${idx}`}>
                  <Group position="apart" noWrap>
                    <Text>
                      <Link to={`/mentions/${e.entity_type}/${e.id}?sport=${activeSport}`} style={{ textDecoration: 'none', color: theme.colors.text.primary }}>
                        {e.name || `${e.entity_type} ${e.id}`}
                      </Link>
                    </Text>
                    <Text c="dimmed" size="sm">{e.hits} hits</Text>
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