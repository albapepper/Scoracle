import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Container, Group, Box, Paper, ActionIcon, Drawer, Switch, Select, Stack } from '@mantine/core';

function Header() {
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [language, setLanguage] = useState('en');
  const [darkMode, setDarkMode] = useState(false); // stub, wire to ThemeProvider later

  const headerStyle = {
    // Solid purple header background per request
    background: '#6f42c1',
    backgroundColor: '#6f42c1',
    border: 'none',
    padding: '0.5rem 0',
  };

  return (
    <Paper component="header" shadow="xs" radius={0} p={0} style={headerStyle}>
      <Container size="xl" style={{ display: 'flex', alignItems: 'center', height: '60px' }}>
        <Group style={{ flex: 1 }}>
          {/* Left: Hamburger opens settings */}
          <ActionIcon variant="subtle" color="white" onClick={() => setSettingsOpen(true)} title="Settings">
            {/* Simple hamburger glyph */}
            <span style={{ display: 'inline-block', width: 20 }}>
              <span style={{ display: 'block', height: 2, background: '#fff', margin: '4px 0' }} />
              <span style={{ display: 'block', height: 2, background: '#fff', margin: '4px 0' }} />
              <span style={{ display: 'block', height: 2, background: '#fff', margin: '4px 0' }} />
            </span>
          </ActionIcon>
        </Group>

        <Box style={{ flex: 2, display: 'flex', justifyContent: 'center' }}>
          {/* Center: Scoracle logo acts as home */}
          <Link to="/" style={{ textDecoration: 'none' }}>
            <img
              src="/scoracle-logo.png"
              alt="Scoracle"
              style={{ height: 36, display: 'block' }}
            />
          </Link>
        </Box>

        <Group style={{ flex: 1, justifyContent: 'flex-end' }}>
          {/* Right: Language selector */}
          <Select
            data={[
              { value: 'en', label: 'EN' },
              { value: 'es', label: 'ES' },
            ]}
            value={language}
            onChange={setLanguage}
            size="xs"
            styles={{ input: { background: 'transparent', color: '#fff', borderColor: 'rgba(255,255,255,0.4)' } }}
          />
        </Group>

        <Drawer opened={settingsOpen} onClose={() => setSettingsOpen(false)} title="Settings">
          <Stack>
            <Switch
              checked={darkMode}
              onChange={(e) => setDarkMode(e.currentTarget.checked)}
              label="Dark mode"
            />
            {/* Additional settings can go here */}
          </Stack>
        </Drawer>
      </Container>
    </Paper>
  );
}

export default Header;