import asyncio
from collections.abc import Awaitable, Callable
from typing import Any


class SingleFlight:
    """Coalesce concurrent requests for the same key.

    If multiple coroutines request the same key concurrently, only one executes
    the work function; the rest await its result.
    """

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._inflight: dict[str, asyncio.Future] = {}

    async def do(self, key: str, work: Callable[[], Awaitable[Any]]) -> Any:
        async with self._lock:
            fut = self._inflight.get(key)
            if fut is None:
                fut = asyncio.get_event_loop().create_future()
                self._inflight[key] = fut
                leader = True
            else:
                leader = False

        if not leader:
            return await fut

        try:
            result = await work()
            fut.set_result(result)
            return result
        except Exception as exc:
            fut.set_exception(exc)
            raise
        finally:
            async with self._lock:
                self._inflight.pop(key, None)


singleflight = SingleFlight()
