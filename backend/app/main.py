"""Canonical FastAPI application entrypoint.

Minimal routers: widgets (entity data), news (articles).
"""
from contextlib import asynccontextmanager
import logging
import os
from pathlib import Path
import httpx

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi import Request, HTTPException

from app.config import settings
from app.routers import widgets, news, twitter, reddit, stats
from app.utils.middleware import CorrelationIdMiddleware, RateLimitMiddleware
from app.utils.errors import build_error_payload, map_status_to_code
from app.services.entity_index import initialize_entity_index

# Configure logging if not already configured
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# Shared HTTP client to reduce per-request connection churn
timeout = httpx.Timeout(connect=3.0, read=10.0, write=10.0, pool=3.0)
limits = httpx.Limits(max_keepalive_connections=20, max_connections=50)

# Detect Vercel environment for CORS configuration
IS_VERCEL = os.getenv("VERCEL") == "1"


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting application")
    # follow_redirects=True is needed for Google News RSS which returns 302
    app.state.http_client = httpx.AsyncClient(timeout=timeout, limits=limits, follow_redirects=True)

    # Initialize entity index for news validation
    # Try multiple paths to find the database (local dev vs Vercel)
    db_paths = [
        Path(__file__).parent.parent.parent / "instance" / "localdb",  # Local: backend/../instance
        Path("/var/task/instance/localdb"),  # Vercel absolute path
        Path("instance/localdb"),  # Relative to cwd
        Path(__file__).parent.parent / "instance" / "localdb",  # Alternative
    ]

    logger.info(f"Looking for entity database. CWD: {os.getcwd()}, __file__: {__file__}")

    for db_path in db_paths:
        logger.info(f"Checking path: {db_path} (exists: {db_path.exists()})")
        if db_path.exists():
            logger.info(f"Found entity database at {db_path}")
            try:
                initialize_entity_index(db_path)
                logger.info("Entity index initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize entity index: {e}", exc_info=True)
            break
    else:
        logger.warning("Entity database not found in any expected location")

    yield
    client = getattr(app.state, "http_client", None)
    if client is not None:
        await client.aclose()
    logger.info("Stopping application")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.PROJECT_VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# Middleware
app.add_middleware(GZipMiddleware, minimum_size=500)
app.add_middleware(CorrelationIdMiddleware)
# Only enable rate limiting in non-Vercel environments (Vercel has its own)
if not IS_VERCEL:
    app.add_middleware(RateLimitMiddleware)

# CORS: prefer explicit origins or an origin regex; avoid '*' by default.
cors_origins = ["*"] if settings.BACKEND_CORS_ALLOW_ALL else settings.BACKEND_CORS_ORIGINS
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=settings.BACKEND_CORS_ORIGIN_REGEX,
    allow_origins=cors_origins,
    allow_credentials=False,  # keep hydration simple; enable only when needed
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure rate limit settings on app state
app.state.rate_limit = (
    bool(settings.RATE_LIMIT_ENABLED),
    float(settings.RATE_LIMIT_RPS),
    int(settings.RATE_LIMIT_BURST),
)

# Routers - only what we need
app.include_router(widgets.router, prefix=settings.API_V1_STR)   # /widget/{type}/{id}?sport=X
app.include_router(stats.router, prefix=settings.API_V1_STR)     # /stats/{type}/{id}?sport=X&category=Y
app.include_router(news.router, prefix=settings.API_V1_STR)      # /news/{entity_name}
app.include_router(twitter.router, prefix=settings.API_V1_STR)   # Twitter (future)
app.include_router(reddit.router, prefix=settings.API_V1_STR)    # Reddit (future)


@app.get("/health")
async def health():
    from app.services.entity_index import get_entity_index
    entity_index = get_entity_index()
    return {
        "status": "ok",
        "version": settings.PROJECT_VERSION,
        "entity_index": {
            "loaded": entity_index.is_loaded,
            "patterns": len(entity_index._patterns) if entity_index.is_loaded else 0,
        },
    }


@app.get("/")
async def root_index():
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.PROJECT_VERSION,
        "endpoints": {
            "widget": "/api/v1/widget/{type}/{id}?sport=FOOTBALL|NBA|NFL",
            "stats": "/api/v1/stats/{type}/{id}?sport=FOOTBALL|NBA|NFL&category=offense|defense|...",
            "news": "/api/v1/news?sport=NFL|NBA|FOOTBALL&entity_id=123&entity_type=player|team",
            "news_legacy": "/api/v1/news/{entity_name}?sport=NFL|NBA|FOOTBALL",
        },
        "docs": "/api/docs",
        "health": "/health",
    }


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    cid = getattr(request.state, "correlation_id", None)
    payload = build_error_payload(
        message=str(getattr(exc, "detail", "HTTP error")),
        status=exc.status_code,
        correlation_id=cid,
        code=map_status_to_code(exc.status_code),
    )
    return JSONResponse(payload, status_code=exc.status_code)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    cid = getattr(request.state, "correlation_id", None)
    payload = build_error_payload("Internal server error", 500, correlation_id=cid)
    return JSONResponse(payload, status_code=500)
