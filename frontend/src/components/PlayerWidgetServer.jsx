import React from 'react';
import { Card, Skeleton, Text, Group, Badge } from '@mantine/core';
import { useWidgetEnvelope } from '../features/widgets/useWidgetEnvelope';
import { useSportContext } from '../context/SportContext';

// Server-side widget envelope consumer for player stats.
// TODO: Extend mapping once backend standardizes statistic keys per sport.
export default function PlayerWidgetServer({ playerId, season }) {
  const { activeSport } = useSportContext();
  const { data, isLoading, error, refetch, isFetching } = useWidgetEnvelope('player', playerId, { sport: activeSport, season });

  if (isLoading) {
    return (
      <Card withBorder p="md">
        <Group spacing="sm">
          <Skeleton height={28} width={160} />
          <Skeleton height={20} width={80} />
        </Group>
        <Skeleton mt="md" height={18} width="70%" />
        <Skeleton mt="sm" height={120} />
      </Card>
    );
  }

  if (error || (data && data.payload && data.payload.error)) {
    const message = error?.message || data?.payload?.error || 'Unavailable';
    return (
      <Card withBorder p="md" color="red">
        <Text fw={600} mb="xs">Widget unavailable</Text>
        <Text size="sm" color="dimmed">{message}</Text>
        <Text size="xs" mt="xs" color="dimmed">Retry later or check API key.</Text>
        <Badge mt="sm" onClick={() => refetch()} color="red" variant="filled" style={{ cursor: 'pointer' }}>
          Retry
        </Badge>
      </Card>
    );
  }

  const payload = data?.payload || {};
  const stats = payload.statistics || {};
  const team = payload.team || {};
  const loading = isFetching;

  const STAT_GROUPS = [
    { label: 'points', keys: ['pts', 'points', 'points_per_game'] },
    { label: 'assists', keys: ['ast', 'assists', 'assists_per_game'] },
    { label: 'rebounds', keys: ['reb', 'rebounds', 'rebounds_per_game'] },
    { label: 'steals', keys: ['stl', 'steals', 'steals_per_game'] },
    { label: 'blocks', keys: ['blk', 'blocks', 'blocks_per_game'] },
  ];

  return (
    <Card withBorder p="md">
      <Group position="apart" mb="xs">
        <Text fw={600}>{payload.name || 'Player'}</Text>
        {team?.abbreviation && <Badge>{team.abbreviation}</Badge>}
      </Group>
      <Text size="sm" color="dimmed">Season: {payload.season || season || 'current'}</Text>
      <Group mt="md" spacing="lg" wrap="wrap">
        {STAT_GROUPS.map(({ label, keys }) => {
          const val = keys.map(k => stats[k]).find(v => v !== undefined && v !== null);
          return (
            <Card key={label} shadow="xs" p="xs" style={{ minWidth: 90 }}>
              <Text size="xs" color="dimmed" style={{ textTransform: 'uppercase' }}>{label}</Text>
              <Text fw={600}>{loading ? '…' : (val ?? '—')}</Text>
            </Card>
          );
        })}
      </Group>
      {payload.position && <Text mt="sm" size="xs" color="dimmed">Position: {payload.position}</Text>}
    </Card>
  );
}