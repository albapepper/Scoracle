import { useEffect, useState } from 'react';
import { http } from '../app/http';

export default function useCorrelationId() {
  const [cid, setCid] = useState(http.getLastCorrelationId());

  useEffect(() => {
    const id = setInterval(() => {
      const latest = http.getLastCorrelationId();
      if (latest !== cid) {
        setCid(latest);
      }
    }, 1500);
    return () => clearInterval(id);
  }, [cid]);

  return cid;
}
