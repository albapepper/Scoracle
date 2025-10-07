# Generated API Types

This folder contains generated API types.

Run:

npm run api:types

The command fetches the FastAPI OpenAPI schema from [http://localhost:8000/api/openapi.json](http://localhost:8000/api/openapi.json) and writes TypeScript definitions to `api.ts`. Do not edit `api.ts` manually – regenerate after backend schema changes.
