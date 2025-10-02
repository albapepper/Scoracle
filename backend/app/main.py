from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.routers import home, mentions, links, player, team, autocomplete

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.PROJECT_VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
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

@app.get("/api/health")
def health_check():
    return {"status": "healthy"}