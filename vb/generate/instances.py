"""Optimization instance construction.

An *instance* is the canonical, solver-agnostic statement of one routing
problem: a depot, a set of service nodes, demands, capacities, time windows and
an objective definition, pinned to one cost snapshot.

This is the contract that makes classical/quantum comparison honest. Every
solver -- Dijkstra, OR-Tools, a QUBO, QAOA on hardware -- consumes the same
``instance_id`` and the same ``cost_snapshot_id``. Nothing may re-derive its own
distance matrix.

Instances are sized in bands, because the quantum track can only encode small
problems. The ``quantum_ready`` flag marks instances whose node count keeps the
QUBO within a qubit budget that a simulator, and occasionally real hardware,
can actually run.
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd

from vb.generate.graph import BASELINE_SCENARIO, cost_snapshot_id
from vb.ids import content_id, instance_hash

GRAPH_VERSION = "g1"

# Default multi-objective weights. Kept in data, never buried in solver code,
# so an experiment can vary them and record what it used.
DEFAULT_OBJECTIVE_WEIGHTS = {
    "distance_km": 1.0,
    "time_min": 0.35,
    "fuel_inr": 0.010,
    "toll_inr": 0.010,
    "risk": 12.0,
    "empty_km": 0.85,          # penalty on unloaded running
    "circular_bonus": -1.10,   # negative: a return load improves the objective
}

PROBLEM_TYPES = ("TSP", "CVRP", "VRPTW", "PDP", "CIRCULAR_VRP")

# Node-count bands. The quantum band is deliberately tiny: a naive
# permutation-encoded TSP needs n^2 binary variables, so 6 nodes is 36 qubits
# and 8 nodes is 64 -- already past what current hardware runs meaningfully.
BANDS = {
    "quantum": (3, 7),
    "small": (8, 14),
    "medium": (15, 30),
    "large": (31, 60),
}
# Above this many service nodes, a permutation QUBO is not encodable in any
# honest sense. Measured, not guessed: with the depot, c customers give c+1
# nodes and (c+1)^2 qubits. At c=3 that is 16 qubits (fine); at c=4 it is 25
# (~537 MB of statevector); at c=6 it is 49, which is 2^49 amplitudes and
# simply cannot be simulated. The wider `quantum` size band is retained for the
# edge-selection encoding, which scales with edges rather than nodes squared.
QUANTUM_NODE_CEILING = 3


def build_route_instances(
    cfg,
    requests: pd.DataFrame,
    trucks: pd.DataFrame,
    locations: pd.DataFrame,
    depots: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (route_instances, instance_requests junction).

    Request lists are held in a junction table rather than a delimited cell, so
    foreign keys can actually be validated.
    """
    rng = np.random.default_rng(cfg.seed + 101)

    # Only servable requests become instances. Infeasible and unresolved rows
    # stay in the request corpus as labelled hard negatives for the parser and
    # the matcher -- they are not silently dropped, but they are not routed.
    servable = requests[
        (requests["feasibility_label"] == "feasible")
        & requests["quantity_kg"].notna()
        & (requests["quantity_kg"] > 0)
    ].copy()
    if servable.empty:
        raise ValueError("no servable requests: check quantity normalization")

    loc_district = dict(zip(locations["location_id"], locations["district"]))
    n_instances = cfg.sizes.n_route_instances
    n_quantum = cfg.sizes.n_quantum_instances

    # District-local instances: a real truck serves one neighbourhood, not four
    # states. Grouping by district also makes the held-out-district split
    # meaningful, since an instance belongs to exactly one district.
    by_district = {d: g for d, g in servable.groupby("district") if len(g) >= 4}
    if not by_district:
        raise ValueError("no district has enough servable requests")
    districts = list(by_district)

    trucks_by_district = {d: g for d, g in trucks.groupby("district")}

    inst_rows, junction_rows = [], []
    snapshot = cost_snapshot_id(BASELINE_SCENARIO, cfg.dataset_version, GRAPH_VERSION)
    weights_json = json.dumps(DEFAULT_OBJECTIVE_WEIGHTS, sort_keys=True)

    for i in range(n_instances):
        d = districts[int(rng.integers(0, len(districts)))]
        pool = by_district[d]

        # First n_quantum instances are drawn small so the quantum track has a
        # canonical, non-cherry-picked subset to work with.
        if i < n_quantum:
            band = "quantum"
        else:
            band = str(rng.choice(["small", "medium", "large"], p=[0.45, 0.40, 0.15]))
        lo, hi = BANDS[band]
        # A district may not have enough servable requests for the drawn band;
        # shrink to what is available rather than fabricating nodes.
        hi = min(hi, len(pool))
        lo = min(lo, hi)
        if hi < 2:
            continue
        n_nodes = int(rng.integers(lo, hi + 1))

        # A single-vehicle quantum instance can only be feasible if its loads are
        # small, so draw those nodes from the light end of the district's
        # requests rather than rejecting instances after the fact.
        draw_pool = pool
        if band == "quantum":
            light = pool[pool["quantity_kg"] <= pool["quantity_kg"].quantile(0.35)]
            if len(light) >= n_nodes:
                draw_pool = light
            n_nodes = min(n_nodes, len(draw_pool))
            if n_nodes < 2:
                continue

        picks = draw_pool.iloc[rng.choice(len(draw_pool), size=n_nodes, replace=False)]
        demands = picks["quantity_kg"].astype(float).tolist()

        # Prefer local trucks, but a thin district fleet must not make an
        # otherwise-valid instance unservable -- fall back to the wider fleet.
        truck_pool = trucks_by_district.get(d, trucks)
        if truck_pool["capacity_kg"].sum() < float(sum(demands)):
            truck_pool = trucks
        # Size the fleet to the load. Drawing a vehicle count at random produced
        # instances whose demand exceeded fleet capacity ~99% of the time, which
        # makes every benchmark trivially infeasible. Instead, assign the largest
        # trucks available and add vehicles until the load fits (plus one spare
        # so the solver has a real assignment choice rather than a forced one).
        total_demand = float(sum(demands))
        ranked = truck_pool.sort_values("capacity_kg", ascending=False)
        cum = ranked["capacity_kg"].cumsum().to_numpy()
        need = int(np.searchsorted(cum, total_demand) + 1)
        # No artificial fleet cap beyond the quantum band. A 40-stop mandi-day
        # aggregation genuinely needs a dozen-plus trucks; capping it at 6 just
        # manufactured infeasible instances.
        max_vehicles = 1 if band == "quantum" else 25
        n_vehicles = int(np.clip(need + (0 if band == "quantum" else 1),
                                 1, min(max_vehicles, len(ranked))))
        chosen_trucks = ranked.iloc[:n_vehicles]
        capacity = float(chosen_trucks["capacity_kg"].min())

        depot_pool = depots[depots["district"] == d]
        depot_id = (depot_pool.iloc[0]["location_id"] if len(depot_pool)
                    else depots.iloc[0]["location_id"])

        has_tw = bool(rng.random() < 0.6)
        has_pd = bool(rng.random() < 0.35)
        circular = bool(rng.random() < 0.45)

        if n_nodes <= 3 and n_vehicles == 1:
            problem = "TSP"
        elif has_pd:
            problem = "PDP"
        elif circular:
            problem = "CIRCULAR_VRP"
        elif has_tw:
            problem = "VRPTW"
        else:
            problem = "CVRP"

        node_ids = picks["request_id"].tolist()
        ihash = instance_hash(node_ids, demands, capacity)
        instance_id = content_id("instance", d, ihash, i)

        # Feasibility guard: an instance whose total demand cannot fit in the
        # assigned fleet is unsolvable and would pollute benchmark statistics.
        fleet_capacity = float(chosen_trucks["capacity_kg"].sum())
        capacity_feasible = total_demand <= fleet_capacity

        inst_rows.append({
            "instance_id": instance_id,
            "instance_hash": ihash,
            "problem_type": problem,
            "size_band": band,
            "depot_location_id": depot_id,
            "district": d,
            "state_code": picks.iloc[0]["state_code"],
            "n_customers": n_nodes,
            "n_vehicles": n_vehicles,
            "truck_ids": "|".join(chosen_trucks["truck_id"].tolist()),
            "capacity_constraint": capacity,
            "fleet_capacity_kg": fleet_capacity,
            "total_demand_kg": round(total_demand, 1),
            "capacity_feasible": capacity_feasible,
            "time_window_constraint": has_tw,
            "pickup_delivery_constraint": has_pd,
            "circular_return_constraint": circular,
            "objective_weights_json": weights_json,
            "cost_snapshot_id": snapshot,
            "scenario_id": BASELINE_SCENARIO,
            "graph_version": GRAPH_VERSION,
            "quantum_ready": n_nodes <= QUANTUM_NODE_CEILING and n_vehicles == 1,
            # Includes the depot, which the permutation encoding must also place.
            "estimated_qubits_permutation": (n_nodes + 1) ** 2,
            "split": pd.NA,  # assigned later by vb.splits
            "seed": cfg.seed,
            "dataset_version": cfg.dataset_version,
        })
        for order, rid in enumerate(node_ids):
            junction_rows.append({
                "instance_id": instance_id,
                "request_id": rid,
                "node_order": order,
                "demand_kg": float(picks.iloc[order]["quantity_kg"]),
                "dataset_version": cfg.dataset_version,
            })

    return pd.DataFrame(inst_rows), pd.DataFrame(junction_rows)
