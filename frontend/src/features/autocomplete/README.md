# Autocomplete Implementation

Autocomplete runs entirely on the frontend using bundled JSON files loaded into memory. No IndexedDB, no backend calls during search.

## Architecture: In-Memory Search

1. **Data Loading**: `dataLoader.ts` fetches `/data/{sport}.json` once per sport and caches in memory
2. **Search**: `useAutocomplete.ts` performs fast in-memory fuzzy search with scoring
3. **Preloading**: `SportContext` preloads data when user switches sports

### Files

- `dataLoader.ts` - Loads JSON, caches in memory, provides search functions
- `useAutocomplete.ts` - React hook for debounced autocomplete
- `types.ts` - TypeScript interfaces

## Performance

- **First load**: ~50-200ms to fetch JSON (cached by browser/CDN)
- **Search**: <5ms in-memory (instant feel)
- **Memory**: ~500KB-2MB per sport (acceptable for modern browsers)

## Regenerating Data

When backend SQLite files change:

```bash
python backend/scripts/export_sqlite_to_json.py
```

This refreshes JSON snapshots under `frontend/public/data`. Commit and redeploy.

## Why Not IndexedDB?

The previous IndexedDB implementation added ~900 lines of code for:
- Database schema management
- Sync service with ETag handling  
- Background sync hooks

The new in-memory approach achieves the same performance with ~200 lines and zero complexity around database versioning, migrations, or sync failures.
