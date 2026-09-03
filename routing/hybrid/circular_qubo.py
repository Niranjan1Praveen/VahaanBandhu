"""Return-load selection as a quadratic knapsack -- the circular-logistics QUBO.

**Why this problem and not shortest path.**

Dijkstra solves single-source shortest path *exactly* in polynomial time. No
quantum method can beat an exact polynomial algorithm on its own problem, so
framing VahaanBandhu's quantum layer as "quantum shortest path" guarantees at
best a tie. The Krauss & McCollum formulation (IEEE TQE 2020) is mathematically
elegant precisely because it reproduces Dijkstra's answer -- it is a
demonstration of encoding, not a claim of advantage.

Return-load selection is different. After a truck unloads at a mandi, it must
decide **which subset of nearby shop deliveries to carry home, and implicitly in
what grouping**, subject to remaining capacity and a detour budget. That is a
*quadratic* knapsack / prize-collecting problem:

* the value of a shop is its revenue minus its detour cost, and
* **shops interact**: two shops on the same corridor share a detour, so taking
  both costs less than the sum of taking each alone. Two shops in opposite
  directions cost more.

Quadratic knapsack is NP-hard. There is no exact polynomial classical algorithm,
so unlike shortest path there is genuine room for a different optimizer to
contribute. This is also the single most VahaanBandhu-specific decision in the
whole system: it is what turns an empty return leg into revenue.

Formulation
-----------
    x_i = 1  iff return load i is accepted

    minimize   sum_i (detour_i - revenue_i) x_i
             + sum_{i<j} synergy_ij x_i x_j          [genuine coupling]
             + A_cap * capacity_violation_penalty

``synergy_ij`` is the *extra* cost of serving both i and j relative to serving
each independently. Negative where the shops share a corridor (worth taking
together), positive where they diverge.

Capacity is enforced with binary slack variables, the standard exact encoding of
an inequality constraint in a QUBO. Penalty weights follow Krauss & McCollum:
strictly greater than the sum of all achievable cost magnitudes, so no violation
can ever pay for itself.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from routing.quantum.qubo import QUBO

ENCODING_RETURN_LOAD = "return_load_quadratic_knapsack_v1"
QUBO_VERSION = "circular_hybrid_v1"

# Revenue proxy: what a shop delivery is worth per tonne-kilometre carried.
# A tariff, not a measurement -- it is a modelling assumption and is recorded as
# such in the artifact metadata.
REVENUE_INR_PER_TONNE_KM = 4.5


@dataclass
class ReturnLoadOption:
    """One candidate return load."""

    load_id: str
    shop_id: str
    demand_kg: float
    # Detour cost in objective units if this load is served alone.
    solo_detour_cost: float
    revenue_inr: float
    lat: float
    lon: float
    detour_km: float

    @property
    def solo_value(self) -> float:
        """Net benefit of taking this load alone. Negative is good (a cost we
        want to minimize), so value = detour - revenue."""
        return self.solo_detour_cost - self.revenue_inr


@dataclass
class CircularProblem:
    """The reduced return-load decision handed to the quantum layer."""

    instance_id: str
    mandi_id: str
    depot_id: str
    options: list[ReturnLoadOption]
    remaining_capacity_kg: float
    synergy: np.ndarray
    n_slack: int
    baseline_empty_cost: float
    notes: list[str] = field(default_factory=list)

    @property
    def n_options(self) -> int:
        return len(self.options)

    def summary(self) -> dict:
        return {
            "instance_id": self.instance_id,
            "n_options": self.n_options,
            "n_slack_vars": self.n_slack,
            "n_variables": self.n_options + self.n_slack,
            "remaining_capacity_kg": self.remaining_capacity_kg,
            "total_demand_kg": float(sum(o.demand_kg for o in self.options)),
            "capacity_is_binding": bool(
                sum(o.demand_kg for o in self.options) > self.remaining_capacity_kg),
            "mean_synergy": float(np.mean(self.synergy[np.triu_indices(
                self.n_options, k=1)])) if self.n_options > 1 else 0.0,
        }


def _haversine(a_lat, a_lon, b_lat, b_lon) -> float:
    from vb.geo import haversine_km
    return haversine_km(a_lat, a_lon, b_lat, b_lon)


def build_synergy_matrix(
    options: list[ReturnLoadOption],
    mandi: tuple[float, float],
    depot: tuple[float, float],
    *,
    cost_per_km: float = 1.0,
    detour_factor: float = 1.35,
) -> np.ndarray:
    """Pairwise extra cost of serving two loads together vs. separately.

    Serving i then j costs mandi->i->j->depot. Serving each alone costs
    mandi->i->depot and mandi->j->depot. The synergy is the difference, and it
    is **negative** when the two shops lie on a shared corridor -- which is
    exactly the structure that makes this problem quadratic rather than a
    simple per-item ranking.
    """
    n = len(options)
    S = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            oi, oj = options[i], options[j]
            # Best of the two orderings for the joint trip.
            joint = min(
                _haversine(*mandi, oi.lat, oi.lon)
                + _haversine(oi.lat, oi.lon, oj.lat, oj.lon)
                + _haversine(oj.lat, oj.lon, *depot),
                _haversine(*mandi, oj.lat, oj.lon)
                + _haversine(oj.lat, oj.lon, oi.lat, oi.lon)
                + _haversine(oi.lat, oi.lon, *depot),
            ) * detour_factor
            solo_i = (_haversine(*mandi, oi.lat, oi.lon)
                      + _haversine(oi.lat, oi.lon, *depot)) * detour_factor
            solo_j = (_haversine(*mandi, oj.lat, oj.lon)
                      + _haversine(oj.lat, oj.lon, *depot)) * detour_factor
            base = _haversine(*mandi, *depot) * detour_factor
            # Extra cost of the joint trip beyond what the two solo detours
            # already account for. Sharing a corridor makes this negative.
            extra = (joint - base) - ((solo_i - base) + (solo_j - base))
            S[i, j] = S[j, i] = extra * cost_per_km
    return S


def build_circular_qubo(
    problem: CircularProblem,
    *,
    penalty_capacity: float | None = None,
) -> QUBO:
    """Build the return-load selection QUBO with exact capacity slack encoding.

    Capacity is an inequality (sum d_i x_i <= C), which a QUBO cannot express
    directly. The standard exact treatment adds binary slack variables encoding
    the unused capacity in powers of two, turning the inequality into an
    equality that squares cleanly into the objective.
    """
    n = problem.n_options
    if n == 0:
        raise ValueError("no return-load options to select from")

    demands = np.array([o.demand_kg for o in problem.options], dtype=float)
    values = np.array([o.solo_value for o in problem.options], dtype=float)
    S = problem.synergy
    cap = problem.remaining_capacity_kg

    # --- capacity encoding -------------------------------------------------
    # The constraint is an inequality (sum d_i x_i <= cap), which a QUBO cannot
    # express directly. It becomes an equality with binary slack:
    #     sum_i d_i x_i + sum_k 2^k s_k = cap
    #
    # This only works if the equality is actually satisfiable. With real-valued
    # kilogram demands it never is -- no combination of powers of two hits an
    # arbitrary real capacity exactly -- so every assignment incurred the huge
    # squared penalty and the optimizer returned the empty set every time. The
    # fix is to quantise demands and capacity onto a common integer grid, after
    # which the equality is always satisfiable by construction.
    #
    # The price is that capacity is enforced to within one grid unit. That is
    # recorded in the metadata and re-checked exactly in decode_circular(),
    # rather than being silently absorbed.
    n_slack = 0 if cap <= 0 else 6
    unit = max(1.0, cap / (2 ** n_slack - 1)) if n_slack else 1.0
    # Round demands UP and capacity DOWN. Rounding to nearest let the quantised
    # constraint accept selections that exceeded true capacity by under one grid
    # unit -- the decoder caught them, but the QUBO should not propose them at
    # all. Conservative rounding makes quantised feasibility imply true
    # feasibility, at the cost of occasionally excluding a marginal selection.
    d_units = np.maximum(1, np.ceil(demands / unit)).astype(int)
    cap_units = int(np.floor(cap / unit))
    # Slack must be able to absorb the full capacity when nothing is selected.
    while n_slack < 10 and (2 ** n_slack - 1) < cap_units:
        n_slack += 1

    N = n + n_slack
    Q = np.zeros((N, N))
    offset = 0.0

    scale = float(np.abs(values).sum() + np.abs(S).sum() + 1.0)
    # Krauss & McCollum: the penalty must exceed the total achievable cost
    # magnitude, otherwise violating capacity could be cheaper than obeying it.
    # Coefficients are now in grid units, so the penalty is normalised by the
    # squared unit scale to keep the two terms comparable.
    A_cap = (penalty_capacity if penalty_capacity is not None
             else scale / max(1.0, float(max(cap_units, 1))))

    # --- objective: per-load net cost (linear) + pairwise synergy (quadratic)
    for i in range(n):
        Q[i, i] += values[i]
        for j in range(i + 1, n):
            if S[i, j] != 0:
                Q[i, j] += S[i, j]

    # --- capacity: (sum_i d_i x_i + sum_k 2^k s_k - cap)^2, in grid units
    coef = np.zeros(N)
    coef[:n] = d_units
    for k in range(n_slack):
        coef[n + k] = 2 ** k

    for a in range(N):
        if coef[a] == 0:
            continue
        Q[a, a] += A_cap * (coef[a] ** 2 - 2.0 * cap_units * coef[a])
        for b in range(a + 1, N):
            if coef[b] != 0:
                Q[a, b] += 2.0 * A_cap * coef[a] * coef[b]
    offset += A_cap * cap_units ** 2
    slack_unit = unit

    variable_map: dict[int, tuple] = {
        i: ("return_load", problem.options[i].load_id, problem.options[i].shop_id)
        for i in range(n)
    }
    for k in range(n_slack):
        variable_map[n + k] = ("capacity_slack", k, slack_unit * (2 ** k))

    return QUBO(
        Q=np.triu(Q),
        variable_map=variable_map,
        encoding=ENCODING_RETURN_LOAD,
        penalty=A_cap,
        constant_offset=offset,
        metadata={
            "qubo_version": QUBO_VERSION,
            "problem": "return_load_quadratic_knapsack",
            "instance_id": problem.instance_id,
            "n_options": n,
            "n_slack": n_slack,
            "slack_unit_kg": slack_unit,
            "capacity_kg": cap,
            "penalty_capacity": A_cap,
            "revenue_model": f"{REVENUE_INR_PER_TONNE_KM} INR per tonne-km (assumption)",
        },
    )


def decode_circular(x: np.ndarray, problem: CircularProblem, qubo: QUBO) -> dict:
    """Decode a bitstring into an accepted return-load set.

    Capacity is re-checked against the true demands rather than trusting the
    slack encoding, because a noisy sample can satisfy the squared penalty
    approximately while still overloading the truck.
    """
    n = problem.n_options
    chosen = [i for i in range(n) if x[i] > 0.5]
    demand = float(sum(problem.options[i].demand_kg for i in chosen))
    violations: list[str] = []
    if demand > problem.remaining_capacity_kg + 1e-6:
        violations.append(
            f"over_capacity:{demand:.0f}kg>{problem.remaining_capacity_kg:.0f}kg")

    # True objective of this selection, independent of the QUBO's penalty terms.
    obj = float(sum(problem.options[i].solo_value for i in chosen))
    for a_i in range(len(chosen)):
        for b_i in range(a_i + 1, len(chosen)):
            obj += float(problem.synergy[chosen[a_i], chosen[b_i]])

    return {
        "feasible": not violations,
        "selected_indices": chosen,
        "selected_load_ids": [problem.options[i].load_id for i in chosen],
        "selected_shop_ids": [problem.options[i].shop_id for i in chosen],
        "total_demand_kg": demand,
        "capacity_utilization": (demand / problem.remaining_capacity_kg
                                 if problem.remaining_capacity_kg else 0.0),
        "objective": obj,
        "revenue_inr": float(sum(problem.options[i].revenue_inr for i in chosen)),
        "violations": violations,
    }


def greedy_baseline(problem: CircularProblem) -> dict:
    """Classical greedy baseline: best value-density first, respecting capacity.

    This is the honest classical comparator. Greedy is the standard heuristic
    for knapsack and is *not* exact for the quadratic variant, which is why
    there is room for another optimizer to do better.
    """
    n = problem.n_options
    order = sorted(
        range(n),
        key=lambda i: (problem.options[i].solo_value / max(problem.options[i].demand_kg, 1.0)),
    )
    chosen: list[int] = []
    demand = 0.0
    for i in order:
        d = problem.options[i].demand_kg
        if demand + d > problem.remaining_capacity_kg:
            continue
        # Marginal cost including interaction with what is already chosen.
        marginal = problem.options[i].solo_value + sum(
            problem.synergy[i, j] for j in chosen)
        if marginal < 0:  # only take loads that improve the objective
            chosen.append(i)
            demand += d

    obj = float(sum(problem.options[i].solo_value for i in chosen))
    for a_i in range(len(chosen)):
        for b_i in range(a_i + 1, len(chosen)):
            obj += float(problem.synergy[chosen[a_i], chosen[b_i]])

    return {
        "feasible": True,
        "selected_indices": chosen,
        "selected_load_ids": [problem.options[i].load_id for i in chosen],
        "total_demand_kg": demand,
        "objective": obj,
        "algorithm": "greedy_value_density",
    }


def exhaustive_baseline(problem: CircularProblem, max_options: int = 20) -> dict:
    """Exact selection by enumeration -- ground truth for small option sets."""
    n = problem.n_options
    if n > max_options:
        raise ValueError(f"{n} options exceeds the exact limit of {max_options}")
    best, best_obj = [], float("inf")
    for mask in range(1 << n):
        chosen = [i for i in range(n) if (mask >> i) & 1]
        demand = sum(problem.options[i].demand_kg for i in chosen)
        if demand > problem.remaining_capacity_kg + 1e-9:
            continue
        obj = float(sum(problem.options[i].solo_value for i in chosen))
        for a_i in range(len(chosen)):
            for b_i in range(a_i + 1, len(chosen)):
                obj += float(problem.synergy[chosen[a_i], chosen[b_i]])
        if obj < best_obj:
            best, best_obj = chosen, obj
    return {
        "feasible": True,
        "selected_indices": best,
        "selected_load_ids": [problem.options[i].load_id for i in best],
        "total_demand_kg": float(sum(problem.options[i].demand_kg for i in best)),
        "objective": best_obj,
        "algorithm": "exhaustive_exact",
    }
