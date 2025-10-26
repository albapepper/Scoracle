import React from 'react';
import { Container, Group, Text, Anchor, Paper } from '@mantine/core';
import theme from '../theme';
import { useTranslation } from 'react-i18next';

function Footer() {
  const year = new Date().getFullYear();
  const { t } = useTranslation();
  
  return (
  <Paper component="footer" withBorder radius={0} p="md" style={{ backgroundColor: theme.colors.background.primary }}>
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
          </Group>
        </Group>
      </Container>
    </Paper>
  );
}

export default Footer;