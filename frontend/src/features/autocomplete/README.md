# Autocomplete Implementation

## Current Setup: Backend API Calls

The autocomplete currently queries the backend API directly via `/api/v1/{sport}/autocomplete/{entity_type}` endpoints. This provides real-time results from the backend SQLite database.

## Switching Back to IndexedDB (Frontend Local DB)

To revert to the IndexedDB-based autocomplete for faster local searches:

1. **Update `useAutocomplete.ts`:**
   - Import IndexedDB search functions: `searchPlayers`, `searchTeams` from `../../services/indexedDB`
   - Import `mapSportToBackendCode` from `../../utils/sportMapping`
   - Import `mapResults` from `./worker/map`
   - Replace the backend API calls with IndexedDB searches (see git history for previous implementation)

2. **Re-enable IndexedDB sync in `SportContext.tsx`:**
   - Import `useIndexedDBSync` hook
   - Add the sync hook back to `SportContextProvider`
   - This will automatically sync bootstrap data when sport changes

3. **Ensure bootstrap endpoint works:**
   - The backend `/api/v1/{sport}/bootstrap` endpoint must be functional
   - This endpoint seeds IndexedDB with player/team data

## Benefits of Each Approach

**Backend API (Current):**
- Always up-to-date data
- No sync complexity
- Works immediately without bootstrap
- Slightly slower (network latency)

**IndexedDB (Previous):**
- Instant local searches (no network calls)
- Works offline after initial sync
- Requires bootstrap sync on sport change
- More complex setup

