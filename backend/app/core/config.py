import os
from typing import List, Union
from pydantic import AnyHttpUrl, validator
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Scoracle"
    PROJECT_DESCRIPTION: str = "A one-stop shop for sports news and statistics"
    PROJECT_VERSION: str = "0.1.0"
    
    API_V1_STR: str = "/api/v1"
    
    # CORS Configuration
    BACKEND_CORS_ORIGINS: List[Union[str, AnyHttpUrl]] = ["http://localhost:3000", "http://localhost:8000"]

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # API Keys
    BALLDONTLIE_API_KEY: str = os.getenv("BALLDONTLIE_API_KEY", "fd8788ca-65fe-4ea6-896f-a2c9776977d1")
    # API-Sports.com key (required for new provider)
    API_SPORTS_KEY: str = os.getenv("API_SPORTS_KEY", "")
    # Registry DB path relative to project root (NOT inside backend/ so file writes don't trigger reloads)
    REGISTRY_DB_PATH: str = os.getenv("REGISTRY_DB_PATH", "instance/registry.db")
    # Debug flag to enable verbose upstream payload logging / diagnostic endpoints
    BALLDONTLIE_DEBUG: bool = bool(int(os.getenv("BALDONTLIE_DEBUG", "0")))
    # Default seasons/leagues for API-Sports where applicable
    API_SPORTS_DEFAULTS: dict = {
        # Football (soccer) – English Premier League league id 39, current season autodetected if empty
        "EPL": {"sport": "football", "league": 39, "season": os.getenv("API_SPORTS_EPL_SEASON", "")},
        # Basketball – NBA: sport=basketball; note API-Sports requires league ids by endpoint; placeholder values
        "NBA": {"sport": "basketball", "league": int(os.getenv("API_SPORTS_NBA_LEAGUE", "12")), "season": os.getenv("API_SPORTS_NBA_SEASON", "")},
        # American Football – NFL
        "NFL": {"sport": "american-football", "league": int(os.getenv("API_SPORTS_NFL_LEAGUE", "1")), "season": os.getenv("API_SPORTS_NFL_SEASON", "")},
    }
    
    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()