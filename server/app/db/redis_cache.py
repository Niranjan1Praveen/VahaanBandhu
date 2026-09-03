"""Redis cache. Optional by design.

Redis improves latency and coordinates ephemeral state. It is **never** the
source of truth, and every operation degrades to a miss when Redis is
unavailable -- a Redis outage must slow the application down, not break it.

**Version-aware cache keys.** A routing result is only valid for the exact
optimization model that produced it. Keys therefore incorporate
``vbqer_version``, ``graph_version`` and ``cost_snapshot_id``, so bumping any of
them makes previously cached results unreachable rather than silently stale.
Serving an old route after the optimizer changed is worse than a cache miss.
"""

from __future__ import annotations

import hashlib
import json
import logging

import redis.asyncio as aioredis

from server.app.core.config import get_settings

log = logging.getLogger(__name__)


class RedisCache:
    def __init__(self) -> None:
        self.client: aioredis.Redis | None = None
        self.available = False

    async def connect(self) -> None:
        s = get_settings()
        if not s.redis_enabled:
            log.info("redis disabled by configuration")
            return
        try:
            self.client = aioredis.from_url(
                s.redis_url, encoding="utf-8", decode_responses=True,
                socket_connect_timeout=3, socket_timeout=3)
            await self.client.ping()
            self.available = True
            log.info("redis connected")
        except Exception as e:
            # Not fatal. The application runs without a cache.
            self.available = False
            log.warning("redis unavailable, continuing without cache: %s", e)

    async def disconnect(self) -> None:
        if self.client:
            await self.client.aclose()
            self.client = None
            self.available = False

    async def healthy(self) -> bool:
        if not self.client:
            return False
        try:
            await self.client.ping()
            return True
        except Exception:
            self.available = False
            return False

    async def get_json(self, key: str):
        if not self.available or not self.client:
            return None
        try:
            raw = await self.client.get(key)
            return json.loads(raw) if raw else None
        except Exception as e:
            log.warning("redis get failed (%s); treating as miss", e)
            self.available = False
            return None

    async def set_json(self, key: str, value, ttl_s: int | None = None) -> bool:
        if not self.available or not self.client:
            return False
        try:
            await self.client.set(key, json.dumps(value, default=str), ex=ttl_s)
            return True
        except Exception as e:
            log.warning("redis set failed (%s); continuing", e)
            self.available = False
            return False

    async def delete(self, *keys: str) -> int:
        if not self.available or not self.client or not keys:
            return 0
        try:
            return int(await self.client.delete(*keys))
        except Exception:
            return 0

    async def incr_with_ttl(self, key: str, ttl_s: int) -> int:
        """Counter used for simple rate limiting. Returns 0 when unavailable,
        which callers treat as 'do not rate limit' rather than 'block'."""
        if not self.available or not self.client:
            return 0
        try:
            n = await self.client.incr(key)
            if n == 1:
                await self.client.expire(key, ttl_s)
            return int(n)
        except Exception:
            return 0


cache = RedisCache()


def route_cache_key(
    *, origin_id: str, destination_id: str, stops: list[str] | None,
    vehicle_capacity_kg: float, vbqer_version: str, graph_version: str,
    cost_snapshot_id: str, profile: str,
) -> str:
    """Version-aware routing cache key.

    Every component that could change the answer is in the key. If the optimizer
    version, graph or cost snapshot moves, old entries become unreachable by
    construction -- no manual invalidation step to forget.
    """
    payload = {
        "o": origin_id, "d": destination_id,
        "stops": sorted(stops or []),
        "cap": round(float(vehicle_capacity_kg), 1),
        "vbqer": vbqer_version, "graph": graph_version,
        "snapshot": cost_snapshot_id, "profile": profile,
    }
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True).encode()).hexdigest()[:24]
    return f"route:v1:{vbqer_version}:{digest}"
