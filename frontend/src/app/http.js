import axios from 'axios';

// Simple in-memory caches for ETag and response bodies
const etagCache = new Map(); // key: urlWithParams -> etag
const bodyCache = new Map(); // key: urlWithParams -> data
let lastCorrelationId = null;
let rateLimitEvents = 0;

// Expose minimal diagnostics in dev
if (typeof window !== 'undefined') {
  window.__scoracleDiag = window.__scoracleDiag || {};
  Object.defineProperties(window.__scoracleDiag, {
    lastCorrelationId: {
      get: () => lastCorrelationId,
    },
    rateLimitEvents: {
      get: () => rateLimitEvents,
    },
  });
}

const api = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
  // Accept 304 as a valid status for conditional requests
  validateStatus: (status) => (status >= 200 && status < 300) || status === 304 || status === 429,
});

// Utility to build a canonical request key
function buildKey(config) {
  const url = new URL((config.baseURL || '') + config.url, 'http://local');
  // append params
  if (config.params) {
    Object.entries(config.params)
      .filter(([, v]) => v !== undefined && v !== null)
      .forEach(([k, v]) => url.searchParams.set(k, String(v)));
  }
  return url.pathname + (url.search ? url.search : '');
}

api.interceptors.request.use((config) => {
  // Only apply to GETs
  if ((config.method || 'get').toLowerCase() === 'get') {
    const key = buildKey(config);
    const etag = etagCache.get(key);
    if (etag) {
      config.headers = { ...(config.headers || {}), 'If-None-Match': etag };
    }
  }
  return config;
});

api.interceptors.response.use(
  (response) => {
    const cfg = response.config || {};
    const key = buildKey(cfg);

    // Correlation ID surfaced
    const cid = response.headers?.['x-correlation-id'] || response.headers?.['x-cid'];
    if (cid) {
      lastCorrelationId = cid;
      if (process.env.NODE_ENV !== 'production') {
        // eslint-disable-next-line no-console
        console.debug('[HTTP] Correlation-ID:', cid, cfg.url);
      }
    }

    // Handle ETag caching
    const etag = response.headers?.etag;
    if (etag) {
      etagCache.set(key, etag);
    }

    // 304 Not Modified -> serve cached body if present
    if (response.status === 304) {
      if (bodyCache.has(key)) {
        return { ...response, data: bodyCache.get(key) };
      }
      // If no cached body, fall back to empty data
      return { ...response, data: null };
    }

    // Cache GET bodies for reuse on 304
    if ((cfg.method || 'get').toLowerCase() === 'get') {
      bodyCache.set(key, response.data);
    }

    return response;
  },
  async (error) => {
    const response = error.response;
    const cfg = error.config || {};

    // Correlation ID capture even on errors
    const cid = response?.headers?.['x-correlation-id'] || response?.headers?.['x-cid'];
    if (cid) {
      lastCorrelationId = cid;
      if (process.env.NODE_ENV !== 'production') {
        // eslint-disable-next-line no-console
        console.debug('[HTTP] Correlation-ID (error):', cid, cfg.url);
      }
    }

    // Emit error envelope event for UI if available
    try {
      const envelope = response?.data?.error ? response.data.error : null;
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
      const ra = response.headers?.['retry-after'];
      const delayMs = ra ? Number(ra) * 1000 : 750 + Math.floor(Math.random() * 250);
      await new Promise((r) => setTimeout(r, delayMs));
      return api(cfg);
    }

    return Promise.reject(error);
  }
);

export const http = {
  get: async (url, options = {}) => {
    const res = await api.get(url, options);
    return res.data;
  },
  post: async (url, data, options = {}) => {
    const res = await api.post(url, data, options);
    return res.data;
  },
  raw: api,
  getLastCorrelationId: () => lastCorrelationId,
  getRateLimitEvents: () => rateLimitEvents,
};

export default http;
