// Simple script loader to inject external scripts once and track load state
import { useEffect, useState } from 'react';

type ScriptStatus = 'idle' | 'loading' | 'ready' | 'error';

const loadedScripts: Map<string, { status: ScriptStatus; script: HTMLScriptElement }> = new Map();

export function useScript(src?: string | null): ScriptStatus {
  const [status, setStatus] = useState<ScriptStatus>(() => (src ? loadedScripts.get(src)?.status ?? 'idle' : 'idle'));

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
    const record = { status: 'loading' as ScriptStatus, script };
    loadedScripts.set(src, record);
    setStatus('loading');

    // Suppress noisy cross-origin "Script error." from this specific script to avoid dev overlay
    const swallow = (evt: ErrorEvent) => {
      try {
        const filename = (evt as ErrorEvent)?.filename || '';
        if (typeof filename === 'string' && filename.includes(src)) {
          evt.preventDefault?.();
          (evt as Event).stopImmediatePropagation?.();
          return false;
        }
      } catch (_) {
        /* ignore */
      }
      return undefined;
    };
    window.addEventListener('error', swallow as EventListener, true);

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
      window.removeEventListener('error', swallow as EventListener, true);
      // We keep the script in DOM for reuse; don't remove to avoid re-downloads
    };
  }, [src]);

  return status; // 'idle' | 'loading' | 'ready' | 'error'
}

export default useScript;
