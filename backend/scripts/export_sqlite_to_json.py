#!/usr/bin/env python3
"""Export SQLite player/team data to JSON files for frontend bundling.

This script reads from the SQLite databases and exports them as JSON files
that can be bundled with the frontend build. The frontend will load these
into IndexedDB for fast local autocomplete.

Usage:
    python backend/scripts/export_sqlite_to_json.py
"""

import json
import os
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.database.local_dbs import (
    list_all_players, 
    list_all_teams, 
    get_player_by_id,
    get_team_by_id,
    _db_path_for_sport,
    _strip_specials_preserve_case,
)

SPORTS = {
    "football": "FOOTBALL",
    "nba": "NBA",
    "nfl": "NFL",
}

def export_sport(sport_key: str, sport_code: str, output_dir: Path):
    """Export a single sport's data to JSON."""
    print(f"Exporting {sport_key} ({sport_code})...")
    
    try:
        players = list_all_players(sport_code)
        teams = list_all_teams(sport_code)
        
        # Convert to format expected by frontend
        players_items = []
        for pid, name in players:
            # Clean name - preserve the full name (remove special chars but keep all name parts)
            cleaned_name = _strip_specials_preserve_case(name or "")
            
            # Get current team from database
            current_team = None
            try:
                row = get_player_by_id(sport_code, int(pid))
                current_team = row.get("current_team") if row else None
                if current_team:
                    current_team = _strip_specials_preserve_case(current_team)
            except Exception:
                current_team = None
            
            players_items.append({
                "id": int(pid),
                "name": cleaned_name,
                "currentTeam": current_team,
            })
        
        # Get team details including league/division
        teams_items = []
        for tid, name in teams:
            cleaned_name = _strip_specials_preserve_case(name or "")
            team_data = {"id": int(tid), "name": cleaned_name}
            # Get league/division from database
            try:
                team_row = get_team_by_id(sport_code, int(tid))
                if team_row and team_row.get("current_league"):
                    team_data["league"] = team_row.get("current_league")
            except Exception:
                pass
            teams_items.append(team_data)
        
        from datetime import datetime, timezone
        generated_at = datetime.now(timezone.utc).isoformat()
        dataset_version = f"{sport_key}-{len(players_items)}p-{len(teams_items)}t-{generated_at[:10]}"
        
        output = {
            "sport": sport_code,
            "datasetVersion": dataset_version,
            "generatedAt": generated_at,
            "players": {
                "count": len(players_items),
                "items": players_items,
            },
            "teams": {
                "count": len(teams_items),
                "items": teams_items,
            },
        }
        
        output_file = output_dir / f"{sport_key}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"  Exported {len(players_items)} players, {len(teams_items)} teams to {output_file}")
        return True
        
    except Exception as e:
        print(f"  ✗ Error exporting {sport_key}: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main export function."""
    # Output to frontend/public/data (will be bundled with build)
    repo_root = Path(__file__).parent.parent.parent
    output_dir = repo_root / "frontend" / "public" / "data"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Exporting SQLite data to JSON files in {output_dir}")
    print("-" * 60)
    
    success_count = 0
    for sport_key, sport_code in SPORTS.items():
        if export_sport(sport_key, sport_code, output_dir):
            success_count += 1
    
    print("-" * 60)
    print(f"Exported {success_count}/{len(SPORTS)} sports successfully")
    
    if success_count == len(SPORTS):
        print("\nAll exports completed! JSON files are ready for frontend bundling.")
        print(f"  Files: {', '.join([f'{sport}.json' for sport in SPORTS.keys()])}")
        return 0
    else:
        print("\nSome exports failed. Check errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

