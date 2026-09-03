"""Health and readiness. Reports degradation truthfully, exposes no secrets."""

from __future__ import annotations

import time

from fastapi import APIRouter

from server.app.core.config import get_settings
from server.app.db.mongodb import mongo
from server.app.db.redis_cache import cache

router = APIRouter()
_STARTED = time.time()


@router.get("/health")
async def health() -> dict:
    """Component-level health.

    Reports booleans about *configuration* and *reachability* only -- never a key,
    URI or token. `status` is `ok` when persistence is available, `degraded`
    when it is not, because the API can still serve reference data and honest
    errors without Mongo.
    """
    s = get_settings()
    mongo_ok = await mongo.healthy()
    redis_ok = await cache.healthy()

    return {
        "status": "ok" if mongo_ok else "degraded",
        "app": s.app_name,
        "version": "2.0.0",
        "environment": s.environment,
        "uptime_s": round(time.time() - _STARTED, 1),
        "components": {
            "mongodb": {"connected": mongo_ok, "required": True},
            # Redis is a performance component; its absence is not an outage.
            "redis": {"connected": redis_ok, "required": False,
                      "enabled": s.redis_enabled},
            "clerk": {"configured": s.clerk_configured, "required": False},
            "tomtom": {"configured": s.tomtom_configured, "required": False},
        },
        "auth": {
            "clerk_configured": s.clerk_configured,
            "dev_auth_active": s.demo_auth_active,
        },
        "routing": {
            "engine": "VB-QER",
            "profile": s.vbqer_profile,
            # Load-bearing guarantee: no QPU call in the request path.
            "live_quantum_hardware_call": False,
            "ibm_quantum_offline_only": s.ibm_quantum_offline_only,
        },
    }


@router.get("/health/live")
async def liveness() -> dict:
    return {"alive": True}


@router.get("/health/ready")
async def readiness() -> dict:
    """Ready only when persistence is reachable, for container orchestration."""
    ok = await mongo.healthy()
    return {"ready": ok, "mongodb": ok}
