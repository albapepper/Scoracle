import React, { useEffect, useMemo, useRef } from 'react';
import useScript from '../hooks/useScript';
import { APISPORTS_KEY } from '../config';

// Public CDN for API-Sports Widgets (3.x). Use a sport-level script which supports multiple widget types.
const DEFAULT_BY_SPORT = {
  FOOTBALL: 'https://widgets.api-sports.io/3.1.0/football',
  EPL: 'https://widgets.api-sports.io/3.1.0/football',
  NBA: 'https://widgets.api-sports.io/3.1.0/basketball',
  NFL: 'https://widgets.api-sports.io/3.1.0/american-football',
};

const HOST_BY_SPORT = {
  FOOTBALL: 'v3.football.api-sports.io',
  EPL: 'v3.football.api-sports.io',
  NBA: 'v2.nba.api-sports.io',
  NFL: 'v1.american-football.api-sports.io',
};

const SPORT_ATTR = {
  FOOTBALL: 'football',
  EPL: 'football',
  NBA: 'nba',
  NFL: 'nfl',
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
export default function ApiSportsWidget({ type, sport = 'FOOTBALL', data = {}, src, className, style, debug = false }) {
  const sportKey = String(sport || 'FOOTBALL').toUpperCase();
  const finalSrc = src || DEFAULT_BY_SPORT[sportKey] || DEFAULT_BY_SPORT.FOOTBALL;
  const status = useScript(finalSrc);
  const ref = useRef(null);
  const triedFallbackRef = useRef(false);

  // Build attributes for the custom element
  const attrs = useMemo(() => {
    const out = new Map();
    out.set('data-type', type);
    const obj = { ...data };
    // Optionally inject API key from centralized config/env (exposes key to client!)
    let envKey = APISPORTS_KEY || '';
    // Debug-friendly fallbacks: allow localStorage or URL query to provide a key without restart
    if (!envKey && typeof window !== 'undefined') {
      try {
        const fromLs = window.localStorage.getItem('APISPORTS_WIDGET_KEY');
        if (fromLs) envKey = fromLs;
      } catch (_) {}
      if (!envKey) {
        try {
          const usp = new URLSearchParams(window.location.search);
          const fromQs = usp.get('apisportsKey');
          if (fromQs) envKey = fromQs;
        } catch (_) {}
      }
    }
    // For config type, don't add defaults/host; pass through exactly what caller provided
    const isConfig = String(type).toLowerCase() === 'config';
    if (!isConfig) {
      if (!obj.key && envKey) {
        out.set('data-key', envKey);
      }
      // Required host hint for some widget builds
      const host = HOST_BY_SPORT[sportKey];
      if (host) {
        out.set('data-host', host);
      }
      // Ensure sport attribute reflects current context unless explicitly provided
      const sportAttr = SPORT_ATTR[sportKey] || 'football';
      if (!obj.sport && sportAttr) {
        out.set('data-sport', sportAttr);
      }
      // Let global config control theme/timezone unless explicitly provided
    } else {
      // Ensure config can receive explicit env key if not provided
      if (!obj.key && envKey) {
        out.set('data-key', envKey);
      }
    }
    // Provide attribute synonyms expected by some API-Sports widgets
    if (!isConfig && obj.playerId) {
      out.set('data-player-id', String(obj.playerId));
      out.set('data-id', String(obj.playerId));
      out.set('data-id-player', String(obj.playerId));
    }
    if (!isConfig && obj.teamId) {
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
  }, [type, data, sportKey]);

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

  // Fallback: if loading the primary script failed, try an older stable path once
  useEffect(() => {
    if (status !== 'error' || triedFallbackRef.current) return;
    triedFallbackRef.current = true;
    const altBySport = {
      FOOTBALL: 'https://widgets.api-sports.io/3.0.4/football',
      EPL: 'https://widgets.api-sports.io/3.0.4/football',
      NBA: 'https://widgets.api-sports.io/3.0.4/basketball',
      NFL: 'https://widgets.api-sports.io/3.0.4/american-football',
    };
    const alt = altBySport[sportKey];
    if (!alt) return;
    const script = document.createElement('script');
    script.src = alt;
    script.async = true;
    script.onload = () => {
      const el = ref.current;
      if (!el) return;
      try {
        el.setAttribute('data-refresh-tick', String(Date.now()));
        setTimeout(() => el.removeAttribute('data-refresh-tick'), 800);
      } catch (_) {}
    };
    document.body.appendChild(script);
  }, [status, sportKey]);

  // Render the official custom element tag used by API-Sports widgets (v3)
  return React.createElement(
    'api-sports-widget',
    {
      ref,
      className,
      style,
      ...Object.fromEntries(attrs),
    }
  );
}
