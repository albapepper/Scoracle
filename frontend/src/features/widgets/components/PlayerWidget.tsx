import React from 'react';
// Using JS hook facade for now
// @ts-ignore
import { useWidgetEnvelope } from '../useWidgetEnvelope';

interface PlayerWidgetProps { playerId: string; sport: string; season?: string }
export function PlayerWidget({ playerId, sport, season }: PlayerWidgetProps) {
  const { data, isLoading, error } = useWidgetEnvelope('player', playerId, { sport: sport, season: season, enabled: true } as any);
  if (isLoading) return <div>Loading widget...</div>;
  if (error) return <div>Error loading widget</div>;
  if (!data) return null;
  const payload: any = (data as any)?.payload || {};
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
