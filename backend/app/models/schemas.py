from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class PlayerBase(BaseModel):
    id: str
    first_name: str
    last_name: str
    position: Optional[str] = None
    height: Optional[str] = None
    weight: Optional[str] = None
    jersey_number: Optional[str] = None

class TeamBase(BaseModel):
    id: str
    name: str
    abbreviation: str
    city: Optional[str] = None
    conference: Optional[str] = None
    division: Optional[str] = None
    logo_url: Optional[str] = None

class PlayerWithTeam(PlayerBase):
    team: TeamBase

class PlayerStats(BaseModel):
    games_played: int = Field(..., alias="games_played")
    season: str
    minutes_per_game: float = Field(..., alias="min")
    points_per_game: float = Field(..., alias="pts")
    assists_per_game: float = Field(..., alias="ast")
    rebounds_per_game: float = Field(..., alias="reb")
    steals_per_game: float = Field(..., alias="stl")
    blocks_per_game: float = Field(..., alias="blk")
    field_goal_percentage: float = Field(..., alias="fg_pct")
    three_point_percentage: float = Field(..., alias="fg3_pct")
    free_throw_percentage: float = Field(..., alias="ft_pct")
    turnovers_per_game: float = Field(..., alias="turnover")
    
    class Config:
        allow_population_by_field_name = True

class TeamStats(BaseModel):
    games_played: int
    season: str
    wins: int
    losses: int
    points_per_game: float
    assists_per_game: float
    rebounds_per_game: float
    steals_per_game: float
    blocks_per_game: float
    field_goal_percentage: float
    three_point_percentage: float
    free_throw_percentage: float
    turnovers_per_game: float

class PlayerDetail(BaseModel):
    player: PlayerWithTeam
    stats: Optional[PlayerStats] = None

class TeamDetail(BaseModel):
    team: TeamBase
    stats: Optional[TeamStats] = None
    roster: Optional[List[PlayerBase]] = None

class NewsItem(BaseModel):
    title: str
    link: str
    description: str
    pub_date: str
    source: str

class SearchResult(BaseModel):
    entity_type: str
    id: str
    name: str
    sport: str
    additional_info: Dict[str, Any] = {}

class SearchResponse(BaseModel):
    query: str
    entity_type: str
    sport: str
    results: List[SearchResult]

class MentionsResponse(BaseModel):
    entity_type: str
    entity_id: str
    sport: str
    entity_info: Optional[Dict[str, Any]] = None
    mentions: List[NewsItem]
    missing_entity: bool = False

# --- Unified / Normalized Schemas (new) ---

class PlayerSummary(BaseModel):
    id: str
    sport: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    position: Optional[str] = None
    team_id: Optional[str] = None
    team_name: Optional[str] = None
    team_abbreviation: Optional[str] = None

class TeamSummary(BaseModel):
    id: str
    sport: str
    name: Optional[str] = None
    abbreviation: Optional[str] = None
    city: Optional[str] = None
    conference: Optional[str] = None
    division: Optional[str] = None

class PlayerFullResponse(BaseModel):
    summary: PlayerSummary
    season: Optional[str] = None
    stats: Optional[Dict[str, Any]] = None
    percentiles: Optional[Dict[str, Any]] = None
    mentions: Optional[List[NewsItem]] = None

class TeamFullResponse(BaseModel):
    summary: TeamSummary
    season: Optional[str] = None
    stats: Optional[Dict[str, Any]] = None
    percentiles: Optional[Dict[str, Any]] = None
    mentions: Optional[List[NewsItem]] = None

class ErrorEnvelope(BaseModel):
    error: Dict[str, Any]