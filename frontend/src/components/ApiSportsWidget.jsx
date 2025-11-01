import React, { useEffect, useMemo, useRef, useState } from 'react';
import useScript from '../hooks/useScript';
// no direct import needed for key here; config element supplies it

// Public CDN candidates by type and sport. Keep it simple and browser-friendly.
const CDN_BY_TYPE_31 = {
  player: 'https://widgets.api-sports.io/3.1.0/player.js',
  team: 'https://widgets.api-sports.io/3.1.0/team.js',
};
const CDN_BY_TYPE_30 = {
  player: 'https://widgets.api-sports.io/3.0.4/player.js',
  team: 'https://widgets.api-sports.io/3.0.4/team.js',
};
const CDN_BY_SPORT_31 = {
  FOOTBALL: 'https://widgets.api-sports.io/3.1.0/football.js',
  EPL: 'https://widgets.api-sports.io/3.1.0/football.js',
  NBA: 'https://widgets.api-sports.io/3.1.0/basketball.js',
  NFL: 'https://widgets.api-sports.io/3.1.0/american-football.js',
};
const CDN_BY_SPORT_30 = {
  FOOTBALL: 'https://widgets.api-sports.io/3.0.4/football.js',
  EPL: 'https://widgets.api-sports.io/3.0.4/football.js',
  NBA: 'https://widgets.api-sports.io/3.0.4/basketball.js',
  NFL: 'https://widgets.api-sports.io/3.0.4/american-football.js',
};

// sport is still accepted to help pages pick the right config values, but
// the widget element itself relies on the separate config element.

// We always render the generic 'api-sports-widget' tag to keep usage simple.

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
  const widgetType = String(type || '').toLowerCase();
  // Single simple strategy: try type 3.1.0 JS, then sport 3.1.0 JS, then 3.0.4 equivalents.
  const cdnSport31 = CDN_BY_SPORT_31[sportKey] || CDN_BY_SPORT_31.FOOTBALL;
  const cdnType31 = CDN_BY_TYPE_31[widgetType] || CDN_BY_TYPE_31.player;
  const cdnSport30 = CDN_BY_SPORT_30[sportKey] || CDN_BY_SPORT_30.FOOTBALL;
  const cdnType30 = CDN_BY_TYPE_30[widgetType] || CDN_BY_TYPE_30.player;

  // Allow runtime override via URL ?widgetSrc=...
  let overrideSrc;
  try {
    const usp = new URLSearchParams(window.location.search);
    overrideSrc = usp.get('widgetSrc') || undefined;
  } catch (_) {}

  const candidates = useMemo(() => {
    const sportNoExt31 = (cdnSport31 || '').replace(/\.js$/, '');
    const typeNoExt31 = (cdnType31 || '').replace(/\.js$/, '');
    const sportNoExt30 = (cdnSport30 || '').replace(/\.js$/, '');
    const typeNoExt30 = (cdnType30 || '').replace(/\.js$/, '');
    const widgetV3 = 'https://widgets.api-sports.io/v3/widget.js';
    const widget3 = 'https://widgets.api-sports.io/3/widget.js';
    const widgetRoot = 'https://widgets.api-sports.io/widget.js';
    const widget31 = 'https://widgets.api-sports.io/3.1.0/widget.js';
    const widget31No = 'https://widgets.api-sports.io/3.1.0/widget';
    const widget30 = 'https://widgets.api-sports.io/3.0.4/widget.js';
    const widget30No = 'https://widgets.api-sports.io/3.0.4/widget';

    const arr = [
      overrideSrc,
      // Preferred: unified widget loaders first (stable across versions)
      widgetV3,
      widget3,
      widgetRoot,
      widget31,
      widget31No,
      // Then type/sport-specific files for older setups
      cdnType31,
      cdnSport31,
      // Without .js variants (in case CDN serves those)
      typeNoExt31,
      sportNoExt31,
      // Legacy
      cdnType30,
      cdnSport30,
      typeNoExt30,
      sportNoExt30,
      widget30,
      widget30No,
    ];
    // Deduplicate and remove falsy
    return Array.from(new Set(arr.filter(Boolean)));
  }, [cdnSport31, cdnType31, cdnSport30, cdnType30, overrideSrc]);

  const initialSrc = src || (candidates[0] || 'https://widgets.api-sports.io/v3/widget.js');
  const finalSrc = initialSrc;
  const status = useScript(finalSrc);
  const ref = useRef(null);
  const triedFallbackRef = useRef(false);
  // Force generic tag for simplicity and determinism
  const [tagName] = useState('api-sports-widget');

  // No tag switching logic; we always use the generic element

  // Build attributes for the custom element
  const attrs = useMemo(() => {
    const out = new Map();
    out.set('data-type', type);
    const obj = { ...data };
    // For config type, pass through exactly what caller provided (data-key, data-sport, etc.)
    const isConfig = String(type).toLowerCase() === 'config';
    // No automatic key/host/sport on non-config widgets; rely on the config element as per API-Sports docs
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
  }, [type, data]);

  useEffect(() => {
    // When script is ready, nudge by toggling a data attribute to trigger MutationObserver scans
    if (status !== 'ready') return;
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
  }, [status, sportKey, finalSrc]);

  // Fallbacks: if loading the primary script failed, walk remaining candidates sequentially once
  useEffect(() => {
    if (status !== 'error' || triedFallbackRef.current) return;
    triedFallbackRef.current = true;
    const tried = new Set([finalSrc]);
    const rest = candidates.filter((c) => !tried.has(c));

    const injectAt = (idx) => {
      if (idx >= rest.length) return;
      const url = rest[idx];
      const script = document.createElement('script');
      script.src = url;
      script.async = true;
      script.onload = () => {
        const el = ref.current;
        if (!el) return;
        try {
          el.setAttribute('data-refresh-tick', String(Date.now()));
          setTimeout(() => el.removeAttribute('data-refresh-tick'), 800);
        } catch (_) {}
      };
      script.onerror = () => injectAt(idx + 1);
      document.body.appendChild(script);
    };

    injectAt(0);
  }, [status, sportKey, widgetType, finalSrc, candidates]);

  // Render the custom element tag used by API-Sports widgets (v3).
  // Prefer sport-specific tag if available; fall back to generic.
  return React.createElement(
    tagName,
    {
      ref,
      className,
      style,
      ...Object.fromEntries(attrs),
    }
  );
}
