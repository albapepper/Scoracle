# Scoracle Backend Contract (Hydration)

This document defines the **canonical API contract** the Astro frontend should rely on.

## Base

- Base path: `/api/v1`
- Transport: JSON over HTTPS
- Errors: all errors are returned in the standardized envelope emitted by the global exception handlers.

### Error envelope

```json
{
  "error": {
    "code": "BAD_REQUEST|NOT_FOUND|RATE_LIMITED|UPSTREAM_ERROR|INTERNAL_ERROR",
    "message": "Human-readable message",
    "status": 400,
    "correlationId": "<optional>"
  }
}
```

## Common behavior

### Caching headers (recommended)

All GET endpoints should return a `Cache-Control` tuned for the data’s volatility.

- `max-age` applies to browsers.
- `s-maxage` applies to shared caches/CDNs.
- `stale-while-revalidate` allows the CDN/browser to serve cached content immediately while it refreshes in the background.
- Optional: `stale-if-error` allows serving cached content if the origin is temporarily failing.

### Correlation ID

- The backend echoes/sets `X-Correlation-ID` on every response.

### Rate limiting

- The backend may return `429` with a `Retry-After` header.

## Endpoints

### Widgets (API-Sports proxy)

`GET /api/v1/widget/{entity_type}/{entity_id}?sport=FOOTBALL|NBA|NFL`

- `entity_type`: `team` | `player`
- Returns: the **raw first item** from the provider response (`response[0]`) as JSON.
- Errors:
  - `400` invalid sport/type
  - `404` entity not found
  - `502` upstream/network errors or missing API key

Response: provider-shaped JSON object.

Recommended caching:
- Highly cacheable: long CDN TTL.

### News (Google News RSS)

`GET /api/v1/news/{entity_name}?hours=48`

Response:

```json
{
  "query": "LeBron James",
  "hours": 48,
  "count": 12,
  "articles": [
    {
      "title": "...",
      "link": "https://...",
      "pub_date": "2025-12-15T12:34:56+00:00",
      "source": "ESPN"
    }
  ]
}
```

Recommended caching:
- Moderately cacheable: short CDN TTL + generous `stale-while-revalidate`.

### Twitter/X (stub)

`GET /api/v1/twitter/{entity_type}/{entity_id}`

Response:

```json
{
  "entity_type": "player",
  "entity_id": "123",
  "count": 0,
  "tweets": []
}
```

### Reddit (stub)

`GET /api/v1/reddit/{entity_type}/{entity_id}`

Response:

```json
{
  "entity_type": "player",
  "entity_id": "123",
  "count": 0,
  "posts": []
}
```

## Non-goals (for now)

- No unified `/entity` endpoint is exposed as canonical.
- No frontend-specific shapes are introduced in the backend responses.
