from fastapi import FastAPI, APIRouter, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from contextlib import asynccontextmanager
import httpx

from app.api import home, autocomplete, mentions, links, player, team, sport
from app.core.config import settings
from app.models.schemas import ErrorEnvelope

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup – keep it simple; no DB or background jobs
    app.state.http_client = httpx.AsyncClient(timeout=15.0)
    if not settings.API_SPORTS_KEY:
        logger.warning("API_SPORTS_KEY is not set – upstream API calls will fail until configured")
    yield
    # Shutdown
    await app.state.http_client.aclose()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.PROJECT_VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# When run via `python -m app.main` provide a helpful hint (Uvicorn should be used instead)
if __name__ == "__main__":
    import uvicorn, os
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)

# Configure CORS
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers (sport-first API plus thin legacy routes)
app.include_router(home.router, prefix="/api/v1", tags=["home"])
app.include_router(autocomplete.router, prefix="/api/v1", tags=["autocomplete"])
app.include_router(mentions.router, prefix="/api/v1", tags=["mentions"])
app.include_router(links.router, prefix="/api/v1", tags=["links"])
app.include_router(player.router, prefix="/api/v1/player", tags=["player"])
app.include_router(team.router, prefix="/api/v1/team", tags=["team"])
app.include_router(sport.router, prefix="/api/v1", tags=["sport"])

# Registry-related maintenance endpoints removed to keep server lean

@app.get("/api/health")
def health_check():
    logger.info("Health endpoint hit")
    return {"status": "healthy"}

@app.get("/")
async def root():
    """Simple root route so hitting / doesn't 404 and confuse the reloader/browser."""
    logger.info("Root endpoint hit")
    return {
        "message": "Scoracle API",
        "docs": "/api/docs",
        "openapi": "/api/openapi.json",
        "health": "/api/health"
    }

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    # Let HTTPExceptions pass through (FastAPI default will handle)
    from fastapi import HTTPException
    if isinstance(exc, HTTPException):
        # rely on existing behavior; we could still wrap if desired
        return JSONResponse(status_code=exc.status_code, content={
            "error": {
                "message": getattr(exc, 'detail', 'HTTP error'),
                "code": exc.status_code,
                "path": str(request.url)
            }
        })
    logger.exception("Unhandled server error")
    return JSONResponse(status_code=500, content=ErrorEnvelope(
        error={
            "message": "Internal server error",
            "code": 500,
            "path": str(request.url)
        }
    ).dict())