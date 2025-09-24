import React from 'react';
import { Footer as MantineFooter, Container, Group, Text, ActionIcon, Anchor } from '@mantine/core';

function Footer() {
  const year = new Date().getFullYear();
  
  return (
    <MantineFooter height={60} p="md">
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
    </MantineFooter>
  );
}

export default Footer;