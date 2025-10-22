import React, { useEffect, useMemo, useRef } from 'react';
import useScript from '../hooks/useScript';

// Public CDN for API-Sports Widgets (3.x). Use a type-specific default as primary path.
const DEFAULT_BY_TYPE = {
  team: 'https://widgets.api-sports.io/3.1.0/team',
  player: 'https://widgets.api-sports.io/3.1.0/player',
};

/**
 * ApiSportsWidget
 * Props:
 * - type: 'team' | 'player' | other widgets types from API-Sports
 * - data: object of data-* attributes e.g. { teamId: '39', playerStatistics: 'true' }
 *         Keys will be converted from camelCase to kebab-case prefixed with data-.
 * - targetSelector: optional CSS selector for data-target-player or similar; include in data if specific.
 * - src: override widget script URL if needed.
 * - className, style: forwarded to host element.
 */
export default function ApiSportsWidget({ type, data = {}, src, className, style }) {
  const finalSrc = src || DEFAULT_BY_TYPE[type] || DEFAULT_BY_TYPE.player;
  const status = useScript(finalSrc);
  const ref = useRef(null);

  // Build attributes for the custom element
  const attrs = useMemo(() => {
    const out = new Map();
    out.set('data-type', type);
    const obj = { ...data };
    // Optionally inject API key from env for widget initialization (exposes key to client!)
    const envKey = process.env.REACT_APP_APISPORTS_WIDGET_KEY || process.env.REACT_APP_API_SPORTS_KEY || '';
    if (!obj.key && envKey) {
      out.set('data-key', envKey);
    }
    // Provide attribute synonyms expected by some API-Sports widgets
    if (obj.playerId) {
      out.set('data-player-id', String(obj.playerId));
      out.set('data-id', String(obj.playerId));
      out.set('data-id-player', String(obj.playerId));
    }
    if (obj.teamId) {
      out.set('data-team-id', String(obj.teamId));
      out.set('data-id', String(obj.teamId));
      out.set('data-id-team', String(obj.teamId));
    }
    // Copy remaining keys generically
    Object.entries(obj).forEach(([key, value]) => {
      if (value === undefined || value === null || value === '') return;
      if (key === 'playerId' || key === 'teamId') return; // already handled
      const kebab = key
        .replace(/([a-z])([A-Z])/g, '$1-$2')
        .replace(/_/g, '-')
        .toLowerCase();
      out.set(`data-${kebab}`, String(value));
    });
    return out;
  }, [type, data]);

  useEffect(() => {
    // When script is ready, attempt to re-render/upgrade the widget if needed.
    if (status !== 'ready') return;
    // Nudge some scripts by toggling a data attribute to trigger MutationObserver scans
    const el = ref.current;
    if (!el) return;
    const attr = 'data-refresh-tick';
    const v = String(Date.now());
    el.setAttribute(attr, v);
    const t = setTimeout(() => {
      // remove after a short delay
      try { el.removeAttribute(attr); } catch (_) {}
    }, 1000);
    return () => clearTimeout(t);
  }, [status]);

  return (
    <div
      ref={ref}
      className={`wg-api-football ${className || ''}`.trim()}
      style={style}
      id={`wg-api-football-${type}`}
      {...Object.fromEntries(attrs)}
    />
  );
}
