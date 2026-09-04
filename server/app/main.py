"""VahaanBandhu FastAPI application.

Startup is deliberately tolerant: MongoDB or Redis being unavailable degrades
the service rather than preventing it from booting. A half-up API that reports
its own degradation through `/health` is far more useful during development —
and more honest in production — than a process that refuses to start.

There is **no IBM Quantum import anywhere in this module's graph**. A queued or
failed QPU job cannot affect availability.
"""

from __future__ import annotations

import logging
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from server.app.api.routes import (
    dealers, farmers, health, live_routing, locations, me, routing, truckers,
)
from server.app.core.config import get_settings
from server.app.core.logging import configure_logging
from server.app.db.mongodb import ensure_indexes, mongo
from server.app.db.redis_cache import cache

log = logging.getLogger("vahaanbandhu")
settings = get_settings()


def create_app() -> FastAPI:
    configure_logging(settings.log_level)
    app = FastAPI(
        title=settings.app_name,
        version="2.0.0",
        description=(
            "VahaanBandhu rural circular-logistics API. All route optimization "
            "goes through VB-QER; no live quantum hardware is in the request path."
        ),
        docs_url="/docs",
        openapi_url=f"{settings.api_v1_prefix}/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def request_context(request: Request, call_next):
        rid = uuid.uuid4().hex[:12]
        t0 = time.perf_counter()
        request.state.request_id = rid
        try:
            response = await call_next(request)
        except Exception:
            log.exception("unhandled error", extra={
                "request_id": rid, "path": request.url.path})
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error.", "request_id": rid})
        dur = (time.perf_counter() - t0) * 1000
        response.headers["x-request-id"] = rid
        log.info("request", extra={
            "request_id": rid, "path": request.url.path,
            "status_code": response.status_code, "duration_ms": round(dur, 2)})
        return response

    @app.on_event("startup")
    async def _startup() -> None:
        try:
            await mongo.connect()
            idx = await ensure_indexes()
            log.info("indexes ensured on %d collections", len(idx))
        except Exception as e:
            # Degrade, do not crash. /health reports the truth.
            log.error("MongoDB unavailable at startup: %s", e)
        await cache.connect()
        log.info("startup complete: env=%s clerk=%s tomtom=%s dev_auth=%s",
                 settings.environment, settings.clerk_configured,
                 settings.tomtom_configured, settings.demo_auth_active)

    @app.on_event("shutdown")
    async def _shutdown() -> None:
        await mongo.disconnect()
        await cache.disconnect()

    p = settings.api_v1_prefix
    app.include_router(health.router, prefix=p, tags=["health"])
    app.include_router(me.router, prefix=p, tags=["identity"])
    app.include_router(farmers.router, prefix=f"{p}/farmers", tags=["farmer"])
    app.include_router(truckers.router, prefix=f"{p}/truckers", tags=["trucker"])
    app.include_router(dealers.router, prefix=f"{p}/dealers", tags=["dealer"])
    app.include_router(routing.router, prefix=f"{p}/routes", tags=["routing"])
    app.include_router(live_routing.router, prefix=f"{p}/routes", tags=["routing"])
    app.include_router(locations.router, prefix=p, tags=["locations"])
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server.app.main:app", host="0.0.0.0", port=8000, reload=True)
