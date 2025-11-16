import React from 'react';
import { Container, Group, Text, Anchor, Paper } from '@mantine/core';
import DiagnosticsBadge from './dev/DiagnosticsBadge';
import { useThemeMode, getThemeColors } from '../theme';
import { useTranslation } from 'react-i18next';

const Footer: React.FC = () => {
  const year = new Date().getFullYear();
  const { t } = useTranslation();
  const { colorScheme } = useThemeMode();
  const colors = getThemeColors(colorScheme);

  return (
    <Paper component="footer" radius={0} p="md" withBorder={false} style={{ backgroundColor: colors.background.primary, borderTop: `1px solid ${colors.ui.border}` }}>
      <Container>
        <Group justify="space-between" align="center">
          <Text size="sm" c="dimmed">
            © {year} Scoracle. {t('footer.allRightsReserved')}
          </Text>
          <Group>
            <Anchor href="#" target="_blank" c="dimmed" size="sm">
              {t('footer.terms')}
            </Anchor>
            <Anchor href="#" target="_blank" c="dimmed" size="sm">
              {t('footer.privacy')}
            </Anchor>
            <DiagnosticsBadge />
          </Group>
        </Group>
      </Container>
    </Paper>
  );
};

export default Footer;
