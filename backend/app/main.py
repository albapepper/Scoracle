from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
import logging
from contextlib import asynccontextmanager
import httpx

from app.routers import home, autocomplete, mentions, links, player, team
from app.core.config import settings
from app.db.registry import entity_registry

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    app.state.http_client = httpx.AsyncClient(timeout=15.0)
    await entity_registry.connect()
    try:
        # Optionally trigger initial ingestion if empty
        players_count = await entity_registry.count("NBA", "player")
        teams_count = await entity_registry.count("NBA", "team")
        if players_count == 0 or teams_count == 0:
            logger.info("Registry empty; starting initial NBA ingestion")
            await entity_registry.ingest_sport("NBA")
    except Exception as e:
        logger.error("Error during initial registry ingestion: %s", e)
    yield
    # Shutdown
    await app.state.http_client.aclose()
    await entity_registry.close()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.PROJECT_VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# Configure CORS
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
# IMPORTANT: Register specific/static path segments before very generic dynamic ones
# The mentions and links routers each define a very broad pattern '/{entity_type}/{entity_id}'
# which was previously capturing '/autocomplete/player' and returning 400.
app.include_router(home.router, prefix="/api/v1", tags=["home"])
app.include_router(autocomplete.router, prefix="/api/v1", tags=["autocomplete"])
app.include_router(mentions.router, prefix="/api/v1", tags=["mentions"])
app.include_router(links.router, prefix="/api/v1", tags=["links"])
app.include_router(player.router, prefix="/api/v1", tags=["player"])
app.include_router(team.router, prefix="/api/v1", tags=["team"])

# Maintenance / registry router
maintenance_router = APIRouter(prefix="/api/v1/registry", tags=["registry"])

@maintenance_router.post("/refresh/{sport}")
async def refresh_registry(sport: str):
    # Simple reingest (future: diff / incremental)
    await entity_registry.ingest_sport(sport)
    return {"status": "ok", "sport": sport.upper()}

@maintenance_router.get("/counts")
async def registry_counts():
    counts = {}
    for sport in ["NBA"]:  # extend when more sports added
        counts[sport] = {
            "players": await entity_registry.count(sport, "player"),
            "teams": await entity_registry.count(sport, "team"),
        }
    return counts

app.include_router(maintenance_router)

@app.get("/api/health")
def health_check():
    return {"status": "healthy"}