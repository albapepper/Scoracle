// Simple script loader to inject external scripts once and track load state
import { useEffect, useState } from 'react';

const loadedScripts = new Map();

export function useScript(src) {
  const [status, setStatus] = useState(() => (loadedScripts.get(src)?.status ?? 'idle'));

  useEffect(() => {
    if (!src) return;

    const existing = loadedScripts.get(src);
    if (existing) {
      setStatus(existing.status);
      return;
    }

    const script = document.createElement('script');
    script.src = src;
    script.async = true;
    const record = { status: 'loading', script };
    loadedScripts.set(src, record);
    setStatus('loading');

    const onLoad = () => {
      record.status = 'ready';
      setStatus('ready');
    };
    const onError = () => {
      record.status = 'error';
      setStatus('error');
    };

    script.addEventListener('load', onLoad);
    script.addEventListener('error', onError);
    document.body.appendChild(script);

    return () => {
      script.removeEventListener('load', onLoad);
      script.removeEventListener('error', onError);
      // We keep the script in DOM for reuse; don't remove to avoid re-downloads
    };
  }, [src]);

  return status; // 'idle' | 'loading' | 'ready' | 'error'
}

export default useScript;
