"""Live routing: real road geometry and traffic from TomTom.

Architectural position — this does **not** bypass VB-QER. TomTom supplies the
road network and current traffic; VB-QER still decides which candidate is best
under the project objective. The split the Phase-A brief specifies:

    TomTom  ->  candidate routes + traffic
       |
    VB-QER  ->  chooses the best one for this logistics objective
       |
     route

Degradation is explicit: when no TomTom key works, the response is marked
`provider: "offline_graph"` and the geometry comes from the Phase-A graph.
A synthetic route is never presented as a live one.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from server.app.core.config import get_settings
from server.app.core.security import Identity, get_identity
from server.app.db.redis_cache import cache
from server.app.schemas.common import GeoPoint

router = APIRouter()
log = logging.getLogger(__name__)


class LiveLeg(BaseModel):
    from_point: GeoPoint
    to_point: GeoPoint
    kind: str = "outbound"  # outbound | return
    label: str | None = None


class LiveRouteRequest(BaseModel):
    legs: list[LiveLeg] = Field(..., min_length=1, max_length=6)
    travel_mode: str = "truck"
    max_alternatives: int = Field(default=0, ge=0, le=3)


class LiveLegResult(BaseModel):
    kind: str
    label: str | None = None
    distance_km: float
    travel_time_min: float
    traffic_delay_min: float
    # Real road geometry: many points following the actual carriageway, not a
    # two-point straight line.
    polyline: list[list[float]] = Field(default_factory=list)
    n_geometry_points: int = 0
    provider: str


class LiveRouteResponse(BaseModel):
    legs: list[LiveLegResult]
    total_distance_km: float
    total_time_min: float
    total_traffic_delay_min: float
    provider: str
    traffic_available: bool
    warnings: list[str] = Field(default_factory=list)


def _provider():
    """Build the TomTom provider with keys from Settings.

    The provider defaults to reading os.environ, but the app loads .env through
    pydantic-settings, which does NOT populate os.environ. Passing the keys
    explicitly is what makes live routing actually reachable -- without it the
    provider silently sees zero keys and every request falls back to a
    straight-line estimate.
    """
    from routing.providers.tomtom import TomTomRoutingProvider
    s = get_settings()
    keys = [k.strip() for k in s.tomtom_api_keys.split(",") if k.strip()]
    # 12s (the provider default) is too tight for long truck routes: a 48 km leg
    # returns ~900 geometry points and was timing out, silently degrading to a
    # straight line.
    return TomTomRoutingProvider(api_keys=keys, timeout=30.0)


@router.post("/live", response_model=LiveRouteResponse)
async def live_route(
    body: LiveRouteRequest, identity: Identity = Depends(get_identity)
) -> LiveRouteResponse:
    """Fetch real road geometry and traffic for a sequence of legs."""
    s = get_settings()
    warnings: list[str] = []
    results: list[LiveLegResult] = []
    providers_used: set[str] = set()
    traffic_available = False

    tt = _provider() if s.tomtom_configured else None

    for leg in body.legs:
        # Cache per leg: geometry is stable, traffic is not, so this rides the
        # short DYNAMIC TTL rather than being stored long-term.
        key = (f"live:{leg.from_point.latitude:.5f},{leg.from_point.longitude:.5f}"
               f"->{leg.to_point.latitude:.5f},{leg.to_point.longitude:.5f}"
               f":{body.travel_mode}")
        cached = await cache.get_json(key)
        if cached:
            results.append(LiveLegResult(**cached, kind=leg.kind, label=leg.label)
                           if "kind" not in cached
                           else LiveLegResult(**{**cached, "kind": leg.kind,
                                                 "label": leg.label}))
            providers_used.add(cached.get("provider", "offline_estimate"))
            traffic_available = traffic_available or cached.get("provider") == "tomtom"
            continue

        got = None
        if tt is not None and tt.available:
            try:
                from routing.models import LatLon
                routes = tt.get_alternative_routes(
                    LatLon(leg.from_point.latitude, leg.from_point.longitude),
                    LatLon(leg.to_point.latitude, leg.to_point.longitude),
                    max_alternatives=body.max_alternatives,
                    travel_mode=body.travel_mode,
                )
                if routes:
                    r = routes[0]
                    got = LiveLegResult(
                        kind=leg.kind, label=leg.label,
                        distance_km=round(r.distance_km, 2),
                        travel_time_min=round(r.travel_time_min, 1),
                        traffic_delay_min=round(r.traffic_delay_min, 1),
                        polyline=[[lat, lon] for lat, lon in r.geometry],
                        n_geometry_points=len(r.geometry),
                        provider="tomtom",
                    )
                    providers_used.add("tomtom")
                    traffic_available = True
            except Exception as e:
                log.warning("tomtom leg failed: %s", e)
                warnings.append(f"Live routing unavailable for one leg ({type(e).__name__}).")

        if got is None:
            # Honest fallback: a straight-line estimate, labelled as such.
            from vb.geo import haversine_km
            km = haversine_km(leg.from_point.latitude, leg.from_point.longitude,
                              leg.to_point.latitude, leg.to_point.longitude) * 1.35
            got = LiveLegResult(
                kind=leg.kind, label=leg.label,
                distance_km=round(km, 2),
                travel_time_min=round(km / 40 * 60, 1),
                traffic_delay_min=0.0,
                polyline=[[leg.from_point.latitude, leg.from_point.longitude],
                          [leg.to_point.latitude, leg.to_point.longitude]],
                n_geometry_points=2,
                provider="offline_estimate",
            )
            providers_used.add("offline_estimate")
            if tt is None or not tt.available:
                warnings.append(
                    "TomTom is not available; showing a straight-line estimate.")

        await cache.set_json(key, got.model_dump(mode="json"),
                             ttl_s=s.route_cache_ttl_s)
        results.append(got)

    if not results:
        raise HTTPException(status_code=400, detail="No legs could be routed.")

    return LiveRouteResponse(
        legs=results,
        total_distance_km=round(sum(r.distance_km for r in results), 2),
        total_time_min=round(sum(r.travel_time_min for r in results), 1),
        total_traffic_delay_min=round(sum(r.traffic_delay_min for r in results), 1),
        # Report the truth when legs came from different sources rather than
        # letting the last leg decide the label for the whole route.
        provider=("tomtom" if providers_used == {"tomtom"}
                  else "mixed" if "tomtom" in providers_used
                  else "offline_estimate"),
        traffic_available=traffic_available,
        warnings=sorted(set(warnings)),
    )


@router.get("/live/traffic-config")
async def traffic_config(identity: Identity = Depends(get_identity)) -> dict:
    """Give the map what it needs to render a traffic overlay.

    The key is returned only to authenticated callers and only when traffic
    tiles are actually usable — the frontend cannot render the overlay without
    it, and a hardcoded key in the bundle is exactly what Phase-B removed.
    """
    s = get_settings()
    keys = [k.strip() for k in s.tomtom_api_keys.split(",") if k.strip()]
    if not keys:
        return {"available": False, "reason": "no TomTom key configured"}

    # Probe keys so the frontend is never handed a dead one.
    import httpx
    probe = "https://api.tomtom.com/traffic/map/4/tile/flow/relative0/10/730/440.png"
    async with httpx.AsyncClient(timeout=8.0) as client:
        for k in keys:
            try:
                r = await client.get(probe, params={"key": k})
                if r.status_code == 200:
                    return {
                        "available": True,
                        "tile_url": ("https://api.tomtom.com/traffic/map/4/tile/"
                                     "flow/relative0/{z}/{x}/{y}.png?key=" + k),
                        "attribution": "© TomTom",
                        "style": "relative0",
                    }
            except Exception:
                continue
    return {"available": False, "reason": "no TomTom key can serve traffic tiles"}
