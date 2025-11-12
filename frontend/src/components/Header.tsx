import React, { useState } from 'react';
import './Header.css';
import { Link } from 'react-router-dom';
import { Container, Group, Box, Paper, ActionIcon, Drawer, Switch, Select, Stack, Text, Tooltip } from '@mantine/core';
import { IconMenu2 } from '@tabler/icons-react';
import { useThemeMode, getThemeColors } from '../theme';
import { useLanguage } from '../context/LanguageContext';
import { useTranslation } from 'react-i18next';

const Header: React.FC = () => {
  const { language, changeLanguage, languages } = useLanguage() as {
    language: string;
    changeLanguage: (lang: string) => void;
    languages: Array<{ id: string; display: string; label: string }>;
  };
  const { colorScheme, toggleColorScheme } = useThemeMode();
  const isDark = colorScheme === 'dark';
  const { t } = useTranslation();
  const [settingsOpen, setSettingsOpen] = useState(false);

  // Get appropriate header colors based on color scheme
  const colors = getThemeColors(colorScheme);

  const headerStyle: React.CSSProperties = {
    background: colors.background.primary,
    borderBottom: `1px solid ${colors.ui.border}`,
    padding: '0.5rem 0',
  };

  return (
    <Paper component="header" shadow="none" radius={0} p={0} style={headerStyle}>
      <Container size="xl" px="md" style={{ display: 'flex', alignItems: 'center', height: '60px', justifyContent: 'space-between', position: 'relative' }}>
        {/* Left: Hamburger -> settings drawer */}
        <Group style={{ flexShrink: 0 }}>
          <Tooltip label={t('header.menu')} withArrow>
            <ActionIcon variant="subtle" color="gray" aria-label="Open menu" onClick={() => setSettingsOpen(true)}>
              <IconMenu2 size={22} color={colors.text.primary} />
            </ActionIcon>
          </Tooltip>
        </Group>

        {/* Center: Brand/logo -> home */}
        <Box style={{ position: 'absolute', left: '50%', transform: 'translateX(-50%)', display: 'flex', alignItems: 'center' }}>
          <Link to="/" aria-label="Go to home" style={{ textDecoration: 'none' }}>
            <img src="/scoracle-logo.png" alt="Scoracle" className="header-logo" />
          </Link>
        </Box>

        {/* Right: Language selector */}
        <Group style={{ flexShrink: 0 }}>
          <Select
            aria-label={t('header.language') || 'Select language'}
            data={languages.map((l) => ({ value: l.id, label: l.display }))}
            value={language}
            onChange={(v) => v && changeLanguage(v || language)}
            size="xs"
            styles={{ input: { background: 'transparent', color: colors.text.primary, borderColor: colors.ui.border } }}
          />
        </Group>

        {/* Settings Drawer - light/dark only for now */}
        <Drawer opened={settingsOpen} onClose={() => setSettingsOpen(false)} title={t('header.settings')} position="left">
          <Stack>
            <Text fw={600}>{t('header.appearance')}</Text>
            <Switch checked={isDark} onChange={toggleColorScheme} label={t('header.darkMode')} />
            <Text fw={600} mt="md">{t('header.language')}</Text>
            <Select
              aria-label={t('header.language') || 'Select language'}
              data={languages.map((l) => ({ value: l.id, label: `${l.display} — ${l.label}` }))}
              value={language}
              onChange={(v) => v && changeLanguage(v || language)}
            />
          </Stack>
        </Drawer>
      </Container>
    </Paper>
  );
};

export default Header;
