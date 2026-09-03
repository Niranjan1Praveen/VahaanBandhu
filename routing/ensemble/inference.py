"""VB-QER inference: the canonical entry point for VahaanBandhu routing.

    solution = VBQEROptimizer().solve(instance)

Everything downstream -- and eventually the web application -- calls this and
nothing else. It should not need to know what QAOA is.

Pipeline
--------
    instance
      -> classical ensemble members            (candidate pool + consensus)
      -> candidate reduction
      -> load offline quantum-derived artifacts (NO live QPU call)
      -> quantum-enhanced ensemble scoring
      -> constraint validation
      -> classical local refinement
      -> incumbent comparison                   (the guard)
      -> final route + explanation + quantum contribution trace

**Production-safety invariants**, each enforced in code rather than by
convention:

1. No live quantum hardware call. ``routing.quantum.ibm_runtime`` is not
   imported anywhere in this module's import graph, and a test asserts that.
2. A worse or infeasible candidate can never replace a better feasible
   incumbent.
3. Missing, stale or non-deployable artifacts degrade the system to a classical
   ensemble rather than failing it.
4. Every decision carries a quantum contribution trace, so "quantum helped" is
   measurable after the fact instead of asserted.
"""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field

from routing.ensemble.members import (
    Candidate, compute_diversity, generate_candidates,
)
from routing.ensemble.quantum_priors import QuantumPrior, load_priors
from routing.ensemble.scorer import (
    DEFAULT_WEIGHTS, apply_quantum_prior, score_candidates,
)
from routing.evaluation.metrics import evaluate, tour_to_routes
from routing.hybrid.objective_costs import objective_cost_matrix
from routing.models import RoutingInstance

VBQER_VERSION = "vbqer_v1"


@dataclass
class VBQERSolution:
    """Final routing answer with a full decision trace."""

    instance_id: str
    algorithm: str
    algorithm_version: str
    tour: list[int]
    routes: list[list[int]]
    objective: float
    distance_km: float
    time_min: float
    toll_inr: float
    fuel_inr: float
    empty_km: float
    feasible: bool
    violations: list[str]
    cost_snapshot_id: str

    # Ensemble trace.
    n_candidates: int
    consensus: int
    diversity: float
    classical_incumbent_objective: float
    final_route_source: str  # classical_incumbent | ensemble_refined | quantum_refined
    ensemble_score: float
    score_terms: dict[str, float] = field(default_factory=dict)

    # Quantum contribution trace.
    quantum_contribution_used: bool = False
    quantum_artifact_ids: list[str] = field(default_factory=list)
    quantum_artifact_source: str = "none"
    quantum_artifact_version: str = "none"
    quantum_contribution_score: float = 0.0
    quantum_hardware_called_live: bool = False  # always False by design
    quantum_component_invoked: bool = False

    # Component / classification trace, so a decision can be attributed later.
    vbqer_version: str = ""
    problem_type: str = ""
    problem_family: str | None = None
    classical_members_used: list[str] = field(default_factory=list)
    qubo_used: bool = False
    circular_optimizer_used: bool = False
    candidate_selected: str = ""
    objective_before: float = 0.0
    objective_after: float = 0.0
    improvement: float = 0.0
    incumbent_guard_triggered: bool = False

    # Decomposed timing.
    classical_ms: float = 0.0
    artifact_ms: float = 0.0
    scoring_ms: float = 0.0
    refinement_ms: float = 0.0
    total_ms: float = 0.0

    explanation: dict = field(default_factory=dict)

    def to_row(self) -> dict:
        d = asdict(self)
        d["tour"] = ",".join(map(str, self.tour))
        d["routes"] = "|".join(",".join(map(str, r)) for r in self.routes)
        d["violations"] = ";".join(self.violations)
        d["quantum_artifact_ids"] = ",".join(self.quantum_artifact_ids)
        d["classical_members_used"] = ",".join(self.classical_members_used)
        d.pop("score_terms", None)
        d.pop("explanation", None)
        return d


