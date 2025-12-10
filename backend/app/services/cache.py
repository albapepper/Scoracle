import time
from typing import Any, Optional, Dict, Tuple
from collections import OrderedDict

class TTLCache:
    """Very small in-process TTL cache (sufficient for low-QPS prototype).
    Not thread-safe beyond standard CPython GIL assumptions. Keys are simple strings.
    Uses LRU eviction for better performance than sorting on every set.
    """
    def __init__(self, default_ttl: int = 60, max_items: int = 500):
        # Use OrderedDict for efficient LRU tracking
        self._store: OrderedDict[str, Tuple[float, Any]] = OrderedDict()
        self._default_ttl = default_ttl
        self._max_items = max_items

    def _evict_if_needed(self):
        if len(self._store) <= self._max_items:
            return
        # Evict expired entries first
        now = time.time()
        expired_keys = [k for k, (exp, _) in self._store.items() if exp < now]
        for k in expired_keys:
            self._store.pop(k, None)
        
        # If still over limit, evict oldest accessed items (LRU)
        while len(self._store) > self._max_items:
            self._store.popitem(last=False)  # Remove oldest item

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        expires = time.time() + (ttl if ttl is not None else self._default_ttl)
        # Remove if exists to update position in OrderedDict
        self._store.pop(key, None)
        self._store[key] = (expires, value)
        self._evict_if_needed()

    def get(self, key: str) -> Optional[Any]:
        entry = self._store.get(key)
        if not entry:
            return None
        expires, value = entry
        if expires < time.time():
            self._store.pop(key, None)
            return None
        # Move to end (mark as recently used)
        self._store.move_to_end(key)
        return value

    def purge(self):
        now = time.time()
        stale = [k for k, (exp, _) in self._store.items() if exp < now]
        for k in stale:
            self._store.pop(k, None)

# Singleton instances for different data classes
basic_cache = TTLCache(default_ttl=120, max_items=1000)
stats_cache = TTLCache(default_ttl=300, max_items=500)
# Dedicated cache for widget or profile blobs that can be larger and tolerate longer TTL
widget_cache = TTLCache(default_ttl=900, max_items=300)
# Removed percentile_cache after deprecating percentile feature
