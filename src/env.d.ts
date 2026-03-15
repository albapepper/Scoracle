/// <reference types="astro/client" />

/**
 * Environment variable type declarations for Astro
 * 
 * PUBLIC_ prefix makes variables available to client-side code
 */
interface ImportMetaEnv {
  /** FastAPI backend base URL (e.g., http://localhost:8000/api/v1) */
  readonly PUBLIC_API_URL: string;
  /** PostgREST public URL (e.g., https://postgrest.scoracle.com) */
  readonly PUBLIC_POSTGREST_URL: string;
  /** Go API public URL including /api/v1 prefix (e.g., https://go-api.scoracle.com/api/v1) */
  readonly PUBLIC_GO_API_URL: string;
  /** FastAPI private Railway network URL (server-only) */
  readonly FASTAPI_INTERNAL_URL: string;
  /** PostgREST private Railway network URL (server-only) */
  readonly POSTGREST_INTERNAL_URL: string;
  /** Go API private Railway network URL (server-only) */
  readonly GO_INTERNAL_URL: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
