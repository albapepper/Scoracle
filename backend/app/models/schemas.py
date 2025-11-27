from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class WidgetDiagnostics(BaseModel):
    provider: Optional[str] = None
    cache: Optional[str] = None  # 'hit' | 'miss'
    request_id: Optional[str] = None
    latency_ms: Optional[int] = None


class WidgetEnvelope(BaseModel):
    type: str  # 'player' | 'team' | etc.
    version: str = "1"
    cacheKey: str
    ttl: int
    generatedAt: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    etag: Optional[str] = None
    diagnostics: Optional[WidgetDiagnostics] = None
    payload: Dict[str, Any]