import React from 'react';
import { Card, Text, Group, Stack, Avatar, Badge, Image, Skeleton } from '@mantine/core';
import { IconUser, IconUsers, IconShirtSport } from '@tabler/icons-react';
import type { WidgetData } from '../features/entities/api';

interface WidgetProps {
  /** Widget data from unified entity API */
  data?: WidgetData | null;
  /** Loading state */
  loading?: boolean;
  /** Error message */
  error?: string | null;
  /** Show enhanced details (position, age, etc.) */
  showDetails?: boolean;
  /** Optional className */
  className?: string;
}

/**
 * Widget component - displays entity info card.
 * 
 * Renders widget data from the unified entity API.
 * Supports both basic and enhanced data (photos, positions, etc.)
 */
export default function Widget({ 
  data, 
  loading, 
  error, 
  showDetails = true,
  className 
}: WidgetProps) {
  if (loading) {
    return (
      <Card shadow="sm" padding="lg" radius="md" withBorder className={className}>
        <Group wrap="nowrap" gap="lg">
          <Skeleton height={60} circle />
          <Stack gap={4} style={{ flex: 1 }}>
            <Skeleton height={20} width="70%" />
            <Skeleton height={14} width="50%" />
          </Stack>
        </Group>
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
  const hasPhoto = data.photo_url || data.logo_url;
  const photoUrl = isPlayer ? data.photo_url : data.logo_url;

  // Build detail badges
  const details: string[] = [];
  if (showDetails) {
    if (data.position) details.push(data.position);
    if (data.age) details.push(`Age ${data.age}`);
    if (data.height) details.push(data.height);
    if (data.conference) details.push(data.conference);
    if (data.division) details.push(data.division);
  }

  return (
    <Card shadow="sm" padding="lg" radius="md" withBorder className={className}>
      <Group wrap="nowrap" gap="lg">
        {/* Photo/Logo or fallback icon */}
        {hasPhoto ? (
          <Image
            src={photoUrl}
            alt={data.display_name}
            w={60}
            h={60}
            radius="xl"
            fit="cover"
            fallbackSrc={undefined}
            onError={(e) => {
              // Hide broken images
              (e.target as HTMLImageElement).style.display = 'none';
            }}
          />
        ) : (
          <Avatar size="lg" radius="xl" color={isPlayer ? 'blue' : 'green'}>
            {isPlayer ? <IconUser size={24} /> : <IconUsers size={24} />}
          </Avatar>
        )}
        
        <Stack gap={4} style={{ flex: 1 }}>
          {/* Name */}
          <Text fw={600} size="lg" lineClamp={1}>
            {data.display_name}
          </Text>
          
          {/* Type badge + subtitle */}
          <Group gap="xs" wrap="wrap">
            <Badge size="sm" variant="light" color={isPlayer ? 'blue' : 'green'}>
              {isPlayer ? 'Player' : 'Team'}
            </Badge>
            {data.subtitle && (
              <Text size="sm" c="dimmed">
                {data.subtitle}
              </Text>
            )}
          </Group>
          
          {/* Enhanced details */}
          {details.length > 0 && (
            <Group gap={6} wrap="wrap" mt={4}>
              {details.map((detail, i) => (
                <Badge 
                  key={i} 
                  size="xs" 
                  variant="outline" 
                  color="gray"
                  leftSection={i === 0 && data.position ? <IconShirtSport size={10} /> : undefined}
                >
                  {detail}
                </Badge>
              ))}
            </Group>
          )}
        </Stack>
      </Group>
    </Card>
  );
}

/**
 * Compact Widget variant - smaller, for lists
 */
export function WidgetCompact({ data, loading }: Pick<WidgetProps, 'data' | 'loading'>) {
  if (loading) {
    return (
      <Group gap="sm">
        <Skeleton height={32} circle />
        <Skeleton height={16} width={100} />
      </Group>
    );
  }

  if (!data) return null;

  const isPlayer = data.type === 'player';
  const photoUrl = isPlayer ? data.photo_url : data.logo_url;

  return (
    <Group gap="sm" wrap="nowrap">
      {photoUrl ? (
        <Image
          src={photoUrl}
          alt={data.display_name}
          w={32}
          h={32}
          radius="xl"
          fit="cover"
        />
      ) : (
        <Avatar size="sm" radius="xl" color={isPlayer ? 'blue' : 'green'}>
          {isPlayer ? <IconUser size={14} /> : <IconUsers size={14} />}
        </Avatar>
      )}
      <Text size="sm" fw={500} lineClamp={1}>
        {data.display_name}
      </Text>
    </Group>
  );
}
