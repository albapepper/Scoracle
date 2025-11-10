import React from 'react';
import { Badge, Group } from '@mantine/core';
import useCorrelationId from '../../hooks/useCorrelationId';
import { http } from '../../app/http';

export default function DiagnosticsBadge(): JSX.Element | null {
  const cid = useCorrelationId() as any;
  if (process.env.NODE_ENV === 'production') return null;
  const rl = http.getRateLimitEvents();
  return (
    <Group gap="xs">
      {cid && (
        <Badge size="xs" color="grape" variant="light" title="X-Correlation-ID">
          cid: {String(cid).slice(0, 8)}
        </Badge>
      )}
      {rl > 0 && (
        <Badge size="xs" color="yellow" variant="light" title="Rate-limit retries (since load)">
          429×{rl}
        </Badge>
      )}
    </Group>
  );
}
