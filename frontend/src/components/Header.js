import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Container, Group, Box, Paper, ActionIcon, Drawer, Switch, Select, Stack, Text, Tooltip } from '@mantine/core';
import { IconMenu2 } from '@tabler/icons-react';
import theme from '../theme';
import { useLanguage } from '../context/LanguageContext';
import { useThemeMode } from '../ThemeProvider';
import { useTranslation } from 'react-i18next';

function Header() {
  const { language, changeLanguage, languages } = useLanguage();
  const { colorScheme, toggleColorScheme } = useThemeMode();
  const isDark = colorScheme === 'dark';
  const { t } = useTranslation();
  const [settingsOpen, setSettingsOpen] = useState(false);

  // Get appropriate header colors based on color scheme
  const headerConfig = theme.header[colorScheme];
  
  const headerStyle = {
    background: `linear-gradient(90deg, ${headerConfig.gradientStart}, ${headerConfig.gradientEnd})`,
    border: 'none',
    padding: '0.5rem 0',
  };

  return (
    <Paper component="header" shadow="xs" radius={0} p={0} style={headerStyle}>
      <Container size="xl" style={{ display: 'flex', alignItems: 'center', height: '60px' }}>
        {/* Left: Hamburger -> settings drawer */}
        <Group style={{ flex: 1 }}>
          <Tooltip label={t('header.menu')} withArrow>
            <ActionIcon variant="subtle" color="gray.1" aria-label="Open menu" onClick={() => setSettingsOpen(true)}>
              <IconMenu2 size={22} color={headerConfig.title.color} />
            </ActionIcon>
          </Tooltip>
        </Group>

        {/* Center: Brand/logo -> home */}
        <Box style={{ flex: 2, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
          <Link to="/" aria-label="Go to home" style={{ textDecoration: 'none' }}>
            <img src="/scoracle-logo.png" alt="Scoracle" style={{ height: 54, display: 'block' }} />
          </Link>
        </Box>

        {/* Right: Language selector */}
        <Group style={{ flex: 1, justifyContent: 'flex-end' }}>
          <Select
            aria-label={t('header.language') || 'Select language'}
            data={languages.map((l) => ({ value: l.id, label: l.display }))}
            value={language}
            onChange={(v) => v && changeLanguage(v)}
            size="xs"
            styles={{ input: { background: 'transparent', color: headerConfig.title.color, borderColor: 'rgba(255,255,255,0.4)' } }}
          />
        </Group>

        {/* Settings Drawer - light/dark only for now */}
        <Drawer opened={settingsOpen} onClose={() => setSettingsOpen(false)} title={t('header.settings')} position="left">
          <Stack>
            <Text fw={600}>{t('header.appearance')}</Text>
            <Switch
              checked={isDark}
              onChange={toggleColorScheme}
              label={t('header.darkMode')}
            />
            <Text fw={600} mt="md">{t('header.language')}</Text>
            <Select
              aria-label={t('header.language') || 'Select language'}
              data={languages.map((l) => ({ value: l.id, label: `${l.display} — ${l.label}` }))}
              value={language}
              onChange={(v) => v && changeLanguage(v)}
            />
          </Stack>
        </Drawer>
      </Container>
    </Paper>
  );
}

export default Header;
