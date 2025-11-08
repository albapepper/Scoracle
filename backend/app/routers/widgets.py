import hashlib
import json
import time
import uuid
from typing import Optional

from fastapi import APIRouter, Query, HTTPException, Request, Response
from fastapi.responses import JSONResponse

from app.models.schemas import WidgetEnvelope, WidgetDiagnostics
from app.services import widget_service
from app.services.cache import widget_cache
from app.config import settings

router = APIRouter()

from app.utils.constants import WIDGET_VERSION, DEFAULT_WIDGET_TTL, MAX_WIDGET_TTL

DEFAULT_TTL = DEFAULT_WIDGET_TTL


def _stable_hash(obj) -> str:
    try:
        data = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")
    except Exception:
        data = repr(obj).encode("utf-8")
    return hashlib.sha256(data).hexdigest()[:32]


@router.get("/widgets/player/{player_id}")
async def player_widget(player_id: str, request: Request, response: Response, sport: str = Query(...), season: str | None = Query(None), debug: int | None = Query(0)):
    t0 = time.perf_counter()
    season_norm = season if (season and season.lower() != "current") else None
    cache_key = f"widgets:player:{sport.upper()}:{player_id}:{season_norm or ''}:v{WIDGET_VERSION}"

    cached = widget_cache.get(cache_key)
    request_id = uuid.uuid4().hex[:12]
    if cached is not None:
        env: WidgetEnvelope = cached
        inm = request.headers.get("if-none-match")
        if inm and env.etag and inm == env.etag:
            headers = {
                "ETag": env.etag,
                "Cache-Control": "public, max-age=300, stale-while-revalidate=600",
            }
            return Response(status_code=304, headers=headers)
        if debug:
            env.diagnostics = WidgetDiagnostics(provider="api-sports", cache="hit", request_id=request_id, latency_ms=int((time.perf_counter()-t0)*1000))
        response.headers["ETag"] = env.etag or ""
        response.headers["Cache-Control"] = "public, max-age=300, stale-while-revalidate=600"
        return JSONResponse(env.dict())

    try:
        payload = await widget_service.build_player_widget_payload(sport, player_id, season_norm)
        etag = _stable_hash({"v": WIDGET_VERSION, "payload": payload})
        env = WidgetEnvelope(
            type="player",
            version=WIDGET_VERSION,
            cacheKey=cache_key,
            ttl=DEFAULT_TTL,
            etag=etag,
            payload=payload,
        )
        widget_cache.set(cache_key, env, ttl=DEFAULT_TTL)
        if debug:
            env.diagnostics = WidgetDiagnostics(provider="api-sports", cache="miss", request_id=request_id, latency_ms=int((time.perf_counter()-t0)*1000))
        response.headers["ETag"] = etag
        response.headers["Cache-Control"] = "public, max-age=300, stale-while-revalidate=600"
        return JSONResponse(env.dict())
    except HTTPException as he:
        payload = {"error": he.detail if isinstance(he.detail, str) else str(he.detail), "status": he.status_code, "retryAfter": 60}
        etag = _stable_hash({"v": WIDGET_VERSION, "payload": payload})
        env = WidgetEnvelope(
            type="player",
            version=WIDGET_VERSION,
            cacheKey=cache_key,
            ttl=60,
            etag=etag,
            payload=payload,
            diagnostics=WidgetDiagnostics(provider="api-sports", cache="miss", request_id=request_id, latency_ms=int((time.perf_counter()-t0)*1000)) if debug else None,
        )
        response.headers["ETag"] = etag
        response.headers["Cache-Control"] = "public, max-age=60"
        return JSONResponse(env.dict(), status_code=he.status_code)
    except Exception:
        payload = {"error": "internal server error", "retryAfter": 60}
        etag = _stable_hash({"v": WIDGET_VERSION, "payload": payload})
        env = WidgetEnvelope(
            type="player",
            version=WIDGET_VERSION,
            cacheKey=cache_key,
            ttl=60,
            etag=etag,
            payload=payload,
            diagnostics=WidgetDiagnostics(provider="api-sports", cache="miss", request_id=request_id, latency_ms=int((time.perf_counter()-t0)*1000)) if debug else None,
        )
        response.headers["ETag"] = etag
        response.headers["Cache-Control"] = "public, max-age=60"
        return JSONResponse(env.dict(), status_code=500)
"""
Remove the temporary HTML-returning endpoint to avoid duplicate responsibilities.
The canonical widget endpoint is /api/v1/widgets/player/{player_id} with JSON envelope.
"""
