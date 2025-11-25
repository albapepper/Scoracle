"""Canonical FastAPI application entrypoint.

Mounts all routers and configures lifespan resources.
"""
from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi import Request, HTTPException

from app.config import settings
from app.routers import widgets, sport, news, twitter, reddit
from app.utils.middleware import CorrelationIdMiddleware, RateLimitMiddleware
from app.utils.errors import build_error_payload, map_status_to_code

# Logger must be defined BEFORE the try/except block that uses it
logger = logging.getLogger(__name__)

# Import news_fast defensively - it may fail if pyahocorasick isn't available
try:
    from app.services import news_fast
except ImportError as e:
    logger.warning(f"Failed to import news_fast (ahocorasick may be unavailable): {e}")
    news_fast = None
except Exception as e:
    logger.warning(f"Error importing news_fast: {e}")
    news_fast = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting application lifespan")
    try:
        # Optional cache warming: build automatons for active sports
        if news_fast:
            try:
                active_sports = {"NBA", "EPL", "FOOTBALL"}
                for s in active_sports:
                    news_fast._get_automatons(s)
                logger.info("Warmed news_fast automatons: %s", ", ".join(sorted(active_sports)))
            except Exception:
                logger.warning("Automaton warmup skipped due to error", exc_info=True)
        else:
            logger.info("news_fast unavailable - skipping automaton warmup")
        yield
    finally:
        logger.info("Stopping application lifespan")


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
app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure rate limit settings on app state
app.state.rate_limit = (
    bool(settings.RATE_LIMIT_ENABLED),
    float(settings.RATE_LIMIT_RPS),
    int(settings.RATE_LIMIT_BURST),
)

# Routers
app.include_router(widgets.router, prefix=settings.API_V1_STR)
app.include_router(sport.router, prefix=settings.API_V1_STR)
app.include_router(news.router, prefix=settings.API_V1_STR)
app.include_router(twitter.router, prefix=settings.API_V1_STR)
app.include_router(reddit.router, prefix=settings.API_V1_STR)


@app.get("/health")
async def health():
    return {"status": "ok", "version": settings.PROJECT_VERSION}


# Simple informational root
@app.get("/")
async def root_index():
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.PROJECT_VERSION,
        "routers": ["widgets", "sport", "news", "twitter", "reddit"],
        "api_base": settings.API_V1_STR,
        "docs": "/api/docs",
        "openapi": "/api/openapi.json",
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