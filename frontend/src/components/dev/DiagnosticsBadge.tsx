import React from 'react';
import { Badge, Group } from '@mantine/core';
import useCorrelationId from '../../hooks/useCorrelationId';

export default function DiagnosticsBadge(): React.ReactElement | null {
  const cid = useCorrelationId() as string | null;
  if (process.env.NODE_ENV === 'production') return null;
  
  return (
    <Group gap="xs">
      {cid && (
        <Badge size="xs" color="grape" variant="light" title="X-Correlation-ID">
          cid: {cid.slice(0, 8)}
        </Badge>
      )}
    </Group>
  );
}
