# Static Data Files

This directory contains the pre-generated JSON files for autocomplete functionality.

## Files

- `football.json` - Football (Soccer) players and teams
- `nba.json` - NBA players and teams  
- `nfl.json` - NFL players and teams

## Generation

These files are generated from the SQLite databases using:

```bash
cd ../backend
python scripts/export_sqlite_to_json.py
```

Then copy the output to this directory.

## Note

Copy these files from `frontend/public/data/` to this directory:

```bash
cp ../frontend/public/data/*.json ./static/data/
```

