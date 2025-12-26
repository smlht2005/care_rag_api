"""
Redis 快取服務 stub
"""
import asyncio
import logging
from typing import Any, Optional

class CacheService:
    """Redis 快取 stub"""
    
    def __init__(self):
        self.store = {}
        self.logger = logging.getLogger("CacheService")

    async def get(self, key: str) -> Optional[Any]:
        """取得快取值"""
        value = self.store.get(key)
        if value:
            self.logger.debug(f"Cache hit: {key}")
        else:
            self.logger.debug(f"Cache miss: {key}")
        return value

    async def set(self, key: str, value: Any, ttl: int = 3600):
        """設定快取值"""
        self.store[key] = value
        self.logger.debug(f"Cache set: {key} (TTL: {ttl}s)")
        # 模擬 TTL
        asyncio.create_task(self._expire(key, ttl))

    async def _expire(self, key: str, ttl: int):
        """模擬 TTL 過期"""
        await asyncio.sleep(ttl)
        if key in self.store:
            self.store.pop(key, None)
            self.logger.debug(f"Cache expired: {key}")

    async def delete(self, key: str):
        """刪除快取值"""
        if key in self.store:
            self.store.pop(key, None)
            self.logger.debug(f"Cache deleted: {key}")
            return True
        return False

    async def exists(self, key: str) -> bool:
        """檢查鍵是否存在"""
        return key in self.store

    async def clear(self):
        """清空所有快取"""
        count = len(self.store)
        self.store.clear()
        self.logger.info(f"Cache cleared: {count} keys removed")
        return count


