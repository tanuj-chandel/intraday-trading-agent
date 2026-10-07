import time
import asyncio
from typing import Dict, Any, Optional, Callable, Awaitable
from app.core.logging import logger

class CachedItem:
    def __init__(self, value: Any, ttl_seconds: float):
        self.value = value
        self.expiry = time.time() + ttl_seconds

    def is_expired(self) -> bool:
        return time.time() > self.expiry

class DataCacheManager:
    """
    In-memory high performance TTL Cache with rate limit protection and exponential backoff retry.
    """
    _cache: Dict[str, CachedItem] = {}

    @classmethod
    def get(cls, key: str) -> Optional[Any]:
        item = cls._cache.get(key)
        if item and not item.is_expired():
            return item.value
        return None

    @classmethod
    def set(cls, key: str, value: Any, ttl_seconds: float = 3.0):
        cls._cache[key] = CachedItem(value, ttl_seconds)

    @classmethod
    def clear(cls):
        cls._cache.clear()

    @classmethod
    async def fetch_with_retry(
        cls,
        func: Callable[[], Awaitable[Any]],
        max_retries: int = 3,
        base_backoff_seconds: float = 0.2
    ) -> Any:
        attempt = 0
        while attempt < max_retries:
            try:
                return await func()
            except Exception as e:
                attempt += 1
                if attempt >= max_retries:
                    logger.error(f"Data fetch failed after {max_retries} attempts: {str(e)}")
                    raise e
                sleep_time = base_backoff_seconds * (2 ** (attempt - 1))
                logger.warning(f"Fetch attempt {attempt} failed ({str(e)}). Retrying in {sleep_time:.2f}s...")
                await asyncio.sleep(sleep_time)
