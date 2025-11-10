import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';

// Simple in-memory caches for ETag and response bodies
const etagCache: Map<string, string> = new Map(); // key: urlWithParams -> etag
const bodyCache: Map<string, any> = new Map(); // key: urlWithParams -> data
let lastCorrelationId: string | null = null;
let rateLimitEvents = 0;

// Expose minimal diagnostics in dev
if (typeof window !== 'undefined') {
  (window as any).__scoracleDiag = (window as any).__scoracleDiag || {};
  Object.defineProperties((window as any).__scoracleDiag, {
    lastCorrelationId: { get: () => lastCorrelationId },
    rateLimitEvents: { get: () => rateLimitEvents },
  });
}

const api: AxiosInstance = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
  // Accept 304 as a valid status for conditional requests
  validateStatus: (status) => (status >= 200 && status < 300) || status === 304 || status === 429,
});

// Utility to build a canonical request key
function buildKey(config: AxiosRequestConfig): string {
  const url = new URL(((config.baseURL as string) || '') + (config.url || ''), 'http://local');
  if (config.params) {
    Object.entries(config.params as Record<string, any>)
      .filter(([, v]) => v !== undefined && v !== null)
      .forEach(([k, v]) => url.searchParams.set(k, String(v)));
  }
  return url.pathname + (url.search ? url.search : '');
}

api.interceptors.request.use((config) => {
  const method = (config.method || 'get').toLowerCase();
  if (method === 'get') {
    const key = buildKey(config);
    const etag = etagCache.get(key);
    if (etag) {
      config.headers = { ...(config.headers || {}), 'If-None-Match': etag } as any;
    }
  }
  return config;
});

api.interceptors.response.use(
  (response: AxiosResponse) => {
    const cfg = (response as any).config as AxiosRequestConfig;
    const key = buildKey(cfg);

    // Correlation ID surfaced
    const headers = response.headers as any;
    const cid = headers?.['x-correlation-id'] || headers?.['x-cid'];
    if (cid) {
      lastCorrelationId = String(cid);
      if (process.env.NODE_ENV !== 'production') {
        // eslint-disable-next-line no-console
        console.debug('[HTTP] Correlation-ID:', cid, cfg.url);
      }
    }

    // Handle ETag caching
    const etag = headers?.etag;
    if (etag) {
      etagCache.set(key, String(etag));
    }

    // 304 Not Modified -> serve cached body if present
    if (response.status === 304) {
      if (bodyCache.has(key)) {
        return { ...response, data: bodyCache.get(key) } as AxiosResponse;
      }
      return { ...response, data: null } as AxiosResponse;
    }

    // Cache GET bodies for reuse on 304
    const method = (cfg.method || 'get').toLowerCase();
    if (method === 'get') {
      bodyCache.set(key, response.data);
    }

    return response;
  },
  async (error) => {
    const response = error?.response as AxiosResponse | undefined;
    const cfg: AxiosRequestConfig & { __retriedOnce?: boolean } = error?.config || {};

    // Correlation ID capture even on errors
    const cid = response?.headers?.['x-correlation-id'] || (response as any)?.headers?.['x-cid'];
    if (cid) {
      lastCorrelationId = String(cid);
      if (process.env.NODE_ENV !== 'production') {
        // eslint-disable-next-line no-console
        console.debug('[HTTP] Correlation-ID (error):', cid, cfg.url);
      }
    }

    // Emit error envelope event for UI if available
    try {
      const envelope = (response?.data as any)?.error ? (response?.data as any).error : null;
      const ev = new CustomEvent('scoracle:error', {
        detail: {
          error: envelope,
          status: response?.status,
          correlationId: lastCorrelationId,
          url: cfg?.url,
          method: cfg?.method,
        },
      });
      if (typeof window !== 'undefined') window.dispatchEvent(ev);
    } catch (_) {}

    // Rate limit handling with retry-after
    if (response && response.status === 429 && !cfg.__retriedOnce) {
      rateLimitEvents += 1;
      cfg.__retriedOnce = true;
      const ra = (response.headers as any)?.['retry-after'];
      const delayMs = ra ? Number(ra) * 1000 : 750 + Math.floor(Math.random() * 250);
      await new Promise((r) => setTimeout(r, delayMs));
      return api(cfg as any);
    }

    return Promise.reject(error);
  }
);

export const http = {
  get: async <T = any>(url: string, options: AxiosRequestConfig = {}): Promise<T> => {
    const res = await api.get(url, options);
    return res.data as T;
  },
  post: async <T = any>(url: string, data: any, options: AxiosRequestConfig = {}): Promise<T> => {
    const res = await api.post(url, data, options);
    return res.data as T;
  },
  raw: api,
  getLastCorrelationId: () => lastCorrelationId,
  getRateLimitEvents: () => rateLimitEvents,
};

export default http;