const API_BASE = import.meta.env.PUBLIC_API_URL || '/api/v1';

export interface ApiError {
  message: string;
  status: number;
  code?: string;
}

export class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE) {
    this.baseUrl = baseUrl;
  }

  async fetch<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
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

    return response.json();
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
}

export const api = new ApiClient();
