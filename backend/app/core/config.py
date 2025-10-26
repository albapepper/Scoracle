import os
from typing import List, Union
from pydantic import AnyHttpUrl, validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Pydantic v2 settings config
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",  # ignore unrelated env vars like PYTHONPATH, legacy keys
    )
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
    
    # API-Sports.com key (required provider)
    API_SPORTS_KEY: str = os.getenv("API_SPORTS_KEY", "")
    # Registry removed: local autocomplete uses per-sport localdb files.
    REGISTRY_DB_PATH: str = os.getenv("REGISTRY_DB_PATH", "instance/registry.db")  # deprecated
    # Default seasons/leagues for API-Sports where applicable
    API_SPORTS_DEFAULTS: dict = {
        # Football (soccer) – now "FOOTBALL" umbrella; EPL legacy alias retained in code paths
        # Default league for football lookups can be any of Top 5 + MLS; we keep EPL (39) for identity fallbacks.
    # Default seasons set to latest requested: Football/NFL 2025-26 => 2025; NBA 2024-25 => 2024
    "FOOTBALL": {"sport": "football", "league": int(os.getenv("API_SPORTS_FOOTBALL_LEAGUE", "39")), "season": os.getenv("API_SPORTS_FOOTBALL_SEASON", "2025")},
    "EPL": {"sport": "football", "league": 39, "season": os.getenv("API_SPORTS_EPL_SEASON", "2025")},
        # Basketball – NBA
    "NBA": {"sport": "basketball", "league": os.getenv("API_SPORTS_NBA_LEAGUE", "standard"), "season": os.getenv("API_SPORTS_NBA_SEASON", "2024")},
        # American Football – NFL
    "NFL": {"sport": "american-football", "league": int(os.getenv("API_SPORTS_NFL_LEAGUE", "1")), "season": os.getenv("API_SPORTS_NFL_SEASON", "2025")},
    }
    # Lean mode: avoid upstream provider calls; serve only local DB + RSS
    LEAN_BACKEND: bool = os.getenv("LEAN_BACKEND", "false").lower() in ("1", "true", "yes")
    
    # Note: Pydantic v2 forbids using both model_config and Config; we only keep model_config above.

settings = Settings()