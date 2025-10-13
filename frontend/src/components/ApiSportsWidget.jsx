import React, { useEffect, useMemo, useRef } from 'react';
import useScript from '../hooks/useScript';

// Public CDN for API-Sports Widgets (3.x). If a project-wide config is needed, we can also inject a global config script.
const DEFAULT_WIDGET_SRC = 'https://widgets.api-sports.io/3.1.0/widget.js';

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
export default function ApiSportsWidget({ type, data = {}, src = DEFAULT_WIDGET_SRC, className, style }) {
  const status = useScript(src);
  const ref = useRef(null);

  // Build attributes for the custom element
  const attrs = useMemo(() => {
    const out = new Map();
    out.set('data-type', type);
    Object.entries(data).forEach(([key, value]) => {
      if (value === undefined || value === null || value === '') return;
      // convert camelCase to kebab-case
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
    // Some widgets auto-initialize on DOMContentLoaded; to re-init after React mounts,
    // they often observe the DOM or expose a refresh; if needed we can dispatch an event.
    // Here we do nothing and rely on the widget's MutationObserver.
  }, [status]);

  return (
    <api-sports-widget
      ref={ref}
      className={className}
      style={style}
      {...Object.fromEntries(attrs)}
    />
  );
}
