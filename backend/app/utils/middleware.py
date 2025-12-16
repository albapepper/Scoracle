import time
import uuid
from typing import Callable, Awaitable, Dict, Tuple

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    header_name = "X-Correlation-ID"

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        incoming = request.headers.get(self.header_name)
        cid = incoming or uuid.uuid4().hex
        request.state.correlation_id = cid
        response = await call_next(request)
        response.headers[self.header_name] = cid
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory token bucket per client IP.

    Configure via app.state.rate_limit: (enabled: bool, rps: float, burst: int)
    """

    def __init__(self, app):
        super().__init__(app)
        self.buckets: Dict[str, Tuple[float, float]] = {}  # ip -> (tokens, last_ts)

    def _allow(self, key: str, rps: float, burst: int) -> bool:
        now = time.monotonic()
        tokens, last = self.buckets.get(key, (float(burst), now))
        # refill
        tokens = min(float(burst), tokens + (now - last) * rps)
        if tokens >= 1.0:
            tokens -= 1.0
            self.buckets[key] = (tokens, now)
            return True
        else:
            self.buckets[key] = (tokens, now)
            return False

    @staticmethod
    def _client_ip(request: Request) -> str:
        """Best-effort client IP extraction.

        In production this app is commonly behind proxies/CDNs.
        We prefer the first IP in X-Forwarded-For when present.
        """
        xff = request.headers.get("x-forwarded-for")
        if xff:
            # XFF can be a comma-separated list: "client, proxy1, proxy2"
            first = xff.split(",")[0].strip()
            if first:
                return first
        xri = request.headers.get("x-real-ip")
        if xri:
            return xri.strip()
        return request.client.host if request.client else "unknown"

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        cfg = getattr(request.app.state, "rate_limit", None)
        if not cfg:
            return await call_next(request)
        enabled, rps, burst = cfg
        if not enabled:
            return await call_next(request)
        ip = self._client_ip(request)
        if self._allow(ip, float(rps), int(burst)):
            return await call_next(request)
        # 429 Too Many Requests
        from fastapi.responses import JSONResponse
        from app.utils.errors import build_error_payload, ErrorCode
        cid = getattr(request.state, "correlation_id", None)
        payload = build_error_payload("Too many requests", 429, correlation_id=cid, code=ErrorCode.RATE_LIMITED)
        resp = JSONResponse(payload, status_code=429)
        resp.headers["Retry-After"] = "1"
        return resp
