# Autocomplete Implementation

Autocomplete now runs entirely on the frontend using the bundled bootstrap JSON + IndexedDB. The legacy backend endpoint `/api/v1/{sport}/autocomplete/{entity_type}` was removed, so all suggestions are generated locally.

## Current Setup: IndexedDB-first

1. `useIndexedDBSync` keeps the browser database in sync with `/api/v1/{sport}/bootstrap` (or the bundled JSON in `frontend/public/data`).
2. `useAutocomplete.ts` calls `searchPlayers`/`searchTeams` from `src/services/indexedDB.ts` and maps the results into UI-friendly labels.
3. No network calls are required for keystrokes, so the UX stays responsive even on flaky connections.

## Regenerating Data

When backend SQLite files change, run `python backend/scripts/export_sqlite_to_json.py` to refresh the JSON snapshots under `frontend/public/data`. Commit the updated JSON and redeploy; the frontend will ship the new dataset and automatically re-seed IndexedDB on first load.

## Optional Backend Fallback (Not Recommended)

If you ever reintroduce a server-driven autocomplete, you would need to:

1. Restore the FastAPI route and helper utilities that were previously located in `backend/app/routers/sport.py`.
2. Update `useAutocomplete.ts` to send requests to the new endpoint and handle latency/loading states.
3. Keep the IndexedDB logic as a graceful fallback in case the serverless environment cannot open SQLite files.

For now the fully local approach is the supported path, optimized for the Vercel/serverless deployment model.

