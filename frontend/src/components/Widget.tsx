import React from 'react';
import { Card, Text, Group, Stack, Avatar, Badge } from '@mantine/core';
import { IconUser, IconUsers } from '@tabler/icons-react';
import type { WidgetData } from '../features/entities/api';

interface WidgetProps {
  /** Widget data from unified entity API */
  data?: WidgetData | null;
  /** Loading state */
  loading?: boolean;
  /** Error message */
  error?: string | null;
  /** Optional className */
  className?: string;
}

/**
 * Widget component - displays entity info card.
 * 
 * Renders widget data from the unified entity API.
 * No more HTML fetching - pure React rendering.
 */
export default function Widget({ data, loading, error, className }: WidgetProps) {
  if (loading) {
    return (
      <Card shadow="sm" padding="lg" radius="md" withBorder className={className}>
        <Stack align="center" gap="sm">
          <Text size="sm" c="dimmed">Loading...</Text>
        </Stack>
      </Card>
    );
  }

  if (error) {
    return (
      <Card shadow="sm" padding="lg" radius="md" withBorder className={className}>
        <Stack align="center" gap="sm">
          <Text size="sm" c="red">{error}</Text>
        </Stack>
      </Card>
    );
  }

  if (!data) {
    return null;
  }

  const isPlayer = data.type === 'player';
  const Icon = isPlayer ? IconUser : IconUsers;

  return (
    <Card shadow="sm" padding="lg" radius="md" withBorder className={className}>
      <Group wrap="nowrap" gap="lg">
        <Avatar size="lg" radius="xl" color={isPlayer ? 'blue' : 'green'}>
          <Icon size={24} />
        </Avatar>
        <Stack gap={4} style={{ flex: 1 }}>
          <Text fw={600} size="lg" lineClamp={1}>
            {data.display_name}
          </Text>
          <Group gap="xs">
            <Badge size="sm" variant="light" color={isPlayer ? 'blue' : 'green'}>
              {isPlayer ? 'Player' : 'Team'}
            </Badge>
            {data.subtitle && (
              <Text size="sm" c="dimmed">
                {data.subtitle}
              </Text>
            )}
          </Group>
        </Stack>
      </Group>
    </Card>
  );
}

/**
 * Legacy Widget component that fetches from URL.
 * 
 * @deprecated Use Widget with data prop instead.
 * Kept for backwards compatibility during migration.
 */
export function LegacyWidget({ url, className }: { url: string; className?: string }) {
  const containerRef = React.useRef<HTMLDivElement>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    if (!url) return;
    
    setLoading(true);
    setError(null);
    
    fetch(url)
      .then(res => {
        if (!res.ok) {
          throw new Error(`Failed to load widget: ${res.statusText}`);
        }
        return res.text();
      })
      .then(html => {
        if (containerRef.current) {
          containerRef.current.innerHTML = html;
        }
        setLoading(false);
      })
      .catch(err => {
        setError(err.message || 'Failed to load widget');
        setLoading(false);
      });
  }, [url]);

  if (loading) {
    return <Text size="sm" c="dimmed">Loading...</Text>;
  }

  if (error) {
    return <Text size="sm" c="red">{error}</Text>;
  }

  return <div ref={containerRef} className={className} />;
}
