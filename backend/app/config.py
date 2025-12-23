from typing import List, Union

from pydantic import AnyHttpUrl, field_validator, computed_field
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
	# For preview deployments where origins vary, you can set BACKEND_CORS_ORIGIN_REGEX
	# e.g., "^https://.*\\.vercel\\.app$"
	BACKEND_CORS_ORIGIN_REGEX: str | None = None
	# Emergency escape hatch. Prefer explicit origins/regex.
	BACKEND_CORS_ALLOW_ALL: bool = False
	BACKEND_CORS_ORIGINS: List[Union[str, AnyHttpUrl]] = [
		"http://localhost:3000",
		"http://localhost:4321",  # Astro dev server
		"http://localhost:4322",  # Astro dev server (fallback port)
		"http://localhost:8000",
		"http://localhost:5173",
	]

	@field_validator("BACKEND_CORS_ORIGINS", mode="before")
	@classmethod
	def assemble_cors_origins(cls, v: Union[str, List[str]]):
		# Default origins for development
		defaults = [
			"http://localhost:3000",
			"http://localhost:4321",  # Astro dev server
			"http://localhost:4322",  # Astro dev server (fallback port)
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
	API_SPORTS_KEY: str = ""
	# API-Sports defaults (override via env)
	API_SPORTS_FOOTBALL_LEAGUE: int = 39
	API_SPORTS_FOOTBALL_SEASON: str = "2025"
	API_SPORTS_NBA_LEAGUE: str = "standard"
	API_SPORTS_NBA_SEASON: str = "2025"
	API_SPORTS_NFL_LEAGUE: int = 1
	API_SPORTS_NFL_SEASON: str = "2025"

	@computed_field
	@property
	def API_SPORTS_DEFAULTS(self) -> dict:
		# Football (soccer) - season is the year the season STARTED (2024-25 season = "2024")
		# NBA/NFL - using 2025 for current season
		return {
			"FOOTBALL": {
				"sport": "football",
				"league": int(self.API_SPORTS_FOOTBALL_LEAGUE),
				"season": str(self.API_SPORTS_FOOTBALL_SEASON),
			},
			"NBA": {
				"sport": "basketball",
				"league": str(self.API_SPORTS_NBA_LEAGUE),
				"season": str(self.API_SPORTS_NBA_SEASON),
			},
			"NFL": {
				"sport": "american-football",
				"league": int(self.API_SPORTS_NFL_LEAGUE),
				"season": str(self.API_SPORTS_NFL_SEASON),
			},
		}

	# Rate limiting (simple in-memory token bucket)
	RATE_LIMIT_ENABLED: bool = False
	RATE_LIMIT_RPS: float = 5.0  # tokens per second
	RATE_LIMIT_BURST: int = 10


settings = Settings()
