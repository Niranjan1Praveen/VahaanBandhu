"""Quantity normalization at the application boundary.

Wraps the the routing research converter so the API preserves its central rule:

    **A bori with no determinable bag weight does NOT become 50 kg.**

It becomes `quantity_kg = None` with confidence `unresolved`, and the API asks
the user to clarify rather than dispatching a wrongly-sized truck. A 20-bori
paddy load assumed at 50 kg/bori is overstated by 25%, which propagates straight
into capacity feasibility.
"""

from __future__ import annotations

from server.app.schemas.common import ConversionConfidence, Quantity, QuantityUnit


def normalize_quantity(value: float, unit: QuantityUnit,
                       crop_key: str | None = None) -> Quantity:
    """Convert to kg where defensible; leave null where it is not."""
    from vb.enums import Unit as VbUnit
    from vb.units import normalize as vb_normalize

    q = vb_normalize(value, VbUnit(unit.value), crop_key)
    return Quantity(
        value=value,
        unit=unit,
        quantity_kg=q.kg,
        bag_weight_kg_used=q.bag_weight_kg_used,
        conversion_source=q.conversion_source,
        conversion_confidence=ConversionConfidence(q.conversion_confidence.value),
    )


def clarification_needed(q: Quantity) -> str | None:
    """A Hindi prompt when the quantity cannot be resolved, else None.

    The UI shows this instead of silently proceeding. Asking one extra question
    is far cheaper than sending the wrong vehicle.
    """
    if q.resolved:
        return None
    if q.unit is QuantityUnit.BORI:
        return ("एक बोरी का वज़न फसल के अनुसार बदलता है। "
                "कृपया बताएं कि एक बोरी में कितने किलो हैं?")
    return "कृपया मात्रा दोबारा जांचें।"


def fits_capacity(q: Quantity, capacity_kg: float) -> bool | None:
    """None when unresolved — an unknown load is not a load that fits."""
    if q.quantity_kg is None:
        return None
    return q.quantity_kg <= capacity_kg
