from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Tuple

import httpx

from app.core.config import settings


DEFAULT_ENDPOINT = "https://newsapi.org/v2/everything"


class NewsApiError(Exception):
    """Base exception for News API errors."""


class NewsApiConfigError(NewsApiError):
    """Raised when the News API key is missing or not configured."""


def _normalized_key() -> str:
    return (settings.NEWS_API_KEY or "").strip()


def _sanitize_endpoint(raw: str | None) -> str:
    endpoint = (raw or "").strip()
    if not endpoint:
        return DEFAULT_ENDPOINT
    return endpoint


def is_configured() -> bool:
    key = _normalized_key()
    if not key:
        return False
    return key.upper() != "YOUR_NEWS_API_KEY"


async def search_news(
    query: str,
    *,
    page_size: int = 20,
    language: str = "en",
    sort_by: str = "publishedAt",
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Query the configured News API endpoint and return normalized items plus metadata.

    Defaults align with the public interface of https://newsapi.org. Consumers can override
    the endpoint via configuration to point at another provider that supports similar
    `q`/`language`/`pageSize` semantics.
    """

    api_key = _normalized_key()
    if not api_key:
        raise NewsApiConfigError("News API key not configured")

    endpoint = _sanitize_endpoint(settings.NEWS_API_ENDPOINT)
    headers = {"X-Api-Key": api_key}
    params: Dict[str, Any] = {
        "q": query,
        "language": language,
        "pageSize": page_size,
        "sortBy": sort_by,
    }

    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            response = await client.get(endpoint, headers=headers, params=params)
            response.raise_for_status()
            payload = response.json()
    except httpx.HTTPStatusError as exc:
        raise NewsApiError(f"News API returned {exc.response.status_code}") from exc
    except httpx.HTTPError as exc:
        raise NewsApiError("Failed to reach News API endpoint") from exc
    except ValueError as exc:
        raise NewsApiError("Failed to decode News API response") from exc

    items = _normalize_items(payload)
    metadata = {
        "provider": "news-api",
        "endpoint": endpoint,
        "query": query,
        "language": language,
        "sort_by": sort_by,
        "requested": page_size,
        "received": len(items),
    }
    return items, metadata


def _normalize_items(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    raw_items: List[Dict[str, Any]] = []
    if isinstance(payload, dict):
        if isinstance(payload.get("articles"), list):
            raw_items = payload["articles"]  # NewsAPI.org format
        elif isinstance(payload.get("data"), list):
            raw_items = payload["data"]  # generic fallback structure

    normalized: List[Dict[str, Any]] = []
    for item in raw_items:
        if not isinstance(item, dict):
            continue
        title = item.get("title") or item.get("name") or ""
        link = item.get("url") or item.get("link") or ""
        description = item.get("description") or item.get("summary") or ""
        published = item.get("publishedAt") or item.get("publish_date") or item.get("date") or ""
        pub_ts = _parse_timestamp(published)
        source_obj = item.get("source")
        if isinstance(source_obj, dict):
            source = source_obj.get("name") or source_obj.get("title") or ""
        else:
            source = str(source_obj) if source_obj else ""
        image_url = item.get("urlToImage") or item.get("image_url") or item.get("image")

        normalized.append(
            {
                "title": title,
                "link": link,
                "description": description,
                "pub_date": published,
                "source": source,
                "pub_ts": pub_ts,
                "image_url": image_url,
            }
        )

    return normalized


def _parse_timestamp(value: str | None) -> int | None:
    if not value:
        return None
    try:
        cleaned = value.replace("Z", "+00:00") if value.endswith("Z") else value
        dt = datetime.fromisoformat(cleaned)
        return int(dt.timestamp())
    except (ValueError, TypeError):
        return None


