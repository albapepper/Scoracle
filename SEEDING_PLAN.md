# Frontend DB Seeding Plan

## Requirements

### Football (Soccer)
- **Players**: name, ID, current team
- **Teams**: name, ID, league (5 top European leagues + MLS)
- **Leagues**: Premier League (39), La Liga (140), Serie A (135), Bundesliga (78), Ligue 1 (61), MLS (253)

### NBA
- **Players**: name, ID, current team  
- **Teams**: name, ID, division

### NFL
- **Players**: name, ID, current team
- **Teams**: name, ID, division

## Implementation Steps

### 1. Update Backend Seeding Script
- [ ] Capture league names for football teams (map league IDs to names)
- [ ] Fetch division info for NBA teams (from `get_basketball_team_basic`)
- [ ] Fetch division info for NFL teams (check if API provides it)
- [ ] Store league/division in `current_league` field

### 2. Update Bootstrap Endpoint
- [ ] Include `league` field for teams in response
- [ ] Map `current_league` to appropriate field name

### 3. Update Frontend IndexedDB Schema
- [ ] Add `league` field to `TeamRecord` interface
- [ ] Update `upsertTeams` to store league/division

### 4. Update Frontend Sync Service
- [ ] Handle `league` field from bootstrap response
- [ ] Store league/division in IndexedDB

## League Name Mapping (Football)

```python
LEAGUE_NAMES = {
    39: "Premier League",
    140: "La Liga", 
    135: "Serie A",
    78: "Bundesliga",
    61: "Ligue 1",
    253: "MLS"
}
```

## Next Steps

1. Update seeding script to capture league/division
2. Update bootstrap endpoint
3. Update frontend schema and sync
4. Test with API key

