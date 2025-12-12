const API_BASE = import.meta.env.PUBLIC_API_URL || '/api/v1';

export interface ApiError {
  message: string;
  status: number;
  code?: string;
}

interface CacheEntry<T> {
  data: T;
  timestamp: number;
}

/**
 * Simple in-memory cache for API responses
 * Helps reduce redundant API calls on the same session
 */
class ResponseCache {
  private cache = new Map<string, CacheEntry<any>>();
  private ttl = 5 * 60 * 1000; // 5 minutes default

  get<T>(key: string): T | null {
    const entry = this.cache.get(key);
    if (!entry) return null;

    const isExpired = Date.now() - entry.timestamp > this.ttl;
    if (isExpired) {
      this.cache.delete(key);
      return null;
    }

    return entry.data as T;
  }

  set<T>(key: string, data: T): void {
    this.cache.set(key, { data, timestamp: Date.now() });
  }

  clear(): void {
    this.cache.clear();
  }
}

export class ApiClient {
  private baseUrl: string;
  private cache = new ResponseCache();

  constructor(baseUrl: string = API_BASE) {
    this.baseUrl = baseUrl;
  }

  async fetch<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    // Check cache for GET requests
    if (options.method !== 'POST' && !options.method) {
      const cached = this.cache.get<T>(url);
      if (cached) {
        console.debug(`Cache hit for ${endpoint}`);
        return cached;
      }
    }
    
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      const error: ApiError = {
        message: `API error: ${response.status} ${response.statusText}`,
        status: response.status,
      };
      
      try {
        const data = await response.json();
        error.message = data.message || error.message;
        error.code = data.code;
      } catch {
        // Response wasn't JSON
      }
      
      throw error;
    }

    const data = await response.json() as T;
    
    // Cache GET responses
    if (!options.method || options.method === 'GET') {
      this.cache.set<T>(url, data);
    }

    return data;
  }

  get<T>(endpoint: string): Promise<T> {
    return this.fetch<T>(endpoint, { method: 'GET' });
  }

  post<T>(endpoint: string, data: unknown): Promise<T> {
    return this.fetch<T>(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  clearCache(): void {
    this.cache.clear();
  }
}

export const api = new ApiClient();
