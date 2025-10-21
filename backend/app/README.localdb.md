# Local SQLite autocomplete databases

- Path: instance/localdb/{sport}.sqlite (configurable via LOCAL_DB_DIR)
- Sports supported: NBA, NFL, FOOTBALL (EPL alias supported)
- Minimal schema:
  - players(id INTEGER PRIMARY KEY, name TEXT, current_team TEXT, updated_at INTEGER)
  - teams(id INTEGER PRIMARY KEY, name TEXT, current_league TEXT, updated_at INTEGER)

Seeding

- Use the script app/scripts/seed_local_dbs.py to populate from API-Sports.
- Requires API_SPORTS_KEY env set.

Run (example):

- With uvicorn running, optional. Script runs independently.

Notes

- Autocomplete uses ONLY the local SQLite DB. No upstream calls are made by the autocomplete path.
- FOOTBALL umbrella covers Europe top 5 leagues + MLS when seeding.
