"""Canonical route evaluation.

**Every solver in a benchmark must be scored by this module and nothing else.**

The previous benchmark compared TSP heuristics on raw tour distance while
OR-Tools reported a weighted objective. Those numbers were never comparable,
and the resulting "everything ties at optimal" table said nothing. A single
evaluator fixes that: given an instance and a set of routes, it computes every
cost component from the instance's own matrices and applies the instance's own
``objective_weights``.

A solution is a list of routes; each route is a list of node indices starting
and ending at the depot.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

import numpy as np

from routing.models import RoutingInstance


@dataclass
class RouteEvaluation:
    """Full cost breakdown of a candidate solution."""

    objective: float
    distance_km: float
    time_min: float
    toll_inr: float
    fuel_inr: float
    risk: float
    empty_km: float
    loaded_km: float
    circular_score: float
    capacity_utilization: float
    feasible: bool
    violations: list[str] = field(default_factory=list)
    n_routes: int = 0
    n_served: int = 0
    terms: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


def _component(matrix: np.ndarray | None, i: int, j: int, default: float = 0.0) -> float:
    return float(matrix[i, j]) if matrix is not None else default


def evaluate(
    inst: RoutingInstance,
    routes: list[list[int]],
    *,
    weights: dict[str, float] | None = None,
    circular_score: float = 0.0,
) -> RouteEvaluation:
    """Score a solution against the instance's own cost data and weights.

    Args:
        routes: Each route is a list of node indices. A leading/trailing depot
            is optional and normalized here.
        circular_score: Return-load benefit, supplied by the caller because it
            depends on loads outside the instance graph.

    Feasibility covers: every customer served exactly once, capacity per route,
    and time windows where the instance declares them. A violation makes the
    solution infeasible but the cost is still reported, so a near-miss can be
    inspected rather than vanishing.
    """
    w = {**inst.objective_weights, **(weights or {})}
    D, T = inst.distance_matrix, inst.time_matrix
    depot = inst.depot_index

    total_km = total_min = total_toll = total_fuel = 0.0
    risk_accum: list[float] = []
    empty_km = loaded_km = 0.0
    violations: list[str] = []
    served: list[int] = []
    peak_utilisation: list[float] = []

    capacities = list(inst.vehicle_capacities)

    for r_idx, raw in enumerate(routes):
        route = [n for n in raw]
        if not route:
            continue
        if route[0] != depot:
            route = [depot] + route
        if route[-1] != depot:
            route = route + [depot]
        if len(route) <= 2:
            continue  # depot -> depot, an unused vehicle

        cap = capacities[r_idx] if r_idx < len(capacities) else capacities[-1]
        load = float(sum(inst.demands[n] for n in route))
        if load > cap + 1e-6:
            violations.append(f"route_{r_idx}_over_capacity")
        peak_utilisation.append(load / cap if cap else 0.0)

        # Remaining load determines whether a leg runs loaded or empty. We treat
        # the tour as a collection run: the truck fills up as it visits nodes and
        # the final leg back to the depot is the only guaranteed-loaded one.
        # Legs before the first pickup are empty running.
        picked = 0.0
        for a, b in zip(route[:-1], route[1:]):
            leg_km = float(D[a, b])
            total_km += leg_km
            total_min += float(T[a, b])
            total_toll += _component(inst.toll_matrix, a, b)
            total_fuel += _component(inst.fuel_matrix, a, b,
                                     default=leg_km / 5.0 * 92.0)
            risk_accum.append(_component(inst.risk_matrix, a, b))
            if picked <= 1e-9:
                empty_km += leg_km
            else:
                loaded_km += leg_km
            picked += float(inst.demands[b])

        served.extend(n for n in route if n != depot)

    # Coverage: every customer exactly once.
    customers = [i for i in range(inst.n_nodes) if i != depot]
    counts = {c: served.count(c) for c in customers}
    missing = [c for c, k in counts.items() if k == 0]
    duplicated = [c for c, k in counts.items() if k > 1]
    if missing:
        violations.append(f"unserved_customers:{len(missing)}")
    if duplicated:
        violations.append(f"duplicated_customers:{len(duplicated)}")

    # Time windows, where the instance declares them.
    if inst.time_windows:
        for r_idx, raw in enumerate(routes):
            route = [n for n in raw if n != depot]
            if not route:
                continue
            clock = inst.time_windows[depot][0]
            prev = depot
            for n in route:
                clock += float(T[prev, n])
                start, end = inst.time_windows[n]
                if clock < start:
                    clock = start  # wait; not a violation
                elif clock > end:
                    violations.append(f"route_{r_idx}_node_{n}_late")
                prev = n

    mean_risk = float(np.mean(risk_accum)) if risk_accum else 0.0

    terms = {
        "distance_km": w.get("distance_km", 1.0) * total_km,
        "time_min": w.get("time_min", 0.0) * total_min,
        "fuel_inr": w.get("fuel_inr", 0.0) * total_fuel,
        "toll_inr": w.get("toll_inr", 0.0) * total_toll,
        "risk": w.get("risk", 0.0) * mean_risk,
        "empty_km": w.get("empty_km", 0.0) * empty_km,
        "circular_bonus": w.get("circular_bonus", 0.0) * circular_score,
    }

    return RouteEvaluation(
        objective=float(sum(terms.values())),
        distance_km=round(total_km, 4),
        time_min=round(total_min, 3),
        toll_inr=round(total_toll, 3),
        fuel_inr=round(total_fuel, 3),
        risk=round(mean_risk, 5),
        empty_km=round(empty_km, 4),
        loaded_km=round(loaded_km, 4),
        circular_score=round(circular_score, 5),
        capacity_utilization=round(float(np.mean(peak_utilisation)), 4)
        if peak_utilisation else 0.0,
        feasible=not violations,
        violations=violations,
        n_routes=len([r for r in routes if len(r) > 2]),
        n_served=len(set(served)),
        terms={k: round(v, 5) for k, v in terms.items()},
    )


def tour_to_routes(tour: list[int], depot: int = 0) -> list[list[int]]:
    """Normalize a single TSP tour into the routes-list form ``evaluate`` takes."""
    if not tour:
        return []
    if depot in tour:
        k = tour.index(depot)
        tour = tour[k:] + tour[:k]
    return [list(tour) + [depot]]


def improvement(base: float, candidate: float) -> float:
    """Relative improvement of candidate over base. Positive means better."""
    if base == 0 or not np.isfinite(base) or not np.isfinite(candidate):
        return 0.0
    return (base - candidate) / abs(base)
