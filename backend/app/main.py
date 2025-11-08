"""Canonical FastAPI application entrypoint.

Mounts all routers and configures lifespan resources.
"""
from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.config import settings
from app.routers import widgets, sport, news, twitter, reddit

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting application lifespan")
    try:
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
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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