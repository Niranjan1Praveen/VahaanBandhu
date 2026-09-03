"""Frozen controlled vocabularies for VahaanBandhu 2.0.

These are the ontology. Changing a member is a breaking schema change and
requires a dataset version bump.
"""

from __future__ import annotations

from enum import Enum


class StrEnum(str, Enum):
    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.value

    @classmethod
    def values(cls) -> list[str]:
        return [m.value for m in cls]


class LocationType(StrEnum):
    VILLAGE = "village"
    MANDI = "mandi"
    SHOP = "shop"
    DEPOT = "depot"
    PARKING = "parking"
    HUB = "hub"
    WAREHOUSE = "warehouse"


class GeocodePrecision(StrEnum):
    """How tightly a coordinate is pinned to the real-world object."""

    EXACT = "exact"
    ROOFTOP = "rooftop"
    STREET = "street"
    SETTLEMENT = "settlement"
    DISTRICT_CENTROID = "district_centroid"
    SYNTHETIC_ENVELOPE = "synthetic_envelope"
    UNKNOWN = "unknown"


class MarketYardType(StrEnum):
    MAIN = "main"
    SUB_YARD = "sub-yard"
    PRIVATE = "private"
    OTHER = "other"


class ShopCategory(StrEnum):
    CEMENT = "cement"
    TMT = "tmt"
    HARDWARE = "hardware"
    BRICK = "brick"
    PIPE = "pipe"
    ELECTRICAL = "electrical"
    PAINT = "paint"
    TILE = "tile"
    SANITARY = "sanitary"
    ROOFING = "roofing"
    MULTI = "multi"


class VehicleAccess(StrEnum):
    LCV = "LCV"
    TWO_AXLE = "2-axle"
    THREE_AXLE = "3-axle"
    HEAVY = "heavy"


class VehicleClass(StrEnum):
    PICKUP = "pickup"
    LCV = "LCV"
    TWO_AXLE = "2axle"
    THREE_AXLE = "3axle"
    MULTI_AXLE = "multi_axle"


class BodyType(StrEnum):
    OPEN = "open"
    CLOSED = "closed"
    REFRIGERATED = "refrigerated"
    TIPPER = "tipper"


class FuelType(StrEnum):
    DIESEL = "diesel"
    CNG = "cng"
    EV = "ev"
    OTHER = "other"


class Unit(StrEnum):
    KG = "kg"
    BORI = "bori"
    QUINTAL = "quintal"
    TONNE = "tonne"


class Season(StrEnum):
    KHARIF = "kharif"
    RABI = "rabi"
    ZAID = "zaid"
    PERENNIAL = "perennial"


class InputLanguage(StrEnum):
    HI = "hi"
    EN = "en"
    HINGLISH = "hinglish"


class InputMode(StrEnum):
    VOICE = "voice"
    TEXT = "text"


class RequesterType(StrEnum):
    FARMER = "farmer"
    SHOP = "shop"


class AlgorithmFamily(StrEnum):
    CLASSICAL = "classical"
    QUANTUM = "quantum"
    HYBRID = "hybrid"


class ConversionConfidence(StrEnum):
    """Trust level of a unit -> kg conversion."""

    EXACT = "exact"
    CROP_DEFAULT = "crop_default"
    REGIONAL_DEFAULT = "regional_default"
    UNRESOLVED = "unresolved"


class Volatility(StrEnum):
    """How long a cached optimization artifact stays valid."""

    STATIC = "static"
    SEMI_STATIC = "semi_static"
    DYNAMIC = "dynamic"
