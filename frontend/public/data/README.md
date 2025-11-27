# Bootstrap Data Files

This directory contains JSON files exported from the backend SQLite databases.
These files are bundled with the frontend build and used to seed IndexedDB for fast local autocomplete.

## Files

- `football.json` - Football players and teams
- `nba.json` - NBA players and teams  
- `nfl.json` - NFL players and teams

## Regenerating Files

When you update the backend SQLite databases, regenerate these JSON files:

```bash
python backend/scripts/export_sqlite_to_json.py
```

This will:

1. Read from `backend/instance/localdb/*.sqlite` files
2. Export to `frontend/public/data/*.json`
3. Format matches the bootstrap endpoint response format

After regenerating, commit the JSON files and redeploy. The frontend will automatically load them into IndexedDB on first visit.

## Workflow

1. Update SQLite databases in `backend/instance/localdb/`
2. Run export script: `python backend/scripts/export_sqlite_to_json.py`
3. Commit JSON files
4. Deploy (frontend will bundle JSON files automatically)
5. Users' IndexedDB will be seeded from bundled JSON on first load

This approach:

- ✅ Avoids serverless SQLite issues (files are bundled, not accessed at runtime)
- ✅ Provides fast local autocomplete (IndexedDB)
- ✅ Keeps backend SQLite for easy data modification
- ✅ Only requires redeploy when DB changes (which you'd do anyway)

