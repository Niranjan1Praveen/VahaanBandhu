"""Reduce a road network to a small subproblem worth optimizing.

This is the load-bearing step of the whole hybrid architecture. Encoding the
Delhi NCR + Haryana + Punjab + UP road graph onto quantum hardware is not
possible and will not become possible by tuning anything. What *is* tractable
is: let the classical road network do what it is good at (finding a handful of
sensible corridors), then optimize the small discrete choice that remains.

    full road graph
      -> k-shortest-path candidate generation   (classical, cheap)
      -> Pareto dominance filtering             (classical, cheap)
      -> reduced selection problem, ~5-20 vars  (QUBO / QAOA-scale)
      -> decode and validate                    (classical)

Dominance filtering matters more than it looks. A candidate that is longer,
slower, more expensive *and* riskier than another can never win under any
non-negative weighting, so carrying it into the QUBO wastes a qubit on a
decision that is already made.
"""

from __future__ import annotations

import numpy as np

from routing.models import RouteCandidate

# Criteria on which lower is always better. Used for dominance testing.
MINIMISE_CRITERIA = (
    "distance_km", "travel_time_min", "traffic_delay_min",
    "toll_cost_inr", "estimated_fuel_cost_inr", "road_risk_score",
)


def _criteria_vector(c: RouteCandidate) -> np.ndarray:
    return np.array([getattr(c, k) for k in MINIMISE_CRITERIA], dtype=float)


def dominates(a: RouteCandidate, b: RouteCandidate) -> bool:
    """True if a is at least as good as b on every criterion and strictly
    better on at least one."""
    va, vb = _criteria_vector(a), _criteria_vector(b)
    return bool(np.all(va <= vb + 1e-9) and np.any(va < vb - 1e-9))


def pareto_filter(candidates: list[RouteCandidate]) -> list[RouteCandidate]:
    """Keep only non-dominated candidates.

    Anything removed here could not have won under any non-negative weight
    vector, so this discards no reachable optimum.
    """
    keep = []
    for i, c in enumerate(candidates):
        if not any(dominates(other, c) for j, other in enumerate(candidates) if i != j):
            keep.append(c)
    return keep


def reduce_candidates(
    candidates: list[RouteCandidate], max_candidates: int = 8,
) -> tuple[list[RouteCandidate], dict]:
    """Filter to a QUBO-scale candidate set, reporting what was discarded."""
    n_in = len(candidates)
    if n_in == 0:
        return [], {"n_input": 0, "n_after_pareto": 0, "n_output": 0}

    pareto = pareto_filter(candidates)
    n_pareto = len(pareto)

    # If dominance alone did not get us small enough, keep the cheapest by a
    # neutral equal-weight normalised score. This *can* discard a candidate
    # that some extreme weighting would have preferred, so it is reported.
    truncated = False
    if len(pareto) > max_candidates:
        mat = np.array([_criteria_vector(c) for c in pareto])
        span = mat.max(axis=0) - mat.min(axis=0)
        span[span == 0] = 1.0
        norm = (mat - mat.min(axis=0)) / span
        order = np.argsort(norm.sum(axis=1))[:max_candidates]
        pareto = [pareto[i] for i in order]
        truncated = True

    return pareto, {
        "n_input": n_in,
        "n_after_pareto": n_pareto,
        "n_output": len(pareto),
        "n_dominated_removed": n_in - n_pareto,
        "truncated_by_budget": truncated,
        "truncation_may_discard_optimum": truncated,
    }


def build_selection_problem(
    candidates: list[RouteCandidate], weights: dict[str, float],
) -> tuple[np.ndarray, list[str]]:
    """Turn scored candidates into a one-hot selection cost vector.

    Returns (costs, route_ids). The caller wraps this in a QUBO with a
    "select exactly one" constraint -- the smallest honest quantum-amenable
    formulation of the route-choice problem.
    """
    from routing.objective import score_candidate

    costs = np.array([score_candidate(c, weights).total for c in candidates])
    return costs, [c.route_id for c in candidates]


def build_one_hot_qubo(costs: np.ndarray, penalty: float | None = None):
    """QUBO for 'choose exactly one candidate'.

    Included for completeness and for the benchmark matrix, with an honest
    caveat recorded in the research notes: selecting the minimum of n numbers
    is O(n) classically. This formulation is a *validation vehicle* for the
    encode/solve/decode pipeline, not a problem where quantum help is expected.
    The genuinely hard formulations are the sequencing ones in
    ``routing.quantum.qubo``.
    """
    from routing.quantum.qubo import QUBO, ENCODING_EDGE_SELECTION

    n = len(costs)
    if penalty is None:
        penalty = float(np.abs(costs).sum() + 1.0)

    Q = np.zeros((n, n))
    for i in range(n):
        Q[i, i] += costs[i] - penalty  # from -2*penalty*x_i + penalty*x_i^2
        for j in range(i + 1, n):
            Q[i, j] += 2 * penalty

    return QUBO(
        Q=np.triu(Q),
        variable_map={i: ("candidate", i, 0) for i in range(n)},
        encoding="one_hot_selection_v1",
        penalty=penalty,
        constant_offset=penalty,
        metadata={"n_candidates": n, "problem": "candidate_selection",
                  "note": "classically trivial; used to validate the pipeline"},
    )
