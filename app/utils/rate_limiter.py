import time
from app.config import settings

class RateLimiter:
    def __init__(self, cache):
        self.cache = cache
        self.limit = int(settings.RATE_LIMIT)
        self.window = int(settings.RATE_LIMIT_WINDOW)

    async def is_allowed(self, key: str) -> bool:
        now = int(time.time())
        window_start = now - self.window
        zkey = f"rl:{key}"
        
        try:
            await self.cache.zremrangebyscore(zkey, 0, window_start)
            current = await self.cache.zcard(zkey)
        except AttributeError:
            
            cur = await self.cache.get(zkey) or []
            cur = [t for t in cur if t >= window_start]
            current = len(cur)
            if current >= self.limit:
                return False
            cur.append(now)
            await self.cache.set(zkey, cur, ex=self.window+1)
            return True

        if current >= self.limit:
            return False
        await self.cache.zadd(zkey, {str(now): now})
        await self.cache.expire(zkey, self.window + 1)
        return True
