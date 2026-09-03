"""Circular logistics: turning empty return running into revenue.

The core inefficiency VahaanBandhu targets: a truck carries grain from a
village to a mandi, then drives home empty. If a building-material load is
waiting near that mandi and headed back toward the truck's home corridor, the
same distance earns twice.

This module quantifies that. The scoring is deliberately conservative -- a
return load only counts if the detour to collect it is small relative to the
empty distance it replaces, because a "return load" 80 km off the homeward path
is just a second trip.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from vb.geo import haversine_km

DIESEL_PRICE_INR_PER_L = 92.0
# Diesel truck CO2, kg per litre burned. Used only as a relative comparison
# proxy between routes, never reported as a certified emissions figure.
CO2_KG_PER_LITRE = 2.68


@dataclass
class CircularEvaluation:
    """Side-by-side comparison of a trip with and without a return load."""

    forward_loaded_km: float
    return_loaded_km: float
    empty_km: float
    total_km: float
    detour_km: float
    truck_utilization: float
    capacity_utilization_return: float
    fuel_litres: float
    fuel_cost_inr: float
    co2_proxy_kg: float
    avoided_empty_km: float
    circular_score: float
    worthwhile: bool
    reason: str

    def to_dict(self) -> dict:
        return self.__dict__.copy()


def evaluate_direct_trip(
    origin: tuple[float, float], mandi: tuple[float, float],
    home: tuple[float, float], kmpl: float, capacity_kg: float, load_kg: float,
    detour_factor: float = 1.35,
) -> CircularEvaluation:
    """Baseline: village -> mandi -> home empty."""
    loaded = haversine_km(*origin, *mandi) * detour_factor
    empty = haversine_km(*mandi, *home) * detour_factor
    total = loaded + empty
    litres = total / kmpl
    return CircularEvaluation(
        forward_loaded_km=round(loaded, 2),
        return_loaded_km=0.0,
        empty_km=round(empty, 2),
        total_km=round(total, 2),
        detour_km=0.0,
        truck_utilization=round(loaded / total if total else 0.0, 4),
        capacity_utilization_return=0.0,
        fuel_litres=round(litres, 2),
        fuel_cost_inr=round(litres * DIESEL_PRICE_INR_PER_L, 2),
        co2_proxy_kg=round(litres * CO2_KG_PER_LITRE, 2),
        avoided_empty_km=0.0,
        circular_score=0.0,
        worthwhile=False,
        reason="no return load considered",
    )


def evaluate_circular_trip(
    origin: tuple[float, float], mandi: tuple[float, float],
    supplier: tuple[float, float], shop: tuple[float, float],
    home: tuple[float, float], kmpl: float, capacity_kg: float,
    forward_load_kg: float, return_load_kg: float,
    detour_factor: float = 1.35,
    max_detour_ratio: float = 0.45,
) -> CircularEvaluation:
    """village -> mandi -> supplier -> shop -> home.

    Args:
        max_detour_ratio: A return load is only worth taking if the extra
            distance is under this fraction of the empty distance it replaces.
            Above it, the "return load" is really a separate job and should be
            priced as one.
    """
    forward = haversine_km(*origin, *mandi) * detour_factor
    baseline_empty = haversine_km(*mandi, *home) * detour_factor

    leg_supplier = haversine_km(*mandi, *supplier) * detour_factor
    leg_shop = haversine_km(*supplier, *shop) * detour_factor
    leg_home = haversine_km(*shop, *home) * detour_factor

    return_loaded = leg_shop
    empty = leg_supplier + leg_home
    total = forward + leg_supplier + leg_shop + leg_home
    detour = total - (forward + baseline_empty)

    litres = total / kmpl
    avoided_empty = max(baseline_empty - empty, 0.0)

    detour_ratio = detour / baseline_empty if baseline_empty > 0 else np.inf
    worthwhile = detour_ratio <= max_detour_ratio and return_load_kg > 0

    # Score rewards loaded share and the empty distance displaced, and is
    # zeroed when the detour is not worth it -- so the objective function can
    # never be talked into a bad return load by a large raw tonnage.
    loaded_share = (forward + return_loaded) / total if total else 0.0
    cap_util = min(return_load_kg / capacity_kg, 1.0) if capacity_kg else 0.0
    score = round(loaded_share * cap_util * (1.0 + avoided_empty / max(total, 1e-9)), 4) \
        if worthwhile else 0.0

    return CircularEvaluation(
        forward_loaded_km=round(forward, 2),
        return_loaded_km=round(return_loaded, 2),
        empty_km=round(empty, 2),
        total_km=round(total, 2),
        detour_km=round(detour, 2),
        truck_utilization=round(loaded_share, 4),
        capacity_utilization_return=round(cap_util, 4),
        fuel_litres=round(litres, 2),
        fuel_cost_inr=round(litres * DIESEL_PRICE_INR_PER_L, 2),
        co2_proxy_kg=round(litres * CO2_KG_PER_LITRE, 2),
        avoided_empty_km=round(avoided_empty, 2),
        circular_score=score,
        worthwhile=worthwhile,
        reason=(
            f"detour {detour:.1f} km is {detour_ratio:.0%} of the {baseline_empty:.1f} km "
            f"empty leg it replaces"
            + ("" if worthwhile else f" -- above the {max_detour_ratio:.0%} threshold")
        ),
    )


def find_return_loads(
    mandi_latlon: tuple[float, float],
    home_latlon: tuple[float, float],
    shop_requests: pd.DataFrame,
    shop_locations: pd.DataFrame,
    remaining_capacity_kg: float,
    max_radius_km: float = 60.0,
    top_k: int = 5,
) -> pd.DataFrame:
    """Candidate return loads near a mandi and roughly homeward.

    "Roughly homeward" is the important filter: a shop 40 km from the mandi in
    the wrong direction adds 80 km, not 40. Candidates are scored on how much
    of the journey they share with the direction of travel.
    """
    if shop_requests.empty:
        return shop_requests

    locs = shop_locations.set_index("shop_id") if "shop_id" in shop_locations else None
    rows = []
    home_bearing_km = haversine_km(*mandi_latlon, *home_latlon)

    for _, r in shop_requests.iterrows():
        if pd.isna(r.get("quantity_kg")) or r["quantity_kg"] > remaining_capacity_kg:
            continue
        shop_id = r.get("destination_shop_id")
        if locs is None or shop_id not in locs.index:
            continue
        sl = locs.loc[shop_id]
        shop_ll = (float(sl["latitude"]), float(sl["longitude"]))

        d_mandi = haversine_km(*mandi_latlon, *shop_ll)
        if d_mandi > max_radius_km:
            continue
        d_home = haversine_km(*shop_ll, *home_latlon)
        # Detour over simply driving mandi -> home.
        detour = (d_mandi + d_home) - home_bearing_km

        rows.append({
            "request_id": r["request_id"],
            "shop_id": shop_id,
            "quantity_kg": float(r["quantity_kg"]),
            "km_from_mandi": round(d_mandi, 2),
            "km_shop_to_home": round(d_home, 2),
            "detour_km": round(detour, 2),
            "capacity_fit": round(r["quantity_kg"] / remaining_capacity_kg, 3),
            # Prefer big loads with small detours.
            "return_load_score": round(
                (r["quantity_kg"] / remaining_capacity_kg) / (1.0 + detour / 10.0), 4),
        })

    if not rows:
        return pd.DataFrame(columns=["request_id", "shop_id", "return_load_score"])
    return pd.DataFrame(rows).sort_values("return_load_score", ascending=False).head(top_k)
