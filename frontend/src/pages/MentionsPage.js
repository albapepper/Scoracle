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
  Grid, 
  Divider,
  Box,
  List
} from '@mantine/core';
import { useSportContext } from '../context/SportContext';
import { getEntityMentions } from '../services/api';
import theme from '../theme';

function MentionsPage() {
  const { entityType, entityId } = useParams();
  const { activeSport } = useSportContext();
  const [mentions, setMentions] = useState([]);
  const [entityInfo, setEntityInfo] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  
  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      setError('');
      
      try {
        const data = await getEntityMentions(entityType, entityId, activeSport);
        
        // Sort mentions by recency (newest first)
        const sortedMentions = (data.mentions || []).sort((a, b) => {
          return new Date(b.pub_date) - new Date(a.pub_date);
        });
        
        setMentions(sortedMentions);
        setEntityInfo(data.entity_info || null);
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
        {/* Entity Information Box */}
        <Card 
          shadow="sm" 
          p="lg" 
          radius="md" 
          withBorder
          style={{ 
            backgroundColor: theme.colors.background.secondary,
            borderColor: theme.colors.ui.border
          }}
        >
          <Stack spacing="md">
            <Title order={2} style={{ color: theme.colors.text.accent }}>
              {getEntityName()}
            </Title>
            
            {entityInfo && (
              <Grid>
                {entityType === 'player' && (
                  <>
                    <Grid.Col span={{ base: 12, md: 6 }}>
                      <Text><strong>Position:</strong> {entityInfo.position || 'N/A'}</Text>
                    </Grid.Col>
                    <Grid.Col span={{ base: 12, md: 6 }}>
                      <Text><strong>Team:</strong> {entityInfo.team?.name || 'N/A'}</Text>
                    </Grid.Col>
                    <Grid.Col span={{ base: 12, md: 6 }}>
                      <Text><strong>Height:</strong> {entityInfo.height || 'N/A'}</Text>
                    </Grid.Col>
                    <Grid.Col span={{ base: 12, md: 6 }}>
                      <Text><strong>Weight:</strong> {entityInfo.weight || 'N/A'}</Text>
                    </Grid.Col>
                    <Grid.Col span={{ base: 12, md: 6 }}>
                      <Text><strong>Jersey #:</strong> {entityInfo.jersey_number || 'N/A'}</Text>
                    </Grid.Col>
                    { (entityInfo.college || entityInfo.draft_year) && (
                      <Grid.Col span={12}>
                        <Text>
                          <strong>Background:</strong> {entityInfo.college ? `${entityInfo.college}` : ''}
                          {entityInfo.college && entityInfo.draft_year ? ' • ' : ''}
                          {entityInfo.draft_year ? `Draft ${entityInfo.draft_year}${entityInfo.draft_round ? ` R${entityInfo.draft_round}` : ''}${entityInfo.draft_number ? ` P${entityInfo.draft_number}` : ''}` : ''}
                        </Text>
                      </Grid.Col>
                    ) }
                  </>
                )}
                
                {entityType === 'team' && (
                  <>
                    <Grid.Col span={{ base: 12, md: 6 }}>
                      <Text><strong>City:</strong> {entityInfo.city || 'N/A'}</Text>
                    </Grid.Col>
                    <Grid.Col span={{ base: 12, md: 6 }}>
                      <Text><strong>Conference:</strong> {entityInfo.conference || 'N/A'}</Text>
                    </Grid.Col>
                  </>
                )}
              </Grid>
            )}
            
            <Box mt="md">
              <Button
                component={Link}
                to={`/${entityType}/${entityId}`}
                style={{ 
                  backgroundColor: theme.colors.ui.primary,
                  color: 'white'
                }}
                size="md"
                fullWidth
              >
                View Stats
              </Button>
            </Box>
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
      </Stack>
    </Container>
  );
}

export default MentionsPage;