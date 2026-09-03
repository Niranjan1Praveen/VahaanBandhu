"""Edge-level costs expressed in the project's real objective.

The classical survey exposed a problem that matters more than any solver choice:
**every classical heuristic in the codebase minimizes distance, while the
VahaanBandhu objective is multi-objective.** On the surveyed instances even
``brute_force_exact`` -- a provably distance-optimal solver -- showed a 2.4% mean
excess against the best objective value found, because the distance-optimal tour
is not the objective-optimal tour.

That is an objective-alignment bug, not a quantum question, and it must be fixed
before any hybrid comparison is meaningful. Otherwise a "quantum improvement"
would really just be the hybrid layer optimizing the correct objective while the
classical baseline optimizes a proxy -- a rigged comparison.

This module builds a scalar per-edge cost in objective units, so that:

* classical solvers can be run on the *true* objective (the fair baseline), and
* segment costs in the QUBO use the same units as everything else.

Additivity caveat, stated because it is a real approximation: distance, time,
fuel and toll are edge-additive, so summing them along a path is exact. Risk is
defined as a route *mean* in ``routing.evaluation.metrics``; here it is summed
per edge, which weights long multi-edge paths more heavily. Empty-kilometre and
circular-logistics terms are route-level and cannot be attributed to a single
edge at all, so they are excluded here and applied by the full evaluator. A
route chosen on this matrix is therefore near-optimal, not provably optimal, for
the full objective -- and the final selection always re-scores candidates with
``metrics.evaluate``.
"""

from __future__ import annotations

import numpy as np

from routing.models import RoutingInstance


def objective_cost_matrix(
    inst: RoutingInstance, weights: dict[str, float] | None = None
) -> np.ndarray:
    """Per-edge cost in objective units.

    Combines the edge-additive terms of the project objective using the
    instance's own weights, so a solver run on this matrix is optimizing the
    same thing the benchmark scores.
    """
    w = {**inst.objective_weights, **(weights or {})}
    n = inst.n_nodes

    C = w.get("distance_km", 1.0) * inst.distance_matrix
    C = C + w.get("time_min", 0.0) * inst.time_matrix

    if inst.fuel_matrix is not None:
        C = C + w.get("fuel_inr", 0.0) * inst.fuel_matrix
    else:
        # Fall back to the same fuel model the evaluator uses, so the two agree.
        C = C + w.get("fuel_inr", 0.0) * (inst.distance_matrix / 5.0 * 92.0)

    if inst.toll_matrix is not None:
        C = C + w.get("toll_inr", 0.0) * inst.toll_matrix
    if inst.risk_matrix is not None:
        C = C + w.get("risk", 0.0) * inst.risk_matrix

    C = np.array(C, dtype=float)
    np.fill_diagonal(C, 0.0)
    return C


def path_cost(C: np.ndarray, path: tuple[int, ...] | list[int]) -> float:
    return float(sum(C[a, b] for a, b in zip(path[:-1], path[1:])))


def tour_cost_objective(C: np.ndarray, tour: list[int]) -> float:
    """Closed-tour cost on the objective matrix."""
    return float(sum(C[tour[i], tour[(i + 1) % len(tour)]] for i in range(len(tour))))
