import * as React from 'react';
import { Card, Skeleton, Text, Group, Badge } from '@mantine/core';
import { useWidgetEnvelope } from '../features/widgets/useWidgetEnvelope';
import { useSportContext } from '../context/SportContext';

interface PlayerWidgetServerProps {
  playerId: string | number;
  season?: string;
}

interface TeamInfo { abbreviation?: string; }
interface WidgetPayload {
  name?: string;
  season?: string | number;
  position?: string;
  team?: TeamInfo | null;
  statistics?: Record<string, number | string | null | undefined>;
  error?: string;
}

export default function PlayerWidgetServer({ playerId, season }: PlayerWidgetServerProps) {
  const { activeSport } = useSportContext();
  const [retryToggle, setRetryToggle] = React.useState(false);
  const { data, isLoading, error } = useWidgetEnvelope<{ payload?: WidgetPayload }>(
    'player',
    playerId,
    { sport: activeSport, season, debug: retryToggle }
  );

  const retry = React.useCallback(() => setRetryToggle((v) => !v), []);

  if (isLoading) {
    return (
      <Card withBorder p="md">
        <Group gap="sm">
          <Skeleton height={28} width={160} />
          <Skeleton height={20} width={80} />
        </Group>
        <Skeleton mt="md" height={18} width="70%" />
        <Skeleton mt="sm" height={120} />
      </Card>
    );
  }

  const payload = (data as any)?.payload as WidgetPayload | undefined;
  if (error || payload?.error) {
    const message = (error as any)?.message || payload?.error || 'Unavailable';
    return (
      <Card withBorder p="md">
        <Text fw={600} mb="xs">Widget unavailable</Text>
        <Text size="sm" c="dimmed">{message}</Text>
        <Text size="xs" mt="xs" c="dimmed">Retry later or check API key.</Text>
        <Badge mt="sm" onClick={retry} color="red" variant="filled" style={{ cursor: 'pointer' }}>
          Retry
        </Badge>
      </Card>
    );
  }

  const stats = payload?.statistics || {};
  const team = payload?.team || {};

  const STAT_GROUPS: Array<{ label: string; keys: string[] }> = [
    { label: 'points', keys: ['pts', 'points', 'points_per_game'] },
    { label: 'assists', keys: ['ast', 'assists', 'assists_per_game'] },
    { label: 'rebounds', keys: ['reb', 'rebounds', 'rebounds_per_game'] },
    { label: 'steals', keys: ['stl', 'steals', 'steals_per_game'] },
    { label: 'blocks', keys: ['blk', 'blocks', 'blocks_per_game'] },
  ];

  return (
    <Card withBorder p="md">
      <Group justify="space-between" mb="xs">
        <Text fw={600}>{payload?.name || 'Player'}</Text>
        {(team as TeamInfo)?.abbreviation && <Badge>{(team as TeamInfo).abbreviation}</Badge>}
      </Group>
      <Text size="sm" c="dimmed">Season: {payload?.season || season || 'current'}</Text>
      <Group mt="md" gap="lg">
        {STAT_GROUPS.map(({ label, keys }) => {
          const val = keys.map((k) => (stats as any)[k]).find((v) => v !== undefined && v !== null);
          return (
            <Card key={label} shadow="xs" p="xs" style={{ minWidth: 90 }}>
              <Text size="xs" c="dimmed" style={{ textTransform: 'uppercase' }}>{label}</Text>
              <Text fw={600}>{val ?? '—'}</Text>
            </Card>
          );
        })}
      </Group>
      {payload?.position && <Text mt="sm" size="xs" c="dimmed">Position: {payload.position}</Text>}
    </Card>
  );
}
