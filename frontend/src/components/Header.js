import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Container, Group, Button, Text, Box, Paper } from '@mantine/core';
import theme from '../theme';

function Header() {
  const location = useLocation();
  const navigate = useNavigate();

  // Determine if we are on the home page
  const isHome = location.pathname === '/';

  const headerStyle = {
    background: `linear-gradient(180deg, ${theme.header.gradientStart} 0%, ${theme.header.gradientEnd} 100%)`,
    border: 'none',
    padding: '0.5rem 0',
  };

  const titleStyle = {
    color: theme.header.title.color,
    fontWeight: 700,
    fontSize: '1.25rem',
    textAlign: 'center',
    margin: 0,
    userSelect: 'none',
  };

  return (
    <Paper component="header" shadow="xs" radius={0} p={0} style={headerStyle}>
      <Container size="xl" style={{ display: 'flex', alignItems: 'center', height: '60px' }}>
        <Group style={{ flex: 1 }}>
          {!isHome && (
            <Button variant="subtle" onClick={() => navigate(-1)} style={{ color: '#fff' }}>
              Back
            </Button>
          )}
        </Group>

        <Box style={{ flex: 2, display: 'flex', justifyContent: 'center' }}>
          {/* On the home page we don't want the title to be clickable; on subpages make it a home link */}
          {isHome ? (
            <Text component="h1" style={titleStyle}>
              Scoracle
            </Text>
          ) : (
            <Link to="/" style={{ textDecoration: 'none' }}>
              <Text component="h1" style={titleStyle}>
                Scoracle
              </Text>
            </Link>
          )}
        </Box>

        <Group style={{ flex: 1, justifyContent: 'flex-end' }}>
          {!isHome && (
            <Button component={Link} to="/" variant="subtle" style={{ color: '#fff' }}>
              Home
            </Button>
          )}
        </Group>
      </Container>
    </Paper>
  );
}

export default Header;