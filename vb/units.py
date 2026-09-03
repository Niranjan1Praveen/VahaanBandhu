"""Quantity normalization.

The one rule that matters here: **never silently fabricate a kilogram value.**

kg, quintal and tonne are exact, definition-level conversions. ``bori`` is not
a unit of mass at all -- it is a sack whose fill weight depends on the crop,
the packaging and local mandi practice. A global "1 bori = 50 kg" assumption is
wrong often enough to corrupt capacity feasibility checks, so a bori quantity
converts only when we have a defensible bag weight, and otherwise resolves to
``None`` with confidence ``unresolved``.
"""

from __future__ import annotations

from dataclasses import dataclass

from vb.enums import ConversionConfidence, Unit
from vb.reference.crops import BY_KEY as CROPS_BY_KEY

EXACT_TO_KG: dict[Unit, float] = {
    Unit.KG: 1.0,
    Unit.QUINTAL: 100.0,
    Unit.TONNE: 1000.0,
}

# Fallback bag weights by handling class, used only when the specific crop is
# unknown but its family is. Deliberately coarser confidence than a crop match.
CLASS_BAG_WEIGHT_KG: dict[str, float] = {
    "granular_bagged": 50.0,
    "pulse_bagged": 50.0,
    "oilseed_bagged": 50.0,
    "perishable_bagged": 50.0,
    "perishable_crate": 25.0,
}


@dataclass(frozen=True)
class Quantity:
    """A normalized quantity that is honest about what it does not know."""

    value: float
    unit: Unit
    kg: float | None
    bag_weight_kg_used: float | None
    conversion_source: str
    conversion_confidence: ConversionConfidence

    @property
    def resolved(self) -> bool:
        return self.kg is not None


def normalize(
    value: float,
    unit: Unit | str,
    crop_key: str | None = None,
    handling_class: str | None = None,
) -> Quantity:
    """Convert a user-stated quantity to kilograms where that is defensible.

    Args:
        value: The number the user gave. Must be > 0 to resolve.
        unit: One of the four supported units.
        crop_key: Canonical crop key, if the parser resolved one. Required for
            a high-confidence bori conversion.
        handling_class: Fallback crop family when the exact crop is unknown.

    Returns:
        A Quantity. ``kg is None`` means the conversion is genuinely unresolved
        and downstream code must treat the load as unsized, not as zero.
    """
    unit = Unit(unit)

    if value is None or value <= 0:
        return Quantity(
            value=value, unit=unit, kg=None, bag_weight_kg_used=None,
            conversion_source="invalid_quantity",
            conversion_confidence=ConversionConfidence.UNRESOLVED,
        )

    if unit in EXACT_TO_KG:
        return Quantity(
            value=value, unit=unit, kg=value * EXACT_TO_KG[unit],
            bag_weight_kg_used=None,
            conversion_source="definitional",
            conversion_confidence=ConversionConfidence.EXACT,
        )

    # unit is BORI from here on.
    crop = CROPS_BY_KEY.get(crop_key) if crop_key else None
    if crop is not None and crop.default_bag_weight_kg is not None:
        bw = crop.default_bag_weight_kg
        return Quantity(
            value=value, unit=unit, kg=value * bw, bag_weight_kg_used=bw,
            conversion_source=f"crop_default:{crop.key}",
            conversion_confidence=ConversionConfidence.CROP_DEFAULT,
        )

    hc = handling_class or (crop.handling_class if crop else None)
    if hc in CLASS_BAG_WEIGHT_KG:
        bw = CLASS_BAG_WEIGHT_KG[hc]
        return Quantity(
            value=value, unit=unit, kg=value * bw, bag_weight_kg_used=bw,
            conversion_source=f"handling_class_default:{hc}",
            conversion_confidence=ConversionConfidence.REGIONAL_DEFAULT,
        )

    # Bori with no crop and no family: we genuinely do not know the fill weight.
    return Quantity(
        value=value, unit=unit, kg=None, bag_weight_kg_used=None,
        conversion_source="no_bag_weight_available",
        conversion_confidence=ConversionConfidence.UNRESOLVED,
    )


def fits_vehicle(quantity: Quantity, capacity_kg: float) -> bool | None:
    """Capacity feasibility. Returns None when the quantity is unresolved --
    an unknown load is not the same as a load that fits."""
    if quantity.kg is None:
        return None
    return quantity.kg <= capacity_kg
