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
    
    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()