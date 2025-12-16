/// <reference types="astro/client" />

/**
 * Environment variable type declarations for Astro
 * 
 * PUBLIC_ prefix makes variables available to client-side code
 */
interface ImportMetaEnv {
  /** Backend API base URL (e.g., http://localhost:8000/api/v1) */
  readonly PUBLIC_API_URL: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
