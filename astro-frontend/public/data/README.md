# Autocomplete Data

This directory should contain JSON files with player and team data for autocomplete functionality:

- `nba-players.json`
- `nba-teams.json`
- `nfl-players.json`
- `nfl-teams.json`
- `football-players.json`
- `football-teams.json`

Each file should be an array of objects with at least `id` and `name` properties.

Example:
```json
[
  {
    "id": "player-123",
    "name": "John Doe",
    "team": "Team Name"
  }
]
```

You can copy these files from the existing frontend directories:
- `/frontend/public/data/`

> Note: `/scoracle-svelte/static/data/` is legacy and no longer present in this repository.
