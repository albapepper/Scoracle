# ── Stage 1: Build ────────────────────────────────────────────────────────────
FROM node:20-alpine AS build
WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . ./
RUN npm run build \
 && test -f dist/server/entry.mjs

# ── Stage 2: Production runtime ──────────────────────────────────────────────
FROM node:20-alpine AS runtime
WORKDIR /app

ENV NODE_ENV=production
ENV HOST=0.0.0.0
ENV PORT=3000

# Run as non-root for security
RUN addgroup -S app && adduser -S app -G app

COPY --from=build /app/package*.json ./
RUN npm ci --omit=dev && npm cache clean --force

COPY --from=build /app/dist ./dist

RUN chown -R app:app /app
USER app

EXPOSE 3000
CMD ["node", "dist/server/entry.mjs"]
