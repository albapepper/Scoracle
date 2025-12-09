import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';

/**
 * Simplified HTTP client for Scoracle.
 * 
 * - Vercel CDN handles caching at the edge
 * - Rate limiting is handled server-side
 * - ETag handling only where explicitly needed (syncService)
 */

let lastCorrelationId: string | null = null;

const api: AxiosInstance = axios.create({
  baseURL: '/api/v1/',
  headers: { 'Content-Type': 'application/json' },
});

// Response interceptor for correlation ID tracking (useful for debugging)
api.interceptors.response.use(
  (response: AxiosResponse) => {
    const headers = response.headers as Record<string, string>;
    const cid = headers?.['x-correlation-id'] || headers?.['x-cid'];
    if (cid) {
      lastCorrelationId = String(cid);
      if (process.env.NODE_ENV !== 'production') {
        console.debug('[HTTP] Correlation-ID:', cid, response.config?.url);
      }
    }
    return response;
  },
  (error) => {
    // Capture correlation ID even on errors
    const headers = error?.response?.headers as Record<string, string> | undefined;
    const cid = headers?.['x-correlation-id'] || headers?.['x-cid'];
    if (cid) {
      lastCorrelationId = String(cid);
    }

    // Emit error event for UI toaster (if listening)
    if (typeof window !== 'undefined' && error?.response) {
      try {
        const ev = new CustomEvent('scoracle:error', {
          detail: {
            error: error.response?.data?.error || null,
            status: error.response?.status,
            correlationId: lastCorrelationId,
            url: error.config?.url,
          },
        });
        window.dispatchEvent(ev);
      } catch (_) {
        // Ignore event dispatch errors
      }
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
  /**
   * Raw Axios instance for advanced use cases (e.g., custom headers, status handling)
   * Used by syncService for ETag-based conditional requests
   */
  raw: api,
  getLastCorrelationId: () => lastCorrelationId,
};

export default http;
