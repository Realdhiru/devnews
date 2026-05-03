import time
from typing import Any, Optional

class TTLCache:
    def __init__(self, ttl_seconds: int = 300):
        self._store = {}
        self._ttl = ttl_seconds

    def get(self, key: str) -> Optional[Any]:
        if key in self._store:
            value, expires = self._store[key]
            if time.time() < expires:
                return value
            del self._store[key]
        return None

    def set(self, key: str, value: Any):
        self._store[key] = (value, time.time() + self._ttl)

    def clear_expired(self):
        now = time.time()
        self._store = {k: v for k, v in self._store.items() if v[1] > now}
