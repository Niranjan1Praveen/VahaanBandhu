"""Shared enums and value objects for the application-facing API.

These are the **frozen research/application boundary types**. Internal optimization
details -- QUBO matrices, bitstrings, QAOA parameters, artifact internals -- never
appear here. The application depends on this contract, not on VB-QER internals,
so the routing research can evolve without breaking the application.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, field_validator

# Coarse project region. Mirrors vb.config.COARSE_BBOX, which was widened to
# 32.6N during the routing research because 31.5 excluded real Punjab districts.
LAT_MIN, LAT_MAX = 23.0, 32.6
LON_MIN, LON_MAX = 73.0, 85.0


class UserRole(str, Enum):
    FARMER = "FARMER"
    TRUCKER = "TRUCKER"
    INPUT_DEALER = "INPUT_DEALER"


class Language(str, Enum):
    HI = "hi"
    EN = "en"
    HINGLISH = "hinglish"


class InputMode(str, Enum):
    TEXT = "text"
    VOICE = "voice"


class QuantityUnit(str, Enum):
    KG = "kg"
    BORI = "bori"
    QUINTAL = "quintal"
    TONNE = "tonne"


class ConversionConfidence(str, Enum):
    EXACT = "exact"
    CROP_DEFAULT = "crop_default"
    REGIONAL_DEFAULT = "regional_default"
    UNRESOLVED = "unresolved"


class VehicleClass(str, Enum):
    PICKUP = "pickup"
    LCV = "LCV"
    TWO_AXLE = "2axle"
    THREE_AXLE = "3axle"
    MULTI_AXLE = "multi_axle"


class TransportStatus(str, Enum):
    """Explicit workflow states. Transitions are validated server-side."""

    DRAFT = "DRAFT"
    REQUESTED = "REQUESTED"
    MATCHING = "MATCHING"
    MATCHED = "MATCHED"
    ACCEPTED = "ACCEPTED"
    PICKUP = "PICKUP"
    IN_TRANSIT = "IN_TRANSIT"
    AT_MANDI = "AT_MANDI"
    RETURN_LOAD = "RETURN_LOAD"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


# Allowed transitions. Anything absent is rejected by the service layer, so a
# client cannot drive a request into an impossible state.
ALLOWED_TRANSITIONS: dict[TransportStatus, set[TransportStatus]] = {
    TransportStatus.DRAFT: {TransportStatus.REQUESTED, TransportStatus.CANCELLED},
    TransportStatus.REQUESTED: {TransportStatus.MATCHING, TransportStatus.CANCELLED},
    TransportStatus.MATCHING: {TransportStatus.MATCHED, TransportStatus.CANCELLED},
    TransportStatus.MATCHED: {TransportStatus.ACCEPTED, TransportStatus.CANCELLED},
    TransportStatus.ACCEPTED: {TransportStatus.PICKUP, TransportStatus.CANCELLED},
    TransportStatus.PICKUP: {TransportStatus.IN_TRANSIT, TransportStatus.CANCELLED},
    TransportStatus.IN_TRANSIT: {TransportStatus.AT_MANDI, TransportStatus.CANCELLED},
    TransportStatus.AT_MANDI: {TransportStatus.RETURN_LOAD, TransportStatus.COMPLETED},
    TransportStatus.RETURN_LOAD: {TransportStatus.COMPLETED},
    TransportStatus.COMPLETED: set(),
    TransportStatus.CANCELLED: set(),
}


class RequirementStatus(str, Enum):
    DRAFT = "DRAFT"
    OPEN = "OPEN"
    MATCHING = "MATCHING"
    MATCHED = "MATCHED"
    IN_TRANSIT = "IN_TRANSIT"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


class GeoPoint(BaseModel):
    """A coordinate in the project region, validated on the way in."""

    latitude: float = Field(..., ge=LAT_MIN, le=LAT_MAX)
    longitude: float = Field(..., ge=LON_MIN, le=LON_MAX)

    def to_geojson(self) -> dict:
        # [longitude, latitude] -- GeoJSON order, the reverse of the field order.
        return {"type": "Point", "coordinates": [self.longitude, self.latitude]}


class Quantity(BaseModel):
    """A user-stated quantity plus its normalization, honest about failure.

    ``quantity_kg`` is **null** when the conversion cannot be justified -- most
    often a bori with no determinable bag weight. It is never silently filled
    with an assumed 50 kg, because that propagates into capacity feasibility and
    dispatches the wrong vehicle.
    """

    value: float = Field(..., gt=0, description="As stated by the user")
    unit: QuantityUnit
    quantity_kg: float | None = Field(
        default=None, description="Null when the conversion is unresolved")
    bag_weight_kg_used: float | None = None
    conversion_source: str | None = None
    conversion_confidence: ConversionConfidence = ConversionConfidence.UNRESOLVED

    @property
    def resolved(self) -> bool:
        return self.quantity_kg is not None

    @field_validator("value")
    @classmethod
    def _positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("quantity must be greater than zero")
        return v


class ErrorResponse(BaseModel):
    detail: str
    code: str | None = None
    hint: str | None = None
