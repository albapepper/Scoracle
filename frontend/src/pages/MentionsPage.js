import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Container, Title, Text, Card, Badge, Group, Button, Loader, Stack, Grid, Paper, Anchor } from '@mantine/core';
import { useSportContext } from '../context/SportContext';
import { getEntityMentions } from '../services/api';

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
        setMentions(data.mentions || []);
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
        <Loader size="xl" />
        <Text mt="md">Loading mentions...</Text>
      </Container>
    );
  }
  
  if (error) {
    return (
      <Container size="md" py="xl" ta="center">
        <Title order={3} c="red">{error}</Title>
        <Button component={Link} to="/" mt="md">
          Return to Home
        </Button>
      </Container>
    );
  }
  
  return (
    <Container size="md" py="xl">
      <Stack spacing="xl">
        {/* Entity Information */}
        <Paper p="md" withBorder>
          <Title order={2} mb="md">{getEntityName()}</Title>
          
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
          
          <Group mt="lg">
            <Button
              component={Link}
              to={`/${entityType}/${entityId}`}
              variant="filled"
            >
              View Stats
            </Button>
            <Button
              component={Link}
              to="/"
              variant="outline"
            >
              Back to Home
            </Button>
          </Group>
        </Paper>
        
        {/* Recent Mentions */}
        <div>
          <Title order={3} mb="md">Recent Mentions</Title>
          <Text c="dimmed" mb="md">News from the last 36 hours</Text>
          
          {mentions.length === 0 ? (
            <Text>No recent mentions found.</Text>
          ) : (
            <Stack spacing="md">
              {mentions.map((mention, index) => (
                <Card key={index} withBorder shadow="sm">
                  <Group position="apart" mb="xs">
                    <Title order={4}>{mention.title}</Title>
                    <Badge>{mention.source}</Badge>
                  </Group>
                  <Text lineClamp={3} mb="md">
                    {mention.description}
                  </Text>
                  <Group position="apart">
                    <Text size="sm" c="dimmed">
                      {new Date(mention.pub_date).toLocaleDateString()}
                    </Text>
                    <Anchor href={mention.link} target="_blank">
                      Read More
                    </Anchor>
                  </Group>
                </Card>
              ))}
            </Stack>
          )}
        </div>
      </Stack>
    </Container>
  );
}

export default MentionsPage;