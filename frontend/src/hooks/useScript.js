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
  script.type = 'module';
  // Helps error reporting and can avoid some proxy quirks; harmless otherwise
  script.crossOrigin = 'anonymous';
  script.referrerPolicy = 'no-referrer-when-downgrade';
    const record = { status: 'loading', script };
    loadedScripts.set(src, record);
    setStatus('loading');

    // Suppress noisy cross-origin "Script error." from this specific script to avoid dev overlay
    const swallow = (evt) => {
      try {
        const filename = evt?.filename || '';
        if (typeof filename === 'string' && filename.includes(src)) {
          evt.preventDefault?.();
          evt.stopImmediatePropagation?.();
          return false;
        }
      } catch (_) { /* ignore */ }
      return undefined;
    };
    window.addEventListener('error', swallow, true);

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
      window.removeEventListener('error', swallow, true);
      // We keep the script in DOM for reuse; don't remove to avoid re-downloads
    };
  }, [src]);

  return status; // 'idle' | 'loading' | 'ready' | 'error'
}

export default useScript;
