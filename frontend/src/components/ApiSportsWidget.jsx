import React, { useMemo, useRef, useEffect } from 'react';

const TAG_NAME = 'api-sports-widget';

function ApiSportsWidget({ type, data = {}, className, style }) {
  const ref = useRef(null);
  const hasConnectedRef = useRef(false);

  const dataSignature = useMemo(() => JSON.stringify(data ?? {}), [data]);

  const attrs = useMemo(() => {
    const out = {};
    out['data-type'] = type;
    const obj = { ...data };
    const isConfig = String(type).toLowerCase() === 'config';

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

    Object.entries(obj).forEach(([key, value]) => {
      if (value === undefined || value === null || value === '' || key === 'playerId' || key === 'teamId') return;
      const kebab = key.replace(/([a-z])([A-Z])/g, '$1-$2').replace(/_/g, '-').toLowerCase();
      out[`data-${kebab}`] = String(value);
    });
    return out;
  }, [type, dataSignature]);

  useEffect(() => {
    const initializeWidget = async () => {
      const el = ref.current;
      if (!el) return;

      try {
        // Wait for the browser to process the script and define the custom element.
        await customElements.whenDefined(TAG_NAME);
        
        // The widget's script is supposed to auto-initialize, but in a SPA,
        // we need to manually trigger its setup logic when the component mounts.
        // We use a ref to ensure this only happens once per component instance.
        if (!hasConnectedRef.current && typeof el.connectedCallback === 'function') {
          el.connectedCallback();
          hasConnectedRef.current = true;
        }
      } catch (error) {
        console.error('Failed to initialize API-Sports widget:', error);
      }
    };
    
    initializeWidget();
  }, []); // Empty array is correct here, as the `key` prop will force a full remount.

  return React.createElement(TAG_NAME, {
    ref,
    className,
    style,
    ...attrs,
  });
}

export default React.memo(ApiSportsWidget);
