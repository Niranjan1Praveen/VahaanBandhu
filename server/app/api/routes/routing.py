"""Routing endpoints. The only optimization surface the application exposes.

Every request goes through `RoutingService` -> `VBQEROptimizer`. No endpoint
here calls an individual solver, and none can reach IBM Quantum.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from server.app.core.security import Identity, get_identity
from server.app.repositories.transport_repo import (
    location_repo, route_result_repo, transport_repo,
)
from server.app.schemas.common import GeoPoint, UserRole
from server.app.schemas.routing import (
    RouteOptimizeResponse, RouteSolution, RouteStop, RoutingRequest,
)
from server.app.services.routing_service import routing_service

router = APIRouter()


@router.post("/optimize", response_model=RouteOptimizeResponse)
async def optimize(
    body: RoutingRequest, identity: Identity = Depends(get_identity)
) -> RouteOptimizeResponse:
    """Optimize a route through VB-QER.

    The response carries a user-facing explanation plus enough provenance
    (versions, snapshot, whether a quantum artifact contributed) to reason about
    staleness — but no research internals.
    """
    solution, warnings = await routing_service.optimize(body)
    try:
        await route_result_repo.save(solution.model_dump(mode="json"))
    except Exception:
        # Persistence failure must not deny the user their route.
        warnings.append("Route computed but could not be saved for history.")
    return RouteOptimizeResponse(solution=solution, warnings=warnings)


@router.post("/optimize/request/{request_id}", response_model=RouteOptimizeResponse)
async def optimize_for_request(
    request_id: str, identity: Identity = Depends(get_identity)
) -> RouteOptimizeResponse:
    """Optimize the route for an existing transport request.

    Resolves the origin and mandi from stored data so the client never has to
    hand the optimizer raw coordinates it might get wrong.
    """
    req = await transport_repo.get(request_id)
    if req is None:
        raise HTTPException(status_code=404, detail="Request not found.")

    origin = RouteStop(
        location_id=req.get("origin_location_id"),
        name=req.get("origin_label"),
        kind="farm",
        point=(GeoPoint(latitude=req["origin"]["latitude"],
                        longitude=req["origin"]["longitude"])
               if req.get("origin") else None),
    )

    dest_point = None
    dest_location_id = None
    if req.get("mandi_id"):
        mandis = await location_repo.list_mandis()
        m = next((x for x in mandis if x.get("mandi_id") == req["mandi_id"]), None)
        if m and m.get("latitude") is not None:
            dest_point = GeoPoint(latitude=m["latitude"], longitude=m["longitude"])
            dest_location_id = m.get("location_id")

    destination = RouteStop(
        location_id=dest_location_id, name=req.get("mandi_label"),
        kind="mandi", point=dest_point)

    routing_request = RoutingRequest(
        origin=origin, destination=destination,
        role=UserRole(req.get("requester_role", UserRole.FARMER.value)),
        request_id=request_id,
        capacity_kg=None,
        mandi_id=req.get("mandi_id"),
    )
    solution, warnings = await routing_service.optimize(routing_request)
    try:
        await route_result_repo.save(solution.model_dump(mode="json"))
    except Exception:
        warnings.append("Route computed but could not be saved for history.")
    return RouteOptimizeResponse(solution=solution, warnings=warnings)


@router.get("/{route_id}", response_model=RouteSolution)
async def get_route(
    route_id: str, identity: Identity = Depends(get_identity)
) -> RouteSolution:
    doc = await route_result_repo.get(route_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Route not found.")
    doc.pop("created_at", None)
    return RouteSolution(**doc)


@router.get("/engine/info")
async def engine_info() -> dict:
    """What optimization engine is in use, and what it will never do."""
    from server.app.services.routing_service import vbqer_version
    return {
        "engine": "VB-QER",
        "full_name": "VahaanBandhu Quantum-Enhanced Routing Ensemble",
        "version": vbqer_version(),
        "architecture_status": "FIXED",
        "live_quantum_hardware_call": False,
        "note": ("Classical solvers, QUBO formulations, QAOA and quantum-derived "
                 "artifacts are components inside VB-QER, not alternatives to it."),
    }
