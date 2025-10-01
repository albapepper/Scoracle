import React from 'react';
import { Container, Group, Text, Anchor, Paper } from '@mantine/core';
import theme from '../theme';

function Footer() {
  const year = new Date().getFullYear();
  
  return (
  <Paper component="footer" withBorder radius={0} p="md" style={{ backgroundColor: theme.colors.background.primary }}>
      <Container>
        <Group justify="space-between" align="center">
          <Text size="sm" c="dimmed">
            © {year} Scoracle. All rights reserved.
          </Text>

          <Group>
            <Anchor href="#" target="_blank" c="dimmed" size="sm">
              Terms of Service
            </Anchor>
            <Anchor href="#" target="_blank" c="dimmed" size="sm">
              Privacy Policy
            </Anchor>
          </Group>
        </Group>
      </Container>
    </Paper>
  );
}

export default Footer;