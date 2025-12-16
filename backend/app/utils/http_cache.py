import hashlib
import json
from typing import Any, Mapping


def build_cache_control(*, max_age: int, s_maxage: int | None = None, stale_while_revalidate: int | None = None, stale_if_error: int | None = None) -> str:
    parts: list[str] = ["public", f"max-age={int(max_age)}"]
    if s_maxage is not None:
        parts.append(f"s-maxage={int(s_maxage)}")
    if stale_while_revalidate is not None:
        parts.append(f"stale-while-revalidate={int(stale_while_revalidate)}")
    if stale_if_error is not None:
        parts.append(f"stale-if-error={int(stale_if_error)}")
    return ", ".join(parts)


def compute_etag(payload: Any) -> str:
    """Compute a stable strong ETag for JSON-like payloads."""
    dumped = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    digest = hashlib.sha256(dumped).hexdigest()[:16]
    return f'"{digest}"'


def if_none_match_matches(header_value: str | None, etag: str) -> bool:
    if not header_value:
        return False
    # Very small parser: handle exact match and comma-separated list
    candidates = [h.strip() for h in header_value.split(",") if h.strip()]
    return etag in candidates or "*" in candidates
