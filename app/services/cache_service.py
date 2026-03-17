import hashlib
import json
from typing import Any, Optional
import redis.asyncio as redis
from app.core.config import Settings


class CacheService:
    def __init__(self, settings: Settings) -> None:
        self._client = redis.from_url(settings.redis_url, decode_responses=True)

    def build_key(
        self,
        task_type: str,
        prompt_id: str,
        prompt_version: str,
        payload: dict[str, Any],
    ) -> str:
        raw = f"{task_type}:{prompt_id}:{prompt_version}:{json.dumps(payload, sort_keys=True)}"
        return "llm:cache:" + hashlib.sha256(raw.encode()).hexdigest()

    async def get(self, key: str) -> Optional[dict[str, Any]]:
        try:
            value = await self._client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception:
            return None

    async def set(self, key: str, value: dict[str, Any], ttl: int) -> None:
        try:
            await self._client.setex(key, ttl, json.dumps(value))
        except Exception:
            pass

    async def delete_by_pattern(self, pattern: str) -> int:
        try:
            keys = await self._client.keys(f"llm:cache:{pattern}*")
            if keys:
                return await self._client.delete(*keys)
            return 0
        except Exception:
            return 0

    async def ping(self) -> bool:
        try:
            await self._client.ping()
            return True
        except Exception:
            return False