class VBQEROptimizer:
    """VahaanBandhu Quantum-Enhanced Routing ensemble."""

    def __init__(
        self,
        *,
        weights: dict[str, float] | None = None,
        priors: list[QuantumPrior] | None = None,
        artifact_source: str | None = None,
        use_quantum_artifacts: bool = True,
        include_ortools: bool = True,
        seed: int = 42,
    ) -> None:
        """
        Args:
            artifact_source: Restrict to one provenance
                (``quantum_simulator`` / ``quantum_hardware`` / ``hybrid``).
                The ablation uses this to isolate where any benefit comes from.
            use_quantum_artifacts: False gives the pure classical ensemble --
                ablation arm B.
        """
        self.weights = {**DEFAULT_WEIGHTS, **(weights or {})}
        self.use_quantum_artifacts = use_quantum_artifacts
        self.artifact_source = artifact_source
        self.include_ortools = include_ortools
        self.seed = seed
        self._priors = priors

    def _load_artifacts(self) -> list[QuantumPrior]:
        if not self.use_quantum_artifacts:
            return []
        if self._priors is not None:
            return [p for p in self._priors
                    if (self.artifact_source is None
                        or p.source == self.artifact_source)
                    and p.deployable]
        try:
            return load_priors(source=self.artifact_source, deployable_only=True)
        except Exception:
            # A missing or unreadable artifact store must not break routing.
            return []

    def solve(self, inst: RoutingInstance) -> VBQERSolution:
        t_start = time.perf_counter()

        # --- classify: decide which internal experts should engage.
        # VB-QER is one algorithm containing specialised optimizers; this is how
        # it picks them. A shortest-path query, for instance, skips the QUBO
        # layer entirely because Dijkstra is already exact.
        from routing.ensemble.problem_family import classify_instance
        classification = classify_instance(inst)
        policy = classification.policy

        # --- classical ensemble members
        t0 = time.perf_counter()
        candidates = generate_candidates(
            inst, seed=self.seed, include_ortools=self.include_ortools)
        compute_diversity(candidates)
        classical_ms = (time.perf_counter() - t0) * 1000

        feasible = [c for c in candidates if c.feasible]
        pool = feasible or candidates
        incumbent = min(pool, key=lambda c: c.objective)

        # --- offline quantum artifacts (never a live QPU call)
        t0 = time.perf_counter()
        # The classification policy can disable the quantum path for problem
        # types where it cannot help (e.g. exact shortest path).
        priors = self._load_artifacts() if policy["use_quantum_artifacts"] else []
        merged: dict[str, float] = {}
        for p in priors:
            merged.update(p.variable_marginals)
        n_touched = apply_quantum_prior(candidates, merged) if merged else 0
        artifact_ms = (time.perf_counter() - t0) * 1000

        # --- ensemble scoring
        t0 = time.perf_counter()
        scored = score_candidates(candidates, self.weights)
        best = scored[0]
        scoring_ms = (time.perf_counter() - t0) * 1000

        # --- classical local refinement of the ensemble's pick
        t0 = time.perf_counter()
        C = objective_cost_matrix(inst)
        from routing.classical.heuristics import two_opt
        refined_tour = two_opt(C, best.candidate.tour).tour
        refined_routes = tour_to_routes(refined_tour, inst.depot_index)
        refined_eval = evaluate(inst, refined_routes)
        refinement_ms = (time.perf_counter() - t0) * 1000

        # --- incumbent guard (invariant 2)
        chosen_tour, chosen_eval = refined_tour, refined_eval
        source = ("ensemble_refined" if best.candidate.candidate_id
                  != incumbent.candidate_id else "classical_incumbent")

        if not refined_eval.feasible and incumbent.feasible:
            chosen_tour = incumbent.tour
            chosen_eval = evaluate(inst, incumbent.routes)
            source = "classical_incumbent"
        elif refined_eval.objective >= incumbent.objective - 1e-9:
            # The ensemble did not beat the incumbent; keep the safe answer.
            if incumbent.feasible or not refined_eval.feasible:
                chosen_tour = incumbent.tour
                chosen_eval = evaluate(inst, incumbent.routes)
                source = "classical_incumbent"

        quantum_used = bool(
            merged
            and n_touched > 0
            and source != "classical_incumbent"
            and best.candidate.quantum_prior_score > 0
        )

        explanation = {
            "selected_candidate": best.candidate.candidate_id,
            "produced_by": sorted(set(best.candidate.produced_by)),
            "classical_incumbent_objective": round(incumbent.objective, 4),
            "final_objective": round(chosen_eval.objective, 4),
            "n_candidates_considered": len(candidates),
            "consensus": best.candidate.consensus,
            "diversity": best.candidate.diversity,
            "quantum_hardware_called_live": False,
            "quantum_artifact_used": quantum_used,
            "quantum_artifact_source": (
                priors[0].source if priors and quantum_used else "none"),
            "quantum_artifact_ids": [p.artifact_id for p in priors] if quantum_used else [],
            "reasons": self._reasons(best, incumbent, chosen_eval, quantum_used),
        }

        guard_triggered = (source == "classical_incumbent"
                           and best.candidate.candidate_id != incumbent.candidate_id)

        return VBQERSolution(
            instance_id=inst.instance_id,
            algorithm="VB-QER",
            algorithm_version=VBQER_VERSION,
            tour=chosen_tour,
            routes=tour_to_routes(chosen_tour, inst.depot_index),
            objective=chosen_eval.objective,
            distance_km=chosen_eval.distance_km,
            time_min=chosen_eval.time_min,
            toll_inr=chosen_eval.toll_inr,
            fuel_inr=chosen_eval.fuel_inr,
            empty_km=chosen_eval.empty_km,
            feasible=chosen_eval.feasible,
            violations=chosen_eval.violations,
            cost_snapshot_id=inst.cost_snapshot_id,
            n_candidates=len(candidates),
            consensus=best.candidate.consensus,
            diversity=best.candidate.diversity,
            classical_incumbent_objective=incumbent.objective,
            final_route_source=source,
            ensemble_score=best.score,
            score_terms=best.terms,
            quantum_contribution_used=quantum_used,
            quantum_artifact_ids=[p.artifact_id for p in priors] if quantum_used else [],
            quantum_artifact_source=(priors[0].source if priors and quantum_used else "none"),
            quantum_contribution_score=(
                best.candidate.quantum_prior_score if quantum_used else 0.0),
            quantum_artifact_version=(priors[0].artifact_version
                                      if priors and quantum_used else "none"),
            quantum_hardware_called_live=False,
            quantum_component_invoked=bool(priors),
            vbqer_version=VBQER_VERSION,
            problem_type=classification.problem_type.value,
            problem_family=classification.family,
            classical_members_used=sorted({m for c in candidates
                                           for m in c.produced_by}),
            qubo_used=bool(policy["use_qubo"]),
            circular_optimizer_used=False,
            candidate_selected=best.candidate.candidate_id,
            objective_before=incumbent.objective,
            objective_after=chosen_eval.objective,
            improvement=incumbent.objective - chosen_eval.objective,
            incumbent_guard_triggered=guard_triggered,
            classical_ms=classical_ms,
            artifact_ms=artifact_ms,
            scoring_ms=scoring_ms,
            refinement_ms=refinement_ms,
            total_ms=(time.perf_counter() - t_start) * 1000,
            explanation=explanation,
        )

    @staticmethod
    def _reasons(best, incumbent, chosen_eval, quantum_used: bool) -> list[str]:
        r: list[str] = []
        if best.candidate.consensus > 1:
            r.append(f"{best.candidate.consensus} independent solvers agreed on this route")
        if chosen_eval.empty_km > 0:
            r.append(f"{chosen_eval.empty_km:.1f} km of the tour runs empty")
        if best.candidate.diversity > 0.5:
            r.append("route is structurally distinct from the rest of the pool")
        if quantum_used:
            r.append("offline quantum-derived segment prior favoured this route")
        else:
            r.append("no deployable quantum artifact applied; classical ensemble decided")
        if chosen_eval.violations:
            r.append("constraint violations: " + ", ".join(chosen_eval.violations[:2]))
        return r
