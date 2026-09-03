"""Identity and role onboarding.

Role assignment happens here and is stored server-side. Every role check
elsewhere reads the database, never a client claim.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from server.app.core.config import get_settings
from server.app.core.security import Identity, get_identity
from server.app.repositories.user_repo import user_repo
from server.app.schemas.common import UserRole

router = APIRouter()


class MeResponse(BaseModel):
    user_id: str
    email: str | None = None
    role: UserRole | None = None
    onboarded: bool = False
    auth_source: str


class RoleSelection(BaseModel):
    role: UserRole
    display_name: str | None = None
    phone: str | None = None
    district: str | None = None
    # Role-specific onboarding fields, kept optional so first-time users are not
    # confronted with a long form.
    village: str | None = None
    primary_crop: str | None = None
    vehicle_number: str | None = None
    vehicle_class: str | None = None
    capacity_kg: float | None = Field(default=None, gt=0)
    business_name: str | None = None
    shop_category: str | None = None


class DevLoginRequest(BaseModel):
    user_id: str
    email: str | None = None
    role: UserRole | None = None


@router.get("/me", response_model=MeResponse)
async def me(identity: Identity = Depends(get_identity)) -> MeResponse:
    return MeResponse(
        user_id=identity.user_id, email=identity.email, role=identity.role,
        onboarded=identity.onboarded, auth_source=identity.source,
    )


@router.post("/me/role", response_model=MeResponse)
async def select_role(
    body: RoleSelection, identity: Identity = Depends(get_identity)
) -> MeResponse:
    """Complete role onboarding. Only the fields relevant to the chosen role
    are persisted, so a farmer never carries empty vehicle attributes."""
    common = {"display_name": body.display_name, "phone": body.phone,
              "district": body.district}
    by_role = {
        UserRole.FARMER: {"village": body.village, "primary_crop": body.primary_crop},
        UserRole.TRUCKER: {"vehicle_number": body.vehicle_number,
                           "vehicle_class": body.vehicle_class,
                           "capacity_kg": body.capacity_kg},
        UserRole.INPUT_DEALER: {"business_name": body.business_name,
                                "shop_category": body.shop_category},
    }[body.role]
    profile = {k: v for k, v in {**common, **by_role}.items() if v is not None}

    await user_repo.upsert(identity.user_id, email=identity.email)
    user = await user_repo.set_role(identity.user_id, body.role, profile)
    return MeResponse(user_id=identity.user_id, email=user.get("email"),
                      role=UserRole(user["role"]), onboarded=True,
                      auth_source=identity.source)


@router.post("/auth/dev-login", response_model=MeResponse)
async def dev_login(body: DevLoginRequest) -> MeResponse:
    """Development-only login. Creates or fetches a local user.

    Returns 404 outside development so the endpoint does not even advertise its
    existence in production. Guarded by `demo_auth_active`, which requires both
    an explicit flag and a non-production environment.
    """
    s = get_settings()
    if not s.demo_auth_active:
        raise HTTPException(status_code=404, detail="Not found.")

    await user_repo.upsert(body.user_id, email=body.email)
    if body.role:
        await user_repo.set_role(body.user_id, body.role, {})
    user = await user_repo.get_by_clerk_id(body.user_id)
    return MeResponse(
        user_id=body.user_id, email=(user or {}).get("email"),
        role=UserRole(user["role"]) if user and user.get("role") else None,
        onboarded=bool(user and user.get("role")), auth_source="dev",
    )
