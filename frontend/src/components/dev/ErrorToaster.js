import React, { useEffect, useState } from 'react';
import { Notification, Transition } from '@mantine/core';

export default function ErrorToaster() {
  const [items, setItems] = useState([]);

  useEffect(() => {
    function handler(e) {
      const detail = e.detail || {};
      const { error, status, correlationId, url } = detail;
      // Ignore non-error envelopes
      if (!error || !error.code) return;
      setItems((prev) => [
        {
          id: Math.random().toString(36).slice(2),
          code: error.code,
          message: error.message || `Request failed (${status})`,
          status,
          correlationId,
          url,
          ts: Date.now(),
        },
        ...prev.filter((i) => Date.now() - i.ts < 10_000).slice(0, 3), // keep recent few
      ]);
    }
    window.addEventListener('scoracle:error', handler);
    return () => window.removeEventListener('scoracle:error', handler);
  }, []);

  return (
    <div style={{ position: 'fixed', bottom: 16, right: 16, zIndex: 5000, width: 340 }}>
      <Transition mounted={items.length > 0} transition="pop" duration={200} timingFunction="ease">
        {(styles) => (
          <div style={styles}>
            {items.map((item) => (
              <Notification
                key={item.id}
                withBorder
                onClose={() => setItems((prev) => prev.filter((i) => i.id !== item.id))}
                title={`Error: ${item.code}`}
                color="red"
                styles={{ root: { marginBottom: 8 } }}
              >
                <div style={{ fontSize: 12 }}>
                  <div>{item.message}</div>
                  {item.correlationId && (
                    <div style={{ opacity: 0.7 }}>cid: {item.correlationId.slice(0, 12)}</div>
                  )}
                  {item.url && <div style={{ opacity: 0.7 }}>path: {item.url}</div>}
                </div>
              </Notification>
            ))}
          </div>
        )}
      </Transition>
    </div>
  );
}
