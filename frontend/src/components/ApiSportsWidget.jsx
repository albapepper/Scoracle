import React, { useEffect, useMemo, useRef, useState } from 'react';

// We always render the generic 'api-sports-widget' tag to keep usage simple.
const TAG_NAME = 'api-sports-widget';

/**
 * ApiSportsWidget
 * Props:
 * - type: 'team' | 'player' | other widgets types from API-Sports
 * - data: object of data-* attributes e.g. { teamId: '39', playerStatistics: 'true' }
 *         Keys will be converted from camelCase to kebab-case prefixed with data-.
 * - className, style: forwarded to host element.
 * - debug: when true, logs lifecycle warnings in the console.
 */
export default function ApiSportsWidget({ type, data = {}, className, style, debug = false }) {
  const ref = useRef(null);
  const hasConnectedRef = useRef(false);
  // Force generic tag for simplicity and determinism
  const [tagName] = useState(TAG_NAME);

  const dataSignature = useMemo(() => {
    try {
      return JSON.stringify(data ?? {});
    } catch (err) {
      if (debug) {
        // eslint-disable-next-line no-console
        console.warn('[ApiSportsWidget] failed to serialise data prop', err);
      }
      return '{}';
    }
  }, [data, debug]);

  // Build attributes for the custom element
  const attrs = useMemo(() => {
    const out = {};
    out['data-type'] = type;
    const obj = { ...data };
    // For config type, pass through exactly what caller provided (data-key, data-sport, etc.)
    const isConfig = String(type).toLowerCase() === 'config';
    // No automatic key/host/sport on non-config widgets; rely on the config element as per API-Sports docs
    // Provide attribute synonyms expected by some API-Sports widgets
    if (!isConfig && obj.playerId) {
      const value = String(obj.playerId);
      out['data-player-id'] = value;
      out['data-id'] = value;
      out['data-id-player'] = value;
    }
    if (!isConfig && obj.teamId) {
      const value = String(obj.teamId);
      out['data-team-id'] = value;
      out['data-id'] = value;
      out['data-id-team'] = value;
    }
    // Copy remaining keys generically
    Object.entries(obj).forEach(([key, value]) => {
      if (value === undefined || value === null || value === '') return;
      if (key === 'playerId' || key === 'teamId') return; // already handled
      const kebab = key
        .replace(/([a-z])([A-Z])/g, '$1-$2')
        .replace(/_/g, '-')
        .toLowerCase();
      out[`data-${kebab}`] = String(value);
    });
    return out;
  }, [type, dataSignature]);

  // Apply the computed attributes directly to the DOM node whenever they change.
  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const currentAttrNames = new Set();
    Object.entries(attrs).forEach(([name, value]) => {
      currentAttrNames.add(name);
      if (el.getAttribute(name) !== value) {
        el.setAttribute(name, value);
      }
    });

    // Remove stale data-* attributes that are no longer present.
    Array.from(el.attributes)
      .filter((attr) => attr.name.startsWith('data-') && !currentAttrNames.has(attr.name))
      .forEach((attr) => el.removeAttribute(attr.name));
  }, [attrs]);

  useEffect(() => {
    const controller = new AbortController();

    const initialise = async () => {
      try {
        if (debug) {
          // eslint-disable-next-line no-console
          console.debug('[ApiSportsWidget] waiting for custom element definition');
        }
        if (typeof customElements?.whenDefined === 'function') {
          await customElements.whenDefined(tagName);
        }
      } catch (err) {
        if (debug) {
          // eslint-disable-next-line no-console
          console.warn('[ApiSportsWidget] custom element definition wait failed', err);
        }
      }

      if (controller.signal.aborted) return;

      const el = ref.current;
      if (!el) return;

      if (!hasConnectedRef.current) {
        // If the custom element exposes its own lifecycle hooks, invoke them once to ensure hydration
        try {
          if (typeof el.connectedCallback === 'function') {
            el.connectedCallback();
          }
        } catch (err) {
          if (debug) {
            // eslint-disable-next-line no-console
            console.warn('[ApiSportsWidget] connectedCallback invocation failed', err);
          }
        }
        hasConnectedRef.current = true;
      }
    };

    initialise();

    return () => controller.abort();
  }, [debug, tagName]);

  useEffect(() => {
    const el = ref.current;
    if (!el || !hasConnectedRef.current) return;

    try {
      const evt = new Event('DOMContentLoaded', { bubbles: true, cancelable: true });
      document.dispatchEvent(evt);
    } catch (err) {
      if (debug) {
        // eslint-disable-next-line no-console
        console.warn('[ApiSportsWidget] DOMContentLoaded dispatch failed', err);
      }
    }

    const attr = 'data-refresh-tick';
    const marker = String(Date.now());
    el.setAttribute(attr, marker);
    const timeout = window.setTimeout(() => {
      try {
        if (el.getAttribute(attr) === marker) {
          el.removeAttribute(attr);
        }
      } catch (_) {}
    }, 750);

    return () => window.clearTimeout(timeout);
  }, [attrs, debug]);

  // Render the custom element tag used by API-Sports widgets (v3).
  // Prefer sport-specific tag if available; fall back to generic.
  return React.createElement(tagName, {
    ref,
    className,
    style,
    ...attrs,
  });
}
