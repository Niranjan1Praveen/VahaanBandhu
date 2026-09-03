"""Trucker endpoints: vehicles, availability, jobs and circular-return matching.

The circular-logistics endpoint is the product differentiator: after a delivery
at a mandi, it looks for a dealer requirement near that mandi and roughly on the
way home, and reports the empty kilometres such a return load would avoid.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from server.app.core.security import Identity, require_role
from server.app.repositories.transport_repo import (
    location_repo, requirement_repo, transport_repo, vehicle_repo,
)
from server.app.repositories.user_repo import user_repo
from server.app.schemas.common import GeoPoint, TransportStatus, UserRole

router = APIRouter()
trucker_only = require_role(UserRole.TRUCKER)

DETOUR_FACTOR = 1.35


class VehicleIn(BaseModel):
    vehicle_number: str
    vehicle_class: str
    capacity_kg: float = Field(..., gt=0, le=40000)
    body_type: str | None = None
    fuel_type: str | None = None


class VehicleOut(BaseModel):
    vehicle_id: str
    vehicle_number: str
    vehicle_class: str
    capacity_kg: float
    available: bool = False
    latitude: float | None = None
    longitude: float | None = None


class AvailabilityIn(BaseModel):
    available: bool
    point: GeoPoint | None = None


class JobOut(BaseModel):
    request_id: str
    status: TransportStatus
    crop_label: str | None = None
    crop_key: str | None = None
    quantity_value: float | None = None
    quantity_unit: str | None = None
    quantity_kg: float | None = None
    mandi_label: str | None = None
    mandi_id: str | None = None
    origin_label: str | None = None
    distance_hint_km: float | None = None


class ReturnLoadOut(BaseModel):
    """A candidate return load, with the empty distance it would avoid."""

    requirement_id: str
    business_name: str | None = None
    material: str | None = None
    quantity_kg: float | None = None
    delivery_label: str | None = None
    distance_from_mandi_km: float
    detour_km: float
    empty_km_avoided: float
    estimated_revenue_inr: float | None = None


@router.get("/profile")
async def profile(identity: Identity = Depends(trucker_only)) -> dict:
    user = await user_repo.get_by_clerk_id(identity.user_id)
    return {"user_id": identity.user_id, "role": identity.role,
            "profile": (user or {}).get("profile", {})}


@router.post("/vehicles", response_model=VehicleOut, status_code=201)
async def add_vehicle(body: VehicleIn,
                      identity: Identity = Depends(trucker_only)) -> VehicleOut:
    doc = await vehicle_repo.create({
        "owner_user_id": identity.user_id,
        "vehicle_number": body.vehicle_number,
        "vehicle_class": body.vehicle_class,
        "capacity_kg": body.capacity_kg,
        "body_type": body.body_type,
        "fuel_type": body.fuel_type,
        "available": False,
    })
    return VehicleOut(**{k: doc.get(k) for k in VehicleOut.model_fields})


@router.get("/vehicles", response_model=list[VehicleOut])
async def list_vehicles(
    identity: Identity = Depends(trucker_only)
) -> list[VehicleOut]:
    docs = await vehicle_repo.list_for_owner(identity.user_id)
    return [VehicleOut(**{k: d.get(k) for k in VehicleOut.model_fields}) for d in docs]


@router.post("/vehicles/{vehicle_id}/availability", response_model=VehicleOut)
async def set_availability(
    vehicle_id: str, body: AvailabilityIn,
    identity: Identity = Depends(trucker_only),
) -> VehicleOut:
    doc = await vehicle_repo.get(vehicle_id)
    if doc is None or doc.get("owner_user_id") != identity.user_id:
        raise HTTPException(status_code=404, detail="Vehicle not found.")
    updated = await vehicle_repo.set_availability(
        vehicle_id, body.available,
        body.point.latitude if body.point else None,
        body.point.longitude if body.point else None)
    return VehicleOut(**{k: updated.get(k) for k in VehicleOut.model_fields})


@router.get("/jobs", response_model=list[JobOut])
async def available_jobs(
    identity: Identity = Depends(trucker_only),
    limit: int = Query(default=20, le=50),
) -> list[JobOut]:
    """Open farmer requests a trucker can take."""
    docs = await transport_repo.list_open(limit=limit)
    return [JobOut(
        request_id=d["request_id"], status=TransportStatus(d["status"]),
        crop_label=d.get("crop_label"), crop_key=d.get("crop_key"),
        quantity_value=d.get("quantity_value"), quantity_unit=d.get("quantity_unit"),
        quantity_kg=d.get("quantity_kg"), mandi_label=d.get("mandi_label"),
        mandi_id=d.get("mandi_id"), origin_label=d.get("origin_label"),
    ) for d in docs]


@router.get("/jobs/mine", response_model=list[JobOut])
async def my_jobs(identity: Identity = Depends(trucker_only)) -> list[JobOut]:
    cur = transport_repo.col.find(
        {"assigned_trucker_user_id": identity.user_id}, {"_id": 0}
    ).sort("created_at", -1).limit(50)
    docs = await cur.to_list(length=50)
    return [JobOut(
        request_id=d["request_id"], status=TransportStatus(d["status"]),
        crop_label=d.get("crop_label"), crop_key=d.get("crop_key"),
        quantity_value=d.get("quantity_value"), quantity_unit=d.get("quantity_unit"),
        quantity_kg=d.get("quantity_kg"), mandi_label=d.get("mandi_label"),
        mandi_id=d.get("mandi_id"), origin_label=d.get("origin_label"),
    ) for d in docs]


class AcceptJob(BaseModel):
    vehicle_id: str


@router.post("/jobs/{request_id}/accept", response_model=JobOut)
async def accept_job(request_id: str, body: AcceptJob,
                     identity: Identity = Depends(trucker_only)) -> JobOut:
    """Accept a job. Capacity is checked server-side before assignment."""
    req = await transport_repo.get(request_id)
    if req is None:
        raise HTTPException(status_code=404, detail="Job not found.")
    veh = await vehicle_repo.get(body.vehicle_id)
    if veh is None or veh.get("owner_user_id") != identity.user_id:
        raise HTTPException(status_code=404, detail="Vehicle not found.")

    load = req.get("quantity_kg")
    if load is None:
        raise HTTPException(
            status_code=400,
            detail=("This request's quantity is unresolved, so its weight is "
                    "unknown. It cannot be assigned until the farmer clarifies."))
    if load > float(veh["capacity_kg"]):
        raise HTTPException(
            status_code=400,
            detail=f"Load {load:.0f} kg exceeds vehicle capacity "
                   f"{veh['capacity_kg']:.0f} kg.")

    await transport_repo.assign_vehicle(request_id, body.vehicle_id, identity.user_id)
    current = TransportStatus(req["status"])
    if current is TransportStatus.REQUESTED:
        await transport_repo.transition(request_id, TransportStatus.MATCHING,
                                        identity.user_id)
    await transport_repo.transition(request_id, TransportStatus.MATCHED,
                                    identity.user_id)
    updated = await transport_repo.transition(request_id, TransportStatus.ACCEPTED,
                                              identity.user_id)
    return JobOut(
        request_id=updated["request_id"], status=TransportStatus(updated["status"]),
        crop_label=updated.get("crop_label"), crop_key=updated.get("crop_key"),
        quantity_value=updated.get("quantity_value"),
        quantity_unit=updated.get("quantity_unit"),
        quantity_kg=updated.get("quantity_kg"),
        mandi_label=updated.get("mandi_label"), mandi_id=updated.get("mandi_id"),
        origin_label=updated.get("origin_label"))


class StatusUpdate(BaseModel):
    status: TransportStatus


@router.post("/jobs/{request_id}/status", response_model=JobOut)
async def update_status(request_id: str, body: StatusUpdate,
                        identity: Identity = Depends(trucker_only)) -> JobOut:
    req = await transport_repo.get(request_id)
    if req is None or req.get("assigned_trucker_user_id") != identity.user_id:
        raise HTTPException(status_code=404, detail="Job not found.")
    try:
        updated = await transport_repo.transition(request_id, body.status,
                                                  identity.user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return JobOut(
        request_id=updated["request_id"], status=TransportStatus(updated["status"]),
        crop_label=updated.get("crop_label"), crop_key=updated.get("crop_key"),
        quantity_kg=updated.get("quantity_kg"),
        mandi_label=updated.get("mandi_label"))


@router.get("/return-loads", response_model=list[ReturnLoadOut])
async def return_loads(
    identity: Identity = Depends(trucker_only),
    mandi_id: str | None = Query(default=None),
    latitude: float | None = Query(default=None),
    longitude: float | None = Query(default=None),
    home_latitude: float | None = Query(default=None),
    home_longitude: float | None = Query(default=None),
    capacity_kg: float = Query(default=10000, gt=0),
    max_km: float = Query(default=60, le=200),
) -> list[ReturnLoadOut]:
    """Circular logistics: dealer requirements near the mandi, headed homeward.

    `empty_km_avoided` is the honest quantity: how much of the otherwise-empty
    return leg the load actually replaces, not the raw distance to the dealer.
    A requirement 40 km in the wrong direction adds 80 km and avoids nothing.
    """
    from vb.geo import haversine_km

    lat, lon = latitude, longitude
    if mandi_id and (lat is None or lon is None):
        mandis = await location_repo.list_mandis()
        m = next((x for x in mandis if x.get("mandi_id") == mandi_id), None)
        if m:
            lat, lon = m.get("latitude"), m.get("longitude")
    if lat is None or lon is None:
        raise HTTPException(
            status_code=400,
            detail="Provide a mandi_id or explicit latitude/longitude.")

    docs = await requirement_repo.near(lat, lon, max_km=max_km, limit=12)
    hlat = home_latitude if home_latitude is not None else lat
    hlon = home_longitude if home_longitude is not None else lon
    base_home_km = haversine_km(lat, lon, hlat, hlon) * DETOUR_FACTOR

    out: list[ReturnLoadOut] = []
    for d in docs:
        loc = d.get("delivery_location") or {}
        dlat, dlon = loc.get("latitude"), loc.get("longitude")
        if dlat is None or dlon is None:
            continue
        qkg = d.get("quantity_kg")
        if qkg is not None and qkg > capacity_kg:
            continue

        km_from_mandi = haversine_km(lat, lon, dlat, dlon) * DETOUR_FACTOR
        km_to_home = haversine_km(dlat, dlon, hlat, hlon) * DETOUR_FACTOR
        detour = max((km_from_mandi + km_to_home) - base_home_km, 0.0)
        # The loaded leg replaces empty running only up to the baseline distance.
        avoided = max(min(km_from_mandi, base_home_km) - detour, 0.0)

        out.append(ReturnLoadOut(
            requirement_id=d["requirement_id"],
            business_name=d.get("business_name"),
            material=d.get("material"),
            quantity_kg=qkg,
            delivery_label=d.get("delivery_label"),
            distance_from_mandi_km=round(km_from_mandi, 1),
            detour_km=round(detour, 1),
            empty_km_avoided=round(avoided, 1),
            estimated_revenue_inr=round((qkg or 0) / 1000 * max(km_from_mandi, 1) * 4.5, 0),
        ))

    out.sort(key=lambda r: -r.empty_km_avoided)
    return out
