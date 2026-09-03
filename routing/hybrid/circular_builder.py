"""Build return-load selection problems from the Phase-A datasets.

Takes a real mandi, a real depot and the synthetic shop replenishment requests
near that mandi, and assembles the reduced decision problem defined in
``circular_qubo``.

Problems are generated with fixed seeds and saved with a manifest so the
benchmark set is reproducible and not silently re-drawn between runs.
"""

from __future__ import annotations

import logging
from functools import lru_cache

import numpy as np
import pandas as pd

from routing.hybrid.circular_qubo import (
    REVENUE_INR_PER_TONNE_KM, CircularProblem, ReturnLoadOption,
    build_synergy_matrix,
)
from vb import config as C
from vb.geo import haversine_km

log = logging.getLogger(__name__)

DETOUR_FACTOR = 1.35
# Objective-unit cost per road kilometre, consistent with the project weights:
# distance 1.0 + fuel 0.010 * (92/5 INR per km) ~= 1.184.
COST_PER_KM = 1.0 + 0.010 * (92.0 / 5.0)


@lru_cache(maxsize=1)
def _tables() -> dict[str, pd.DataFrame]:
    return {
        "locations": pd.read_csv(C.MASTER / "locations_master.csv"),
        "shops": pd.read_csv(C.SYNTHETIC / "shops.csv"),
        "requests": pd.read_csv(C.SYNTHETIC / "transport_requests.csv", low_memory=False),
        "trucks": pd.read_csv(C.SYNTHETIC / "trucks.csv"),
        "mandis": pd.read_csv(C.MASTER / "mandis.csv"),
    }


def build_circular_problem(
    mandi_id: str,
    depot_location_id: str,
    truck_capacity_kg: float,
    *,
    max_options: int = 8,
    max_radius_km: float = 70.0,
    capacity_fraction: float = 0.75,
    seed: int = 0,
    instance_id: str | None = None,
) -> CircularProblem | None:
    """Assemble one return-load decision.

    Args:
        capacity_fraction: Share of the truck still free after the outbound leg.
            Below 1.0 the capacity constraint actually binds, which is what
            makes the knapsack non-trivial.

    Returns None when the mandi has too few nearby shop loads to constitute a
    decision -- a one-option "choice" is not worth benchmarking.
    """
    rng = np.random.default_rng(seed)
    t = _tables()
    loc = t["locations"].set_index("location_id")
    mandis = t["mandis"].set_index("mandi_id")
    if mandi_id not in mandis.index or depot_location_id not in loc.index:
        return None

    mandi_loc_id = mandis.loc[mandi_id, "location_id"]
    if mandi_loc_id not in loc.index:
        return None
    m = loc.loc[mandi_loc_id]
    d = loc.loc[depot_location_id]
    mandi_ll = (float(m["latitude"]), float(m["longitude"]))
    depot_ll = (float(d["latitude"]), float(d["longitude"]))

    shops = t["shops"].set_index("shop_id")
    reqs = t["requests"]
    shop_reqs = reqs[(reqs["requester_type"] == "shop")
                     & reqs["quantity_kg"].notna()
                     & (reqs["feasibility_label"] == "feasible")]

    cap_free = truck_capacity_kg * capacity_fraction

    rows = []
    for _, r in shop_reqs.iterrows():
        sid = r["destination_shop_id"]
        if sid not in shops.index:
            continue
        sloc = shops.loc[sid, "location_id"]
        if sloc not in loc.index:
            continue
        s = loc.loc[sloc]
        s_ll = (float(s["latitude"]), float(s["longitude"]))
        km_from_mandi = haversine_km(*mandi_ll, *s_ll)
        if km_from_mandi > max_radius_km:
            continue
        # A load larger than the free capacity can never be taken; excluding it
        # keeps the qubit budget for decisions that are actually open.
        if float(r["quantity_kg"]) > cap_free:
            continue
        rows.append((sid, r["request_id"], float(r["quantity_kg"]), s_ll, km_from_mandi))
        if len(rows) >= max_options * 4:
            break

    if len(rows) < 3:
        return None

    # Keep a spread of distances rather than the nearest k, so the problem
    # contains both obvious and marginal choices.
    rows.sort(key=lambda x: x[4])
    if len(rows) > max_options:
        idx = np.linspace(0, len(rows) - 1, max_options).astype(int)
        rows = [rows[i] for i in idx]

    base_km = haversine_km(*mandi_ll, *depot_ll) * DETOUR_FACTOR
    options: list[ReturnLoadOption] = []
    for sid, rid, qty, s_ll, km_from_mandi in rows:
        solo_km = (haversine_km(*mandi_ll, *s_ll)
                   + haversine_km(*s_ll, *depot_ll)) * DETOUR_FACTOR
        detour_km = max(solo_km - base_km, 0.0)
        revenue = (qty / 1000.0) * max(km_from_mandi, 1.0) * REVENUE_INR_PER_TONNE_KM
        options.append(ReturnLoadOption(
            load_id=str(rid), shop_id=str(sid), demand_kg=qty,
            solo_detour_cost=detour_km * COST_PER_KM,
            revenue_inr=revenue,
            lat=s_ll[0], lon=s_ll[1], detour_km=detour_km,
        ))

    synergy = build_synergy_matrix(options, mandi_ll, depot_ll,
                                   cost_per_km=COST_PER_KM,
                                   detour_factor=DETOUR_FACTOR)

    return CircularProblem(
        instance_id=instance_id or f"CIRC_{mandi_id}_{seed}",
        mandi_id=mandi_id,
        depot_id=depot_location_id,
        options=options,
        remaining_capacity_kg=cap_free,
        synergy=synergy,
        n_slack=0,  # set by build_circular_qubo
        baseline_empty_cost=base_km * COST_PER_KM,
        notes=[f"{len(rows)} options within {max_radius_km} km of the mandi"],
    )


def build_benchmark_set(
    n_problems: int = 40, seed: int = 20260903, max_options: int = 8,
) -> list[CircularProblem]:
    """A reproducible, deliberately varied set of return-load problems.

    Capacity fraction is varied across problems so the set spans cases where
    capacity binds hard and cases where it barely binds. Duplicating one
    scenario 40 times would inflate the count without adding information.
    """
    rng = np.random.default_rng(seed)
    t = _tables()
    loc = t["locations"]
    depots = loc[loc["location_type"] == "depot"]
    mandis = t["mandis"]
    trucks = t["trucks"]

    problems: list[CircularProblem] = []
    attempts = 0
    while len(problems) < n_problems and attempts < n_problems * 12:
        attempts += 1
        mrow = mandis.iloc[int(rng.integers(0, len(mandis)))]
        mloc = loc[loc["location_id"] == mrow["location_id"]]
        if mloc.empty:
            continue
        district = mloc.iloc[0]["district"]
        dep = depots[depots["district"] == district]
        if dep.empty:
            continue
        tr = trucks[trucks["district"] == district]
        if tr.empty:
            tr = trucks
        truck = tr.iloc[int(rng.integers(0, len(tr)))]

        p = build_circular_problem(
            mrow["mandi_id"], dep.iloc[0]["location_id"],
            float(truck["capacity_kg"]),
            max_options=max_options,
            capacity_fraction=float(rng.uniform(0.35, 0.85)),
            seed=int(rng.integers(0, 10 ** 6)),
            instance_id=f"CIRC_{len(problems):03d}_{mrow['mandi_id']}",
        )
        if p is not None and p.n_options >= 4:
            problems.append(p)
    return problems
