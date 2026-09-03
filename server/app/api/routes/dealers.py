"""Input dealer endpoints: replenishment requirements and incoming deliveries."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from server.app.core.security import Identity, require_role
from server.app.repositories.transport_repo import requirement_repo
from server.app.repositories.user_repo import user_repo
from server.app.schemas.common import (
    GeoPoint, QuantityUnit, RequirementStatus, UserRole,
)
from server.app.services.quantity_service import (
    clarification_needed, normalize_quantity,
)

router = APIRouter()
dealer_only = require_role(UserRole.INPUT_DEALER)

# Rural building-material and agricultural-input categories.
MATERIALS = [
    "cement", "tmt", "brick", "hardware", "pipe", "electrical",
    "paint", "tile", "sanitary", "roofing", "multi", "agri_input",
]


class RequirementIn(BaseModel):
    material: str = Field(..., description="One of the supported categories")
    material_label: str | None = None
    quantity_value: float = Field(..., gt=0)
    quantity_unit: QuantityUnit
    supplier_hub_id: str | None = None
    supplier_label: str | None = None
    delivery_location_id: str | None = None
    delivery_point: GeoPoint | None = None
    delivery_label: str | None = None
    needed_by: str | None = None
    notes: str | None = None


class RequirementOut(BaseModel):
    requirement_id: str
    status: RequirementStatus
    material: str
    material_label: str | None = None
    quantity_value: float
    quantity_unit: QuantityUnit
    quantity_kg: float | None
    conversion_confidence: str
    needs_clarification: bool = False
    clarification_prompt: str | None = None
    delivery_label: str | None = None
    supplier_label: str | None = None
    needed_by: str | None = None
    matched_vehicle_id: str | None = None
    created_at: str | None = None


def _to_out(d: dict) -> RequirementOut:
    return RequirementOut(
        requirement_id=d["requirement_id"],
        status=RequirementStatus(d["status"]),
        material=d.get("material", ""),
        material_label=d.get("material_label"),
        quantity_value=d.get("quantity_value", 0),
        quantity_unit=QuantityUnit(d.get("quantity_unit", "kg")),
        quantity_kg=d.get("quantity_kg"),
        conversion_confidence=d.get("conversion_confidence", "unresolved"),
        needs_clarification=d.get("needs_clarification", False),
        clarification_prompt=d.get("clarification_prompt"),
        delivery_label=d.get("delivery_label"),
        supplier_label=d.get("supplier_label"),
        needed_by=d.get("needed_by"),
        matched_vehicle_id=d.get("matched_vehicle_id"),
        created_at=str(d.get("created_at")) if d.get("created_at") else None,
    )


@router.get("/profile")
async def profile(identity: Identity = Depends(dealer_only)) -> dict:
    user = await user_repo.get_by_clerk_id(identity.user_id)
    return {"user_id": identity.user_id, "role": identity.role,
            "profile": (user or {}).get("profile", {})}


@router.get("/materials")
async def materials() -> dict:
    return {"materials": MATERIALS}


@router.post("/requirements", response_model=RequirementOut, status_code=201)
async def create_requirement(
    body: RequirementIn, identity: Identity = Depends(dealer_only)
) -> RequirementOut:
    """Create a replenishment requirement.

    Building material stated in `bori` has no crop, so the conversion is
    genuinely unresolvable — the same honesty rule as farmer requests applies,
    and the requirement stays a DRAFT until clarified.
    """
    user = await user_repo.get_by_clerk_id(identity.user_id)
    q = normalize_quantity(body.quantity_value, body.quantity_unit, None)
    prompt = clarification_needed(q)

    doc = {
        "dealer_user_id": identity.user_id,
        "business_name": (user or {}).get("profile", {}).get("business_name"),
        "material": body.material,
        "material_label": body.material_label,
        "quantity_value": q.value,
        "quantity_unit": q.unit.value,
        "quantity_kg": q.quantity_kg,
        "conversion_source": q.conversion_source,
        "conversion_confidence": q.conversion_confidence.value,
        "needs_clarification": prompt is not None,
        "clarification_prompt": prompt,
        "supplier_hub_id": body.supplier_hub_id,
        "supplier_label": body.supplier_label,
        "delivery_location_id": body.delivery_location_id,
        "delivery_label": body.delivery_label,
        "delivery_location": ({"geo": body.delivery_point.to_geojson(),
                               "latitude": body.delivery_point.latitude,
                               "longitude": body.delivery_point.longitude}
                              if body.delivery_point else None),
        "needed_by": body.needed_by,
        "notes": body.notes,
        "status": (RequirementStatus.DRAFT if prompt
                   else RequirementStatus.OPEN).value,
    }
    created = await requirement_repo.create(doc)
    return _to_out(created)


@router.get("/requirements", response_model=list[RequirementOut])
async def list_requirements(
    identity: Identity = Depends(dealer_only)
) -> list[RequirementOut]:
    docs = await requirement_repo.list_for_dealer(identity.user_id)
    return [_to_out(d) for d in docs]


@router.get("/requirements/{requirement_id}", response_model=RequirementOut)
async def get_requirement(
    requirement_id: str, identity: Identity = Depends(dealer_only)
) -> RequirementOut:
    d = await requirement_repo.get(requirement_id)
    if d is None or d.get("dealer_user_id") != identity.user_id:
        raise HTTPException(status_code=404, detail="Requirement not found.")
    return _to_out(d)


@router.get("/incoming", response_model=list[RequirementOut])
async def incoming(
    identity: Identity = Depends(dealer_only)
) -> list[RequirementOut]:
    """Requirements that have been matched to a truck and are on the way."""
    cur = requirement_repo.col.find({
        "dealer_user_id": identity.user_id,
        "status": {"$in": [RequirementStatus.MATCHED.value,
                           RequirementStatus.IN_TRANSIT.value]},
    }, {"_id": 0}).sort("updated_at", -1).limit(30)
    docs = await cur.to_list(length=30)
    return [_to_out(d) for d in docs]


class RequirementStatusUpdate(BaseModel):
    status: RequirementStatus


@router.post("/requirements/{requirement_id}/status", response_model=RequirementOut)
async def set_status(
    requirement_id: str, body: RequirementStatusUpdate,
    identity: Identity = Depends(dealer_only),
) -> RequirementOut:
    d = await requirement_repo.get(requirement_id)
    if d is None or d.get("dealer_user_id") != identity.user_id:
        raise HTTPException(status_code=404, detail="Requirement not found.")
    updated = await requirement_repo.set_status(requirement_id, body.status)
    return _to_out(updated)
