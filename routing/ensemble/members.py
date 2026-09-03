"""Classical ensemble members and the candidate pool.

The ensemble is not "run several algorithms and take the lowest number". Each
member contributes a *candidate* plus signals about it, and the scorer combines
those signals. Consensus matters: a route that several independent members
converge on is more likely to be robust than one a single solver found.

Members are chosen from the classical survey evidence, not by assumption:

* **2-opt over the true objective** -- the strongest general-purpose member, and
  the incumbent. The survey showed distance-based solvers are systematically
  misaligned with the project objective, so this member optimizes the real one.
* **Nearest neighbour** -- weak alone, but a genuinely different construction, so
  it contributes diversity rather than a near-duplicate of 2-opt.
* **Simulated annealing** -- a stochastic member that escapes 2-opt's local
  optima on some instances.
* **OR-Tools** -- the only member that produced feasible solutions on
  capacitated multi-vehicle instances (46-75% vs ~1.5% for the TSP heuristics),
  so it is included specifically for those.

Members that duplicate another's answer add no information, which is why the
pool deduplicates and records consensus counts.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

import numpy as np

from routing.classical.heuristics import (
    nearest_neighbour, simulated_annealing, two_opt,
)
from routing.evaluation.metrics import evaluate, tour_to_routes
from routing.hybrid.objective_costs import objective_cost_matrix
from routing.models import RoutingInstance


@dataclass
class Candidate:
    """One candidate solution plus the signals the ensemble scores it on."""

    candidate_id: str
    tour: list[int]
    routes: list[list[int]]
    objective: float
    feasible: bool
    violations: list[str]
    produced_by: list[str] = field(default_factory=list)
    runtime_ms: float = 0.0
    # Ensemble signals.
    consensus: int = 1
    diversity: float = 0.0
    quantum_prior_score: float = 0.0
    source: str = "classical"

    @property
    def key(self) -> tuple[int, ...]:
        """Canonical tour identity, rotation-invariant, for deduplication."""
        t = list(self.tour)
        if not t:
            return ()
        k = t.index(min(t))
        return tuple(t[k:] + t[:k])


def _make(inst: RoutingInstance, tour: list[int], name: str, ms: float) -> Candidate:
    routes = tour_to_routes(tour, inst.depot_index)
    ev = evaluate(inst, routes)
    return Candidate(
        candidate_id=f"{name}", tour=list(tour), routes=routes,
        objective=ev.objective, feasible=ev.feasible, violations=ev.violations,
        produced_by=[name], runtime_ms=ms,
    )


def generate_candidates(
    inst: RoutingInstance, *, seed: int = 42, include_ortools: bool = True,
    sa_restarts: int = 2,
) -> list[Candidate]:
    """Run the classical members and return a deduplicated candidate pool."""
    C = objective_cost_matrix(inst)
    out: list[Candidate] = []

    t0 = time.perf_counter()
    nn = nearest_neighbour(C, inst.depot_index)
    out.append(_make(inst, nn.tour, "nearest_neighbour", (time.perf_counter() - t0) * 1000))

    t0 = time.perf_counter()
    opt = two_opt(C, nn.tour)
    out.append(_make(inst, opt.tour, "two_opt", (time.perf_counter() - t0) * 1000))

    for r in range(sa_restarts):
        t0 = time.perf_counter()
        sa = simulated_annealing(C, inst.depot_index, seed=seed + r)
        out.append(_make(inst, sa.tour, f"simulated_annealing_{r}",
                         (time.perf_counter() - t0) * 1000))

    if include_ortools and len(inst.vehicle_capacities) > 1:
        # Only worth the time limit on genuinely multi-vehicle instances, which
        # is where the survey showed it is the only feasible member.
        try:
            from routing.classical.vrp import solve_vrp
            t0 = time.perf_counter()
            sol = solve_vrp(inst, time_limit_s=3, seed=seed)
            if sol.feasible and sol.ordered_stops:
                flat = [n for r in sol.ordered_stops for n in r if n != inst.depot_index]
                if flat:
                    out.append(_make(inst, [inst.depot_index] + flat, "ortools",
                                     (time.perf_counter() - t0) * 1000))
        except Exception:
            pass  # a member failing is a missing signal, not a fatal error

    return deduplicate(out)


def deduplicate(candidates: list[Candidate]) -> list[Candidate]:
    """Merge identical tours, accumulating consensus counts.

    Consensus is a real signal: when nearest-neighbour, 2-opt and annealing all
    land on the same tour, that tour is likelier to be a genuine optimum than
    one found by a single stochastic member.
    """
    merged: dict[tuple, Candidate] = {}
    for c in candidates:
        k = c.key
        if k in merged:
            m = merged[k]
            m.consensus += 1
            m.produced_by.extend(c.produced_by)
            m.runtime_ms += c.runtime_ms
        else:
            merged[k] = c
    return list(merged.values())


def compute_diversity(candidates: list[Candidate]) -> None:
    """Annotate each candidate with how structurally different it is from the rest.

    Measured as the mean fraction of directed edges not shared with the other
    candidates. Diversity is what makes an ensemble more than a single solver:
    a pool of near-identical tours cannot cover a different local optimum.
    """
    def edges(t: list[int]) -> set[tuple[int, int]]:
        return {(t[i], t[(i + 1) % len(t)]) for i in range(len(t))}

    esets = [edges(c.tour) for c in candidates]
    for i, c in enumerate(candidates):
        if len(candidates) == 1:
            c.diversity = 0.0
            continue
        sims = []
        for j, other in enumerate(esets):
            if i == j:
                continue
            union = esets[i] | other
            sims.append(len(esets[i] & other) / len(union) if union else 0.0)
        c.diversity = round(1.0 - float(np.mean(sims)), 5)
