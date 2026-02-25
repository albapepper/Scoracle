# Scoracle — Frontend Hosting Architecture

## Overview

This document covers the migration of the Scoracle frontend from Vercel to Railway and the architectural decisions around Astro's rendering model. It also notes a future Cloudflare integration for edge asset delivery.

The guiding principle: **pre-render everything possible at build time, use SSR only where live data is required, and keep the entire stack on Railway's private network.**

---

## Why Railway Over Vercel

### Cost Predictability

Vercel's pricing model meters edge requests, function invocations, bandwidth, and CPU time as separate line items with overage charges that compound unpredictably. For an ad-supported sports stats site, this is a structural mismatch:

- Traffic spikes around live games are expected and desirable, but on Vercel they directly translate to unpredictable billing
- Bot and crawler traffic (normal for an ad-indexed site) counts against quotas identically to real users
- Revenue scales indirectly via ad impressions, meaning a traffic spike that increases costs may not proportionally increase revenue in early growth stages

Railway's usage-based model charges for actual CPU and memory consumption. A traffic spike costs proportionally more but does not trigger the kind of compounding overage charges documented in Vercel's billing horror stories. Costs are transparent and predictable.

### Performance — Private Network Advantage

The most significant performance gain comes from network topology. With Vercel, every database call from a serverless function travels over the public internet to the data source. With Railway, the Astro SSR server and the PostgREST service share Railway's private internal network.

For stat-heavy pages where SSR fetches data from PostgREST at render time, this means the most latency-sensitive operation — the database round trip — happens entirely within Railway's private network before the response is sent to the user.

### No Cold Starts

Vercel's serverless functions scale to zero between requests and incur cold start latency when traffic resumes. Railway runs long-lived containers with no cold starts. For a sports site where users arrive in bursts around game times, consistent low latency matters more than theoretical scale-to-zero savings.

Independent benchmarks have shown Railway performing 3–4× faster than Vercel on SSR workloads in SvelteKit and Vanilla JS tests, with React SSR results being comparable.

---

## Astro Rendering Strategy

### Pre-Rendering (Static) — Default

The majority of Scoracle pages are pre-rendered to static HTML at build time. These include:

- Marketing and informational pages
- Player and team profile shells
- Navigation, layout, and UI chrome

Pre-rendered pages are served directly from Railway as static files. No server computation occurs per request. These files are small, highly compressible, and cache-friendly. This is the primary source of frontend snappiness on Railway — most pages require no server work at all.

### SSR — Live Data Pages

Pages requiring live data (current standings, live game stats, real-time leaderboards) use Astro's SSR mode. On request, the Astro server fetches data from PostgREST over Railway's private network, renders the complete HTML, and returns it to the user.

The result is a fully rendered page delivered in a single round trip, with no client-visible loading state for the initial data. The user receives complete HTML rather than a shell that populates asynchronously.

```
User request
    ↓
Astro SSR server (Railway)
    ↓ private network
PostgREST (Railway) → Neon Postgres
    ↓
Fully rendered HTML → User
```

### Islands Architecture

Astro's islands architecture ensures that interactive components (charts, filters, live score updates) are hydrated selectively on the client. The majority of the page is inert HTML — no JavaScript overhead for content that doesn't need it. This keeps Time to Interactive low independent of hosting infrastructure.

---

## Deployment on Railway

The Astro frontend is deployed as a Node.js SSR service within the same Railway project as the Go ingestion service and PostgREST. All three services share Railway's private internal network.

### Build Configuration

Astro requires the Node.js adapter for SSR mode on Railway:

```javascript
// astro.config.mjs
import { defineConfig } from 'astro/config';
import node from '@astrojs/node';

export default defineConfig({
  output: 'static', // In Astro 5+, static with an adapter = hybrid mode
  adapter: node({
    mode: 'standalone'
  })
});
```

In Astro 5+, `output: 'static'` with an adapter present provides hybrid behavior: pages are static by default, and individual pages opt into SSR with `export const prerender = false`.

### Railway Service Configuration

Railway auto-detects Node.js projects. Set the following environment variables in the Railway service dashboard:

```
PUBLIC_POSTGREST_URL=http://postgrest.railway.internal:3000
PUBLIC_GO_API_URL=http://scoracle-data.railway.internal:8080
NODE_ENV=production
```

Using Railway's internal hostnames (`.railway.internal`) ensures all service-to-service communication stays on the private network and never traverses the public internet.

### Region Alignment

Deploy the Astro service in the same Railway region as PostgREST and the Neon database (e.g., `AWS us-east-1`). This minimizes the latency of the private network calls made during SSR data fetching.

---

## Future: Cloudflare Edge Caching

> **Note: This is a future enhancement, not a current priority.** The Railway-only setup is sufficient for Scoracle's initial user base. Add Cloudflare when geographic distribution of users becomes a measurable latency concern.

Railway does not include a built-in CDN. For the initial launch, static assets are served directly from Railway's single-region infrastructure. For a primarily US-based early user base this is acceptable and the performance difference versus a CDN is negligible.

When Cloudflare is added, the integration is straightforward:

1. Point your domain's nameservers to Cloudflare
2. Cloudflare proxies all requests to Railway
3. Static assets (JS, CSS, images) are cached at Cloudflare's global edge after the first request per region
4. SSR responses can be cached at the edge with appropriate `Cache-Control` headers for routes where data staleness is acceptable

The added benefits beyond CDN are meaningful for a sports site:

- **DDoS protection** — Cloudflare absorbs malicious traffic before it reaches Railway, eliminating the class of billing disasters documented against Vercel deployments
- **Bot management** — filters crawler and scraper traffic
- **Free tier** — Cloudflare's free plan covers CDN, DDoS protection, and SSL for most early-stage traffic levels

This addition when the time comes requires no changes to the Railway deployment — Cloudflare sits in front of the existing setup transparently.

---

## Summary

| Concern | Approach |
|---|---|
| Static pages | Astro pre-render at build time |
| Live data pages | Astro SSR, server-to-server with PostgREST |
| Interactive components | Astro islands, selective hydration |
| Hosting | Railway (same project as backend services) |
| Private networking | Astro ↔ PostgREST via Railway internal hostnames |
| Cost model | Railway usage-based, no serverless overages |
| Cold starts | None — Railway long-lived containers |
| Edge CDN | **Future:** Cloudflare free tier when geographic scale requires it |
