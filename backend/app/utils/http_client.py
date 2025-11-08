import httpx

def get_async_client(timeout: float = 15.0) -> httpx.AsyncClient:
    return httpx.AsyncClient(timeout=timeout)
