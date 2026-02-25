# Finalizing the Vercel-to-Railway Migration

## Context

The Vercel-to-Railway migration is approximately 80% complete. The core infrastructure is in place:

- Astro SSR with `@astrojs/node` adapter (standalone mode)
- Multi-backend data abstraction layer (`src/lib/utils/data-sources.ts`)
- Server-side fetch utilities (`src/lib/server/fetch.ts`)
- SSR page conversion for `/stats` and `/news`
- Dockerfile + railway.toml for container deployment
- Repository flattened to standard Astro project layout
- All Vercel configs removed, all Vercel URL references cleaned up

What remains is deployment validation, production hardening, and wiring up the future backends.

---

## Remaining Tasks

### 1. Validate Railway Deployment End-to-End

**Priority:** High -- blocking production launch
**Effort:** ~1 hour

Deploy the Docker container to Railway and verify everything works:

1. Push to Railway (should auto-build from `Dockerfile` + `railway.toml`)
2. Set environment variables in Railway dashboard:
   ```
   PUBLIC_API_URL=https://scoracle-data-production.up.railway.app/api/v1
   FASTAPI_INTERNAL_URL=http://scoracle-data.railway.internal:8000/api/v1
   SITE_URL=https://<assigned-railway-domain>
   NODE_ENV=production
   ```
3. Verify the health check passes (`GET /` returns 200)
4. Test each page type:
   - `/` -- static, should load instantly with sport selector
   - `/stats?sport=NBA&type=player&id=<some-id>` -- SSR, should render with real data (no loading skeleton)
   - `/news?sport=NBA&type=player&id=<some-id>` -- SSR, should render with real data
   - `/co-mentions` -- static, should load with autocomplete working
   - `/404` -- static
5. Verify private network SSR calls work: the Astro server should fetch from `FASTAPI_INTERNAL_URL` (Railway internal), not the public URL. Check Railway logs to confirm requests are going over the private network.
6. Verify client-side fetches work: tab switches, comparison mode, and autocomplete should all hit `PUBLIC_API_URL` from the browser.
7. Test on mobile to confirm responsive layout and safe-area padding.

### 2. Create and Add OG Image

**Priority:** Medium -- affects social media previews
**Effort:** ~30 minutes

The `Layout.astro` OG image meta tag now dynamically builds the URL from `SITE_URL` but there is no actual `public/og-image.png` file. Without it, social media previews (Twitter, Facebook, Discord, Slack) will have no image.

1. Design or generate an OG image (1200x630px recommended)
2. Save as `public/og-image.png`
3. Verify the meta tag resolves correctly when `SITE_URL` is set

### 3. Add `Cache-Control` Headers to SSR Responses

**Priority:** Medium -- prepares for Cloudflare CDN
**Effort:** ~30 minutes

The architecture doc notes that SSR responses should have appropriate cache headers for when Cloudflare is added. Currently no `Cache-Control` headers are set on SSR pages.

Options:
- **Stats page:** `Cache-Control: public, s-maxage=300, stale-while-revalidate=600` (5 min fresh, 10 min stale-while-revalidate)
- **News page:** `Cache-Control: public, s-maxage=120, stale-while-revalidate=300` (2 min fresh, 5 min stale-while-revalidate)
- **Static pages:** Already cached by Astro's static output

In Astro, set response headers in the page frontmatter:
```astro
---
Astro.response.headers.set('Cache-Control', 'public, s-maxage=300, stale-while-revalidate=600');
---
```

### 4. Region Alignment

**Priority:** Medium -- affects SSR latency
**Effort:** ~15 minutes (verification only)

Verify that all Railway services are in the same AWS region:

- Astro frontend service
- FastAPI backend service (`scoracle-data`)
- Neon Postgres database

If they're in different regions, the private network SSR calls will have higher latency than necessary. Consolidate to a single region (e.g., `us-east-1`).

### 5. Wire PostgREST Endpoints

**Priority:** Low -- deferred until PostgREST builds stabilize
**Effort:** ~2-4 hours (depends on response shape differences)

Once PostgREST views are defined in Postgres and the Railway build succeeds:

1. Change in `src/lib/utils/data-sources.ts`:
   ```typescript
   stats: 'postgrest',     // was 'fastapi'
   momentum: 'postgrest',  // was 'fastapi'
   ```
2. Set Railway env vars:
   ```
   POSTGREST_INTERNAL_URL=http://postgrest.railway.internal:3000
   PUBLIC_POSTGREST_URL=https://postgrest.scoracle.com
   ```
3. If PostgREST returns a different response shape than FastAPI, add transformations in the URL builder functions or in `src/lib/server/fetch.ts`
4. Test stats page, momentum tab, and comparison mode

### 6. Wire Go Backend Endpoints

**Priority:** Low -- deferred until Go service builds stabilize
**Effort:** ~2-4 hours

Once the Go ingestion service builds are stable on Railway:

1. Change in `src/lib/utils/data-sources.ts`:
   ```typescript
   news: 'go',     // was 'fastapi'
   twitter: 'go',  // was 'fastapi'
   ```
2. Set Railway env vars:
   ```
   GO_INTERNAL_URL=http://scoracle-go.railway.internal:8080
   PUBLIC_GO_API_URL=https://go-api.scoracle.com
   ```
3. Test news page, twitter tab, and co-mentions

### 7. Cloudflare CDN Integration

**Priority:** Low -- deferred until geographic user distribution demands it
**Effort:** ~1-2 hours

Per the architecture doc, this is a future enhancement:

1. Point domain nameservers to Cloudflare
2. Cloudflare proxies all requests to Railway
3. Static assets cached at edge after first request per region
4. SSR responses cached per the `Cache-Control` headers from task #3
5. Free tier covers CDN, DDoS protection, and SSL

No code changes required -- Cloudflare sits transparently in front of Railway.

---

## Completed Items (from original migration open items list)

| Original Item | Status | Done In |
|---|---|---|
| Update root `README.md` | Done | `d6cb36e` (2026-02-24 restructure) |
| Rewrite `astro-frontend/README.md` | Done | `d6cb36e` (consolidated into single root README) |
| Docker container deployment config | Done | PR #34 + `d6cb36e` (Dockerfile, railway.toml, .dockerignore) |
| Remove all Vercel references from source | Done | 2026-02-24 audit fixes |
| Flatten repo structure | Done | `d6cb36e` (2026-02-24 restructure) |
