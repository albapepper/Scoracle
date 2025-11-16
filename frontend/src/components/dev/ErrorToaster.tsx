import React, { useEffect, useState } from 'react';
import { Notification, Transition } from '@mantine/core';

interface ErrorItem {
  id: string;
  code: string;
  message: string;
  status?: number;
  correlationId?: string;
  url?: string;
  ts: number;
}

export default function ErrorToaster(): React.ReactElement | null {
  const [items, setItems] = useState<ErrorItem[]>([]);

  useEffect(() => {
    function handler(e: Event) {
      const custom = e as CustomEvent;
      const detail: any = custom.detail || {};
      const { error, status, correlationId, url } = detail;
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
        ...prev.filter((i) => Date.now() - i.ts < 10_000).slice(0, 3),
      ]);
    }
    window.addEventListener('scoracle:error', handler as EventListener);
    return () => window.removeEventListener('scoracle:error', handler as EventListener);
  }, []);

  if (!items.length) return null;
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
