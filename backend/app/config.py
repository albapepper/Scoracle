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
	# Set BACKEND_CORS_ORIGINS env var as comma-separated URLs for production
	# e.g., "https://scoracle.vercel.app,https://your-domain.com"
	BACKEND_CORS_ORIGINS: List[Union[str, AnyHttpUrl]] = [
		"http://localhost:3000",
		"http://localhost:8000",
		"http://localhost:5173",
	]

	@validator("BACKEND_CORS_ORIGINS", pre=True)
	def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
		# Default origins for development
		defaults = [
			"http://localhost:3000",
			"http://localhost:8000",
			"http://localhost:5173",
		]
		if isinstance(v, str) and not v.startswith("["):
			# Parse comma-separated string from env var
			parsed = [i.strip() for i in v.split(",") if i.strip()]
			# Merge with defaults, avoiding duplicates
			return list(dict.fromkeys(defaults + parsed))
		elif isinstance(v, list):
			return list(dict.fromkeys(defaults + v))
		return defaults

	# API-Sports.com key (required provider)
	API_SPORTS_KEY: str = os.getenv("API_SPORTS_KEY", "")
	# Default seasons/leagues for API-Sports where applicable
	API_SPORTS_DEFAULTS: dict = {
		# Football (soccer)
		"FOOTBALL": {
			"sport": "football",
			"league": int(os.getenv("API_SPORTS_FOOTBALL_LEAGUE", "39")),
			"season": os.getenv("API_SPORTS_FOOTBALL_SEASON", "2025"),
		},
		# Basketball – NBA
		"NBA": {
			"sport": "basketball",
			"league": os.getenv("API_SPORTS_NBA_LEAGUE", "standard"),
			"season": os.getenv("API_SPORTS_NBA_SEASON", "2024"),
		},
		# American Football – NFL
		"NFL": {
			"sport": "american-football",
			"league": int(os.getenv("API_SPORTS_NFL_LEAGUE", "1")),
			"season": os.getenv("API_SPORTS_NFL_SEASON", "2025"),
		},
	}
	# Rate limiting (simple in-memory token bucket)
	RATE_LIMIT_ENABLED: bool = os.getenv("RATE_LIMIT_ENABLED", "false").lower() in ("1", "true", "yes")
	RATE_LIMIT_RPS: float = float(os.getenv("RATE_LIMIT_RPS", "5"))  # tokens per second
	RATE_LIMIT_BURST: int = int(os.getenv("RATE_LIMIT_BURST", "10"))


settings = Settings()
