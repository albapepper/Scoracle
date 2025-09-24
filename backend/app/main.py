from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.routers import home, mentions, links, player, team

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
app.include_router(home.router, prefix="/api/v1", tags=["home"])
app.include_router(mentions.router, prefix="/api/v1", tags=["mentions"])
app.include_router(links.router, prefix="/api/v1", tags=["links"])
app.include_router(player.router, prefix="/api/v1", tags=["player"])
app.include_router(team.router, prefix="/api/v1", tags=["team"])

@app.get("/api/health")
def health_check():
    return {"status": "healthy"}