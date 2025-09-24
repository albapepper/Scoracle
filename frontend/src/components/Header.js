import React from 'react';
import { Link } from 'react-router-dom';
import { Header as MantineHeader, Container, Group, Button, Text, SegmentedControl, Box } from '@mantine/core';
import { useSportContext } from '../context/SportContext';

function Header() {
  const { activeSport, changeSport, sports } = useSportContext();
  
  return (
    <MantineHeader height={60} p="xs">
      <Container size="xl">
        <Group justify="space-between">
          <Link to="/" style={{ textDecoration: 'none' }}>
            <Text size="xl" fw={700} c="primary.7">Scoracle</Text>
          </Link>
          
          <Box>
            <SegmentedControl
              value={activeSport}
              onChange={changeSport}
              data={sports.map(sport => ({
                label: sport.display,
                value: sport.id,
              }))}
              color="primary"
            />
          </Box>
          
          <Group>
            <Button
              component={Link}
              to="/"
              variant="subtle"
            >
              Home
            </Button>
          </Group>
        </Group>
      </Container>
    </MantineHeader>
  );
}

export default Header;