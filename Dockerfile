# ── Stage 1: Build ────────────────────────────────────────────────────────────
FROM node:20-alpine AS build
WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . ./
RUN npm run fetch-data \
 && npm run build \
 && test -f dist/server/entry.mjs

# ── Stage 2: Production dependencies ─────────────────────────────────────────
FROM node:20-alpine AS deps
WORKDIR /app

COPY package*.json ./
RUN npm ci --omit=dev && npm cache clean --force

# ── Stage 3: Production runtime ──────────────────────────────────────────────
FROM node:20-alpine AS runtime
WORKDIR /app

ENV NODE_ENV=production
ENV HOST=0.0.0.0
ENV PORT=3000

# Run as non-root for security
RUN addgroup -S app && adduser -S app -G app

# Use --chown on COPY instead of RUN chown -R (saves ~18s of recursive walk)
COPY --chown=app:app --from=deps /app/node_modules ./node_modules
COPY --chown=app:app --from=build /app/dist ./dist
COPY --chown=app:app package.json ./

USER app

EXPOSE 3000
CMD ["node", "dist/server/entry.mjs"]
