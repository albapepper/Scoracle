from fastapi import APIRouter, HTTPException, Query, Request, Response
from typing import List, Optional
from pydantic import BaseModel
import time
import logging

from app.services.apisports import apisports_service
from app.db.local_dbs import suggestions_from_local_or_upstream

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
    _t0 = time.perf_counter()
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
        # add diagnostics headers
        response.headers["X-Autocomplete-Q-Len"] = str(len(q.strip()))
        response.headers["X-Autocomplete-Elapsed-ms"] = f"{(time.perf_counter()-_t0)*1000:.0f}"
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
            response.headers["X-Autocomplete-Q-Len"] = str(len(q.strip()))
            response.headers["X-Autocomplete-Elapsed-ms"] = f"{(time.perf_counter()-_t0)*1000:.0f}"
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
        # First try local DB, fallback to upstream and warm local store
        try:
            data = await suggestions_from_local_or_upstream(entity_type, sport, q, limit)
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Autocomplete provider error: %s", e)
            raise HTTPException(status_code=502, detail="Suggestion provider error")

        _cache_set(cache_key, data)
        response.headers["X-Autocomplete-Q-Len"] = str(len(q.strip()))
        response.headers["X-Autocomplete-Elapsed-ms"] = f"{(time.perf_counter()-_t0)*1000:.0f}"
        response.headers["X-Upstream-Provider"] = "local-sqlite"
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