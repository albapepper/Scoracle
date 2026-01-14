# Local Backend Removal Guide

## Overview

The frontend now connects to an external backend hosted on Railway:
```
https://scoracle-data-production.up.railway.app/api/v1
```

The local Python/FastAPI backend is no longer needed and can be removed.

## Current Architecture

**Before:** Frontend + Backend deployed together on Vercel (Python serverless function)
**After:** Frontend-only on Vercel, API calls go to external Railway backend

## Files & Directories to Remove

```
backend/                  # Entire FastAPI backend
api/                      # Vercel serverless wrapper
local.ps1                 # Local dev script (starts backend)
requirements.txt          # Root Python requirements
```

## Configuration Already Updated

- `vercel.json` - Removed Python serverless routing and functions
- `astro-frontend/.env.example` - Points to Railway backend

## Frontend Components

The 13 Astro components have `localhost:8000` fallbacks that are only used when `PUBLIC_API_URL` is not set. In production (Vercel), the env var is always set, so these fallbacks are inactive.

## Local Development

For local frontend development:
1. Copy `astro-frontend/.env.example` to `astro-frontend/.env`
2. Run `cd astro-frontend && npm run dev`
3. Frontend will call the production Railway API directly

No local backend needed.

## Removal Commands

```bash
# Remove backend directories and files
rm -rf backend/
rm -rf api/
rm -f local.ps1
rm -f requirements.txt
```

## Vercel Environment Variables

Ensure `PUBLIC_API_URL` is set in Vercel project settings:
```
PUBLIC_API_URL=https://scoracle-data-production.up.railway.app/api/v1
```

## Frontend Optimizations Applied

The following performance optimizations have been made:

1. **Hybrid SSR** - Entity and mentions pages use server-side rendering for faster initial load
2. **D3 Removed** - Replaced with lightweight custom SVG implementation (-200KB bundle)
3. **Reduced Motion** - Respects `prefers-reduced-motion` for accessibility
4. **Console Stripping** - Production builds remove console.log statements

## Optional: Image Optimization

The `/public` directory contains ~11MB of PNG images. Consider optimizing:

```bash
# Using ImageOptim (macOS) or similar tool
# Or convert to WebP for 70-90% size reduction:

# Install cwebp (part of libwebp)
# Ubuntu/Debian: sudo apt install webp
# macOS: brew install webp

# Convert PNGs to WebP
cd astro-frontend/public
for f in *.png; do cwebp -q 85 "$f" -o "${f%.png}.webp"; done
```

Current image sizes:

- NBA logo.png: 2.0MB
- NFL logo.png: 1.9MB
- fifa logo.png: 1.9MB
- new logo.png: 1.9MB
- logo.png: 337KB
