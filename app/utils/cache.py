import asyncio
from typing import Any
class InMemoryCache:
    def __init__(self):
        self._store = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str):
        async with self._lock:
            item = self._store.get(key)
            if not item:
                return None
            value, expires_at = item
            if expires_at and expires_at < asyncio.get_event_loop().time():
                del self._store[key]
                return None
            return value

    async def set(self, key: str, value: Any, ex: int | None = None):
        async with self._lock:
            expires_at = None
            if ex:
                expires_at = asyncio.get_event_loop().time() + ex
            self._store[key] = (value, expires_at)

    async def zadd(self, key, mapping: dict):
        # minimal: store list of timestamps
        async with self._lock:
            arr = self._store.get(key, ([], None))[0]
            for v in mapping.values():
                arr.append(v)
            self._store[key] = (arr, None)

    async def zremrangebyscore(self, key, min_score, max_score):
        async with self._lock:
            arr = self._store.get(key, ([], None))[0]
            arr = [x for x in arr if not (min_score <= x <= max_score)]
            self._store[key] = (arr, None)

    async def zcard(self, key):
        async with self._lock:
            arr = self._store.get(key, ([], None))[0]
            return len(arr)

    async def expire(self, key, seconds):
        return True

