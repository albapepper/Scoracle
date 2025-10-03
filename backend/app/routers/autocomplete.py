from fastapi import APIRouter, HTTPException, Query, Request, Response
from typing import List, Optional
from pydantic import BaseModel
import time
import logging

from app.services.balldontlie_api import balldontlie_service
from app.db.registry import entity_registry

router = APIRouter()
logger = logging.getLogger(__name__)

_CACHE: dict = {}
_CACHE_HITS = 0
_CACHE_MISSES = 0
_TTL_SECONDS = 30  # short TTL suitable for rapid typing; prevents stale roster lingering too long

def _cache_key(entity_type: str, sport: str, q: str, limit: int) -> str:
    return f"{entity_type}|{sport}|{q.lower()}|{limit}"

def _cache_get(key: str):
    now = time.time()
    entry = _CACHE.get(key)
    if not entry:
        return None
    expires_at, data = entry
    if expires_at < now:
        _CACHE.pop(key, None)
        return None
    return data

def _cache_set(key: str, data):
    _CACHE[key] = (time.time() + _TTL_SECONDS, data)

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
    request: Request,
    response: Response,
    entity_type: str,
    q: str = Query(..., min_length=1, description="Partial name to search"),
    sport: str = Query("NBA", description="Sport (currently NBA supported)"),
    limit: int = Query(8, ge=1, le=15)
):
    raw_entity_type = entity_type
    entity_type = (entity_type or "").strip().lower()
    if entity_type not in {"player", "team"}:
        # Log a hint for debugging mismatches
        request.app.logger.warning(
            "Autocomplete invalid entity_type received",
            extra={"raw": raw_entity_type, "normalized": entity_type, "path": str(request.url)}
        )
        raise HTTPException(status_code=400, detail="Entity type must be 'player' or 'team'")

    # Minimum 2 chars before hitting upstream to reduce noise
    if len(q.strip()) < 2:
        return AutocompleteResponse(query=q, entity_type=entity_type, sport=sport, results=[])

    try:
        cache_key = _cache_key(entity_type, sport, q, limit)
        global _CACHE_HITS, _CACHE_MISSES
        cached = _cache_get(cache_key)
        if cached is not None:
            _CACHE_HITS += 1
            response.headers["X-Autocomplete-Cache"] = "HIT"
            response.headers["X-Autocomplete-Cache-Hits"] = str(_CACHE_HITS)
            response.headers["X-Autocomplete-Cache-Misses"] = str(_CACHE_MISSES)
            return AutocompleteResponse(
                query=q,
                entity_type=entity_type,
                sport=sport,
                results=cached[:limit]
            )
        _CACHE_MISSES += 1
        response.headers["X-Autocomplete-Cache"] = "MISS"
        response.headers["X-Autocomplete-Cache-Hits"] = str(_CACHE_HITS)
        response.headers["X-Autocomplete-Cache-Misses"] = str(_CACHE_MISSES)
        # Try registry first
        try:
            registry_results = await entity_registry.search(sport, entity_type, q, limit=limit)
            if registry_results:
                data = [{
                    'id': r['id'],
                    'label': r.get('full_name') or r.get('team_abbr') or str(r['id']),
                    'team_abbr': r.get('team_abbr'),
                    'sport': r.get('sport'),
                    'entity_type': r.get('entity_type')
                } for r in registry_results]
                _cache_set(cache_key, data)
                return AutocompleteResponse(
                    query=q,
                    entity_type=entity_type,
                    sport=sport,
                    results=data[:limit]
                )
        except Exception as e:
            logger.warning("Registry search failed, falling back to upstream: %s", e)

        # Fallback to upstream service (currently only NBA implemented)
        service = None
        if sport.upper() == 'NBA':
            service = balldontlie_service
        if service is None:
            raise HTTPException(status_code=400, detail=f"Unsupported sport for upstream fallback: {sport}")

        try:
            if entity_type == 'player':
                results = await service.search_players(q)
                data = [
                    {
                        'id': p['id'],
                        'label': f"{p.get('first_name','')} {p.get('last_name','')}".strip(),
                        'team_abbr': (p.get('team') or {}).get('abbreviation'),
                        'sport': sport,
                        'entity_type': 'player'
                    }
                    for p in results
                ]
            elif entity_type == 'team':
                results = await service.search_teams(q)
                data = [
                    {
                        'id': t['id'],
                        'label': t.get('full_name') or t.get('name'),
                        'team_abbr': t.get('abbreviation'),
                        'sport': sport,
                        'entity_type': 'team'
                    }
                    for t in results
                ]
            else:
                raise HTTPException(status_code=400, detail="entity_type must be 'player' or 'team'")
        except Exception as e:
            logger.error("Autocomplete upstream error: %s", e)
            raise HTTPException(status_code=502, detail="Upstream service error")

        _cache_set(cache_key, data)
        return AutocompleteResponse(
            query=q,
            entity_type=entity_type,
            sport=sport,
            results=data[:limit]
        )
    except HTTPException:
        raise
    except Exception as e:
        # Include limited context for diagnostics
        request.app.logger.error("Autocomplete internal error", extra={"error": str(e), "q": q, "entity_type": entity_type})
        raise HTTPException(status_code=500, detail="Autocomplete internal error")