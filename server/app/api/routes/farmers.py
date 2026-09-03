"""Farmer endpoints: create and track transport requests."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from server.app.core.security import Identity, get_identity, require_role
from server.app.repositories.transport_repo import transport_repo
from server.app.repositories.user_repo import user_repo
from server.app.schemas.common import (
    GeoPoint, InputMode, Language, QuantityUnit, TransportStatus, UserRole,
)
from server.app.services.quantity_service import (
    clarification_needed, normalize_quantity,
)

router = APIRouter()
farmer_only = require_role(UserRole.FARMER)


class CreateTransportRequest(BaseModel):
    crop_key: str = Field(..., description="Canonical crop key, e.g. 'wheat'")
    crop_label: str | None = None
    mandi_id: str | None = None
    mandi_label: str | None = None
    quantity_value: float = Field(..., gt=0)
    quantity_unit: QuantityUnit
    origin_location_id: str | None = None
    origin_point: GeoPoint | None = None
    origin_label: str | None = None
    pickup_date: str | None = None
    notes: str | None = None
    language: Language = Language.HI
    input_mode: InputMode = InputMode.TEXT
    raw_utterance: str | None = None


class TransportRequestOut(BaseModel):
    request_id: str
    status: TransportStatus
    crop_key: str
    crop_label: str | None = None
    mandi_id: str | None = None
    mandi_label: str | None = None
    quantity_value: float
    quantity_unit: QuantityUnit
    quantity_kg: float | None
    conversion_confidence: str
    conversion_source: str | None
    needs_clarification: bool = False
    clarification_prompt: str | None = None
    origin_label: str | None = None
    assigned_vehicle_id: str | None = None
    created_at: str | None = None
    status_history: list[dict] = Field(default_factory=list)


def _to_out(doc: dict) -> TransportRequestOut:
    return TransportRequestOut(
        request_id=doc["request_id"],
        status=TransportStatus(doc["status"]),
        crop_key=doc.get("crop_key", ""),
        crop_label=doc.get("crop_label"),
        mandi_id=doc.get("mandi_id"),
        mandi_label=doc.get("mandi_label"),
        quantity_value=doc.get("quantity_value", 0),
        quantity_unit=QuantityUnit(doc.get("quantity_unit", "kg")),
        quantity_kg=doc.get("quantity_kg"),
        conversion_confidence=doc.get("conversion_confidence", "unresolved"),
        conversion_source=doc.get("conversion_source"),
        needs_clarification=doc.get("needs_clarification", False),
        clarification_prompt=doc.get("clarification_prompt"),
        origin_label=doc.get("origin_label"),
        assigned_vehicle_id=doc.get("assigned_vehicle_id"),
        created_at=str(doc.get("created_at")) if doc.get("created_at") else None,
        status_history=[
            {"status": h.get("status"), "at": str(h.get("at"))}
            for h in doc.get("status_history", [])
        ],
    )


@router.get("/profile")
async def profile(identity: Identity = Depends(farmer_only)) -> dict:
    user = await user_repo.get_by_clerk_id(identity.user_id)
    return {"user_id": identity.user_id, "role": identity.role,
            "profile": (user or {}).get("profile", {})}


@router.post("/requests", response_model=TransportRequestOut, status_code=201)
async def create_request(
    body: CreateTransportRequest, identity: Identity = Depends(farmer_only)
) -> TransportRequestOut:
    """Create a transport request.

    The quantity is normalized here. If it cannot be resolved -- typically a bori
    with no determinable bag weight -- the request is still created, but flagged
    with a clarification prompt and left unmatched. It is never silently
    converted, because a wrong kilogram figure dispatches the wrong vehicle.
    """
    q = normalize_quantity(body.quantity_value, body.quantity_unit, body.crop_key)
    prompt = clarification_needed(q)

    doc = {
        "requester_user_id": identity.user_id,
        "requester_role": UserRole.FARMER.value,
        "crop_key": body.crop_key,
        "crop_label": body.crop_label,
        "mandi_id": body.mandi_id,
        "mandi_label": body.mandi_label,
        "quantity_value": q.value,
        "quantity_unit": q.unit.value,
        "quantity_kg": q.quantity_kg,
        "bag_weight_kg_used": q.bag_weight_kg_used,
        "conversion_source": q.conversion_source,
        "conversion_confidence": q.conversion_confidence.value,
        "needs_clarification": prompt is not None,
        "clarification_prompt": prompt,
        "origin_location_id": body.origin_location_id,
        "origin_label": body.origin_label,
        "origin": ({"geo": body.origin_point.to_geojson(),
                    "latitude": body.origin_point.latitude,
                    "longitude": body.origin_point.longitude}
                   if body.origin_point else None),
        "pickup_date": body.pickup_date,
        "notes": body.notes,
        "language": body.language.value,
        "input_mode": body.input_mode.value,
        "raw_utterance": body.raw_utterance,
        # An unresolved quantity cannot enter matching.
        "status": (TransportStatus.DRAFT if prompt
                   else TransportStatus.REQUESTED).value,
    }
    created = await transport_repo.create(doc)
    return _to_out(created)


@router.get("/requests", response_model=list[TransportRequestOut])
async def list_requests(
    identity: Identity = Depends(farmer_only)
) -> list[TransportRequestOut]:
    docs = await transport_repo.list_for_user(identity.user_id)
    return [_to_out(d) for d in docs]


@router.get("/requests/{request_id}", response_model=TransportRequestOut)
async def get_request(
    request_id: str, identity: Identity = Depends(farmer_only)
) -> TransportRequestOut:
    doc = await transport_repo.get(request_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Request not found.")
    if doc.get("requester_user_id") != identity.user_id:
        # Do not leak existence of other users' requests.
        raise HTTPException(status_code=404, detail="Request not found.")
    return _to_out(doc)


class ResolveQuantity(BaseModel):
    bag_weight_kg: float = Field(..., gt=0, le=200)


@router.post("/requests/{request_id}/resolve-quantity",
             response_model=TransportRequestOut)
async def resolve_quantity(
    request_id: str, body: ResolveQuantity,
    identity: Identity = Depends(farmer_only),
) -> TransportRequestOut:
    """Supply the missing bori weight so the request can enter matching.

    This is the clarification path that exists precisely so the system never
    guesses a conversion.
    """
    doc = await transport_repo.get(request_id)
    if doc is None or doc.get("requester_user_id") != identity.user_id:
        raise HTTPException(status_code=404, detail="Request not found.")
    if not doc.get("needs_clarification"):
        raise HTTPException(status_code=400,
                            detail="This request does not need clarification.")

    kg = float(doc["quantity_value"]) * body.bag_weight_kg
    await transport_repo.col.update_one(
        {"request_id": request_id},
        {"$set": {
            "quantity_kg": kg,
            "bag_weight_kg_used": body.bag_weight_kg,
            "conversion_source": "user_supplied_bag_weight",
            "conversion_confidence": "exact",
            "needs_clarification": False,
            "clarification_prompt": None,
        }})
    updated = await transport_repo.transition(
        request_id, TransportStatus.REQUESTED, identity.user_id)
    return _to_out(updated)
