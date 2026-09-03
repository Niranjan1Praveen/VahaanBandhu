"""Problem classification, so VB-QER can route to the right internal experts.

VB-QER is one algorithm containing specialised optimizers. Classification is how
it decides which components should contribute to a given instance -- for example
that a pure shortest-path query should go to Dijkstra/A* and skip the QUBO layer
entirely, because Dijkstra is exact and there is nothing for an approximate
optimizer to add.

Classification also underpins the **artifact transfer hypothesis**: a single
global quantum prior failed held-out validation (0/15), but quantum-derived
information may still transfer *within* structurally matched families. Family
tags let that be tested rather than assumed.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import numpy as np

from routing.models import RoutingInstance


class ProblemType(str, Enum):
    SHORTEST_PATH = "shortest_path"
    SINGLE_VEHICLE = "single_vehicle"
    CAPACITATED = "capacitated"
    TIME_WINDOWED = "time_windowed"
    CIRCULAR_RETURN = "circular_return"


class CircularFamily(str, Enum):
    """Structural families for return-load problems."""

    TIGHT_CAPACITY_DENSE = "A_tight_capacity_dense"
    LOOSE_CAPACITY_SPARSE = "B_loose_capacity_sparse"
    HIGH_DETOUR = "C_high_detour"
    SHARED_CORRIDOR_SYNERGY = "D_shared_corridor_synergy"
    BALANCED = "E_balanced"


# Which VB-QER components are worth engaging per problem type. Recorded as data
# so the routing policy is inspectable rather than buried in branches.
COMPONENT_POLICY: dict[ProblemType, dict] = {
    ProblemType.SHORTEST_PATH: {
        "classical_members": ["dijkstra", "astar"],
        "use_qubo": False,
        "use_quantum_artifacts": False,
        "rationale": "Dijkstra is exact in polynomial time; no optimizer can improve on it.",
    },
    ProblemType.SINGLE_VEHICLE: {
        "classical_members": ["two_opt", "nearest_neighbour", "simulated_annealing"],
        "use_qubo": True,
        "use_quantum_artifacts": True,
        "rationale": "Objective-aware local search; QUBO refinement is admissible.",
    },
    ProblemType.CAPACITATED: {
        "classical_members": ["ortools", "two_opt", "simulated_annealing"],
        "use_qubo": False,
        "use_quantum_artifacts": True,
        "rationale": "OR-Tools is the only member producing feasible capacitated routes.",
    },
    ProblemType.TIME_WINDOWED: {
        "classical_members": ["ortools", "two_opt"],
        "use_qubo": False,
        "use_quantum_artifacts": True,
        "rationale": "Time-window dimensions are handled natively by OR-Tools.",
    },
    ProblemType.CIRCULAR_RETURN: {
        "classical_members": ["greedy_value_density"],
        "use_qubo": True,
        "use_quantum_artifacts": True,
        "rationale": ("Quadratic knapsack: NP-hard, greedy is 22.5% suboptimal, and "
                      "this is where the measured optimization headroom is."),
    },
}


@dataclass(frozen=True)
class Classification:
    problem_type: ProblemType
    family: str | None
    n_nodes: int
    n_vehicles: int
    has_time_windows: bool
    capacity_tightness: float
    policy: dict

    def to_dict(self) -> dict:
        return {
            "problem_type": self.problem_type.value,
            "problem_family": self.family,
            "n_nodes": self.n_nodes,
            "n_vehicles": self.n_vehicles,
            "has_time_windows": self.has_time_windows,
            "capacity_tightness": round(self.capacity_tightness, 4),
            "components_enabled": self.policy,
        }


def classify_instance(inst: RoutingInstance) -> Classification:
    """Determine the problem type and which VB-QER components should engage."""
    n_vehicles = len(inst.vehicle_capacities)
    has_tw = inst.time_windows is not None
    total_demand = float(inst.demands.sum())
    fleet = float(sum(inst.vehicle_capacities)) or 1.0
    tightness = total_demand / fleet

    if inst.n_customers <= 1:
        ptype = ProblemType.SHORTEST_PATH
    elif has_tw:
        ptype = ProblemType.TIME_WINDOWED
    elif n_vehicles > 1 or tightness > 1.0:
        ptype = ProblemType.CAPACITATED
    else:
        ptype = ProblemType.SINGLE_VEHICLE

    return Classification(
        problem_type=ptype, family=None, n_nodes=inst.n_nodes,
        n_vehicles=n_vehicles, has_time_windows=has_tw,
        capacity_tightness=tightness, policy=COMPONENT_POLICY[ptype],
    )


def classify_circular(problem) -> CircularFamily:
    """Family for a return-load problem.

    Thresholds are deliberately structural (capacity tightness, synergy sign,
    detour scale) rather than arbitrary buckets, so a family label means
    something about the optimization landscape a prior would have to transfer
    across.
    """
    demands = np.array([o.demand_kg for o in problem.options], dtype=float)
    cap = problem.remaining_capacity_kg
    tightness = float(demands.sum() / cap) if cap else float("inf")

    off = problem.synergy[np.triu_indices(problem.n_options, k=1)]
    mean_syn = float(np.mean(off)) if off.size else 0.0
    scale = float(np.mean(np.abs([o.solo_value for o in problem.options]))) or 1.0
    rel_syn = mean_syn / scale

    mean_detour = float(np.mean([o.detour_km for o in problem.options]))

    if rel_syn < -0.05:
        return CircularFamily.SHARED_CORRIDOR_SYNERGY
    if mean_detour > 25.0:
        return CircularFamily.HIGH_DETOUR
    if tightness > 2.0:
        return CircularFamily.TIGHT_CAPACITY_DENSE
    if tightness < 1.0:
        return CircularFamily.LOOSE_CAPACITY_SPARSE
    return CircularFamily.BALANCED
