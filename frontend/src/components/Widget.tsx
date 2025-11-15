import React, { useEffect, useRef } from 'react';
import { Loader, Text } from '@mantine/core';

interface WidgetProps {
  url: string;
  className?: string;
}

export default function Widget({ url, className }: WidgetProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  useEffect(() => {
    if (!url) return;
    
    setLoading(true);
    setError(null);
    
    fetch(url)
      .then(res => {
        if (!res.ok) {
          throw new Error(`Failed to load widget: ${res.statusText}`);
        }
        return res.text();
      })
      .then(html => {
        if (containerRef.current) {
          containerRef.current.innerHTML = html;
        }
        setLoading(false);
      })
      .catch(err => {
        setError(err.message || 'Failed to load widget');
        setLoading(false);
      });
  }, [url]);

  if (loading) {
    return <Loader size="sm" />;
  }

  if (error) {
    return <Text size="sm" c="red">{error}</Text>;
  }

  return <div ref={containerRef} className={className} />;
}

