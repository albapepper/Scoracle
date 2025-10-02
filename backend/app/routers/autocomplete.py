from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from app.services.balldontlie_api import balldontlie_service

router = APIRouter()

class AutocompleteSuggestion(BaseModel):
    id: int
    label: str
    entity_type: str
    sport: str
    team_abbr: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class AutocompleteResponse(BaseModel):
    query: str
    entity_type: str
    sport: str
    results: List[AutocompleteSuggestion]

@router.get("/autocomplete/{entity_type}", response_model=AutocompleteResponse)
async def autocomplete(
    entity_type: str,
    q: str = Query(..., min_length=1, description="Partial name to search"),
    sport: str = Query("NBA", description="Sport (currently NBA supported)"),
    limit: int = Query(8, ge=1, le=15)
):
    entity_type = entity_type.lower()
    if entity_type not in {"player", "team"}:
        raise HTTPException(status_code=400, detail="entity_type must be 'player' or 'team'")

    # Minimum 2 chars before hitting upstream to reduce noise
    if len(q.strip()) < 2:
        return AutocompleteResponse(query=q, entity_type=entity_type, sport=sport, results=[])

    try:
        if entity_type == "player":
            raw = await balldontlie_service.search_players(q, sport=sport)
            suggestions = []
            for p in raw:
                team = p.get("team", {}) or {}
                label = f"{p.get('first_name','')} {p.get('last_name','')}".strip()
                if team.get("abbreviation"):
                    label = f"{label} ({team.get('abbreviation')})"
                suggestions.append(AutocompleteSuggestion(
                    id=p.get("id"),
                    label=label,
                    entity_type=entity_type,
                    sport=sport,
                    team_abbr=team.get("abbreviation"),
                    first_name=p.get("first_name"),
                    last_name=p.get("last_name"),
                ))
        else:
            raw = await balldontlie_service.search_teams(q, sport=sport)
            suggestions = []
            for t in raw:
                label = t.get("full_name") or t.get("name") or "Unknown Team"
                suggestions.append(AutocompleteSuggestion(
                    id=t.get("id"),
                    label=label,
                    entity_type=entity_type,
                    sport=sport,
                    team_abbr=t.get("abbreviation") or t.get("abbr"),
                ))

        return AutocompleteResponse(
            query=q,
            entity_type=entity_type,
            sport=sport,
            results=suggestions[:limit]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Autocomplete error: {str(e)}")