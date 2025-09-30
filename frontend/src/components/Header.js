import React from 'react';
import { Link } from 'react-router-dom';
import { Container, Group, Button, Text, SegmentedControl, Box, Paper } from '@mantine/core';
import { useSportContext } from '../context/SportContext';

function Header() {
  const { activeSport, changeSport, sports } = useSportContext();
  
  return (
    <Paper component="header" shadow="xs" radius={0} p="xs" withBorder>
      <Container size="xl">
        <Group justify="space-between">
          <Link to="/" style={{ textDecoration: 'none' }}>
            <Text size="xl" fw={700} c="primary.7">Scoracle</Text>
          </Link>

          <Box>
            <SegmentedControl
              value={activeSport}
              onChange={changeSport}
              data={sports.map((sport) => ({
                label: sport.display,
                value: sport.id,
              }))}
              color="primary"
            />
          </Box>

          <Group>
            <Button component={Link} to="/" variant="subtle">
              Home
            </Button>
          </Group>
        </Group>
      </Container>
    </Paper>
  );
}

export default Header;