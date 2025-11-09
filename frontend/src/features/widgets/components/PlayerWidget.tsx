import React from 'react';
// Using JS hook facade for now
// @ts-ignore
import { useWidgetEnvelope } from '../useWidgetEnvelope.js';

export function PlayerWidget({ playerId, sport, season }: { playerId: string; sport: string; season?: string }) {
  // @ts-ignore - using JS hook without types for now
  const { data, isLoading, error } = useWidgetEnvelope('player', playerId, { sport, season } as any);
  if (isLoading) return <div>Loading widget...</div>;
  if (error) return <div>Error loading widget</div>;
  if (!data) return null;
  const payload: any = data.payload || {};
  return (
    <div>
      <h3>{payload.name || 'Player'}</h3>
      {payload.statistics && Object.keys(payload.statistics).length > 0 && (
        <ul>
          {Object.entries(payload.statistics).slice(0,5).map(([k,v]) => (
            <li key={k}>{k}: {String(v)}</li>
          ))}
        </ul>
      )}
    </div>
  );
}
export default PlayerWidget;
