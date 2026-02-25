# Autocomplete Data

This directory contains JSON files with player and team data for client-side autocomplete:

- `nba.json` -- NBA players and teams
- `nfl.json` -- NFL players and teams
- `football.json` -- Football (soccer) players and teams (~78K entities)

Each file is an array of objects with at least `id` and `name` properties, loaded by the `EntityDataStore` on app startup for instant search.
