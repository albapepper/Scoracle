from enum import Enum
from typing import Any, Dict


class ErrorCode(str, Enum):
    BAD_REQUEST = "BAD_REQUEST"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    NOT_FOUND = "NOT_FOUND"
    RATE_LIMITED = "RATE_LIMITED"
    UPSTREAM_ERROR = "UPSTREAM_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"


def map_status_to_code(status_code: int) -> ErrorCode:
    if status_code == 400:
        return ErrorCode.BAD_REQUEST
    if status_code == 401:
        return ErrorCode.UNAUTHORIZED
    if status_code == 403:
        return ErrorCode.FORBIDDEN
    if status_code == 404:
        return ErrorCode.NOT_FOUND
    if status_code == 429:
        return ErrorCode.RATE_LIMITED
    if 500 <= status_code < 600:
        return ErrorCode.INTERNAL_ERROR
    return ErrorCode.INTERNAL_ERROR


def build_error_payload(message: str, status: int, correlation_id: str | None = None, code: ErrorCode | None = None, extra: Dict[str, Any] | None = None) -> Dict[str, Any]:
    return {
        "error": {
            "code": (code or map_status_to_code(status)).value,
            "message": message,
            "status": status,
            "correlationId": correlation_id,
            **(extra or {}),
        }
    }
