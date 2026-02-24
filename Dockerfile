FROM node:20-alpine AS build
WORKDIR /app/astro-frontend

COPY astro-frontend/package*.json ./
RUN npm ci

COPY astro-frontend/ ./
RUN npm run build
RUN test -f dist/server/entry.mjs

FROM node:20-alpine AS runtime
WORKDIR /app/astro-frontend
ENV NODE_ENV=production
ENV HOST=0.0.0.0
ENV PORT=3000

COPY astro-frontend/package*.json ./
RUN npm ci --omit=dev

COPY --from=build /app/astro-frontend/dist ./dist

EXPOSE 3000
CMD ["node", "dist/server/entry.mjs"]
