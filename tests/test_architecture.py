"""VB-QER architectural invariants.

These tests encode the project invariant: **VB-QER is the final routing
algorithm and its architecture is fixed.** Classical solvers, QUBO formulations,
QAOA and quantum artifacts are components inside it.

They exist because the distinction was once blurred in documentation: a
component failing validation was reported as though it were an architecture
verdict. These assertions make the separation mechanical.
"""

from __future__ import annotations

import pytest

from routing.ensemble.problem_family import (
    COMPONENT_POLICY, CircularFamily, ProblemType, classify_circular,
    classify_instance,
)
from routing.ensemble.status import (
    ARCHITECTURE, BY_NAME, COMPONENTS, ComponentStatus, render, summary,
)
from routing.instances import list_instances, load_instance

pytestmark = pytest.mark.skipif(
    len(list_instances()) == 0, reason="route instances not generated"
)


@pytest.fixture(scope="module")
def instance():
    df = list_instances()
    df = df[(df["n_customers"] + 1).between(8, 14)]
    return load_instance(df.iloc[0]["instance_id"])


class TestArchitectureIsFixed:
    def test_final_algorithm_is_vbqer(self):
        assert ARCHITECTURE["final_algorithm"] == "VB-QER"
        assert ARCHITECTURE["status"] == "FIXED"

    def test_entry_point_is_the_ensemble(self):
        assert "VBQEROptimizer" in ARCHITECTURE["entry_point"]

    def test_architecture_and_component_status_are_reported_separately(self):
        s = summary()
        assert s["architecture"]["status"] == "FIXED"
        # Component statuses vary; the architecture's does not.
        assert {c["status"] for c in s["components"].values()} != {"FIXED"}

    def test_a_rejected_component_does_not_change_the_architecture(self):
        """The route-track prior failed validation. That must not be
        representable as an architecture-level verdict."""
        assert BY_NAME["quantum_route_prior_v1"].status is ComponentStatus.REJECTED
        assert ARCHITECTURE["status"] == "FIXED"

    def test_classical_ensemble_is_a_component_not_an_alternative(self):
        c = BY_NAME["classical_ensemble"]
        assert c.status is ComponentStatus.ACTIVE
        assert c.name in {x.name for x in COMPONENTS}

    def test_hardware_is_offline_only(self):
        assert BY_NAME["ibm_quantum_hardware"].status is ComponentStatus.OFFLINE_ONLY

    def test_incumbent_guard_is_permanently_active(self):
        assert BY_NAME["incumbent_guard"].status is ComponentStatus.ACTIVE

    def test_render_is_readable(self):
        out = render()
        assert "VB-QER" in out and "FIXED" in out


class TestProblemClassification:
    def test_every_problem_type_has_a_policy(self):
        for t in ProblemType:
            assert t in COMPONENT_POLICY
            p = COMPONENT_POLICY[t]
            assert p["classical_members"] and "rationale" in p

    def test_shortest_path_disables_the_quantum_path(self):
        """Dijkstra is exact; engaging an approximate optimizer there would be
        pure overhead and could only match, never improve."""
        p = COMPONENT_POLICY[ProblemType.SHORTEST_PATH]
        assert p["use_qubo"] is False
        assert p["use_quantum_artifacts"] is False

    def test_circular_return_enables_the_qubo(self):
        p = COMPONENT_POLICY[ProblemType.CIRCULAR_RETURN]
        assert p["use_qubo"] is True

    def test_capacitated_policy_prefers_ortools(self):
        assert "ortools" in COMPONENT_POLICY[ProblemType.CAPACITATED]["classical_members"]

    def test_classification_is_deterministic(self, instance):
        assert (classify_instance(instance).problem_type
                == classify_instance(instance).problem_type)

    def test_classification_reports_a_policy(self, instance):
        c = classify_instance(instance)
        assert c.policy is COMPONENT_POLICY[c.problem_type]
        d = c.to_dict()
        assert "problem_type" in d and "components_enabled" in d


class TestCircularFamilies:
    def test_families_are_assigned(self):
        from routing.hybrid.circular_builder import build_benchmark_set
        problems = build_benchmark_set(n_problems=8, max_options=5)
        fams = {classify_circular(p) for p in problems}
        assert fams
        assert all(isinstance(f, CircularFamily) for f in fams)

    def test_classification_is_stable(self):
        from routing.hybrid.circular_builder import build_benchmark_set
        p = build_benchmark_set(n_problems=2, max_options=5)[0]
        assert classify_circular(p) == classify_circular(p)


class TestTraceability:
    """Every decision must record enough to prove when quantum influenced it."""

    REQUIRED = [
        "vbqer_version", "problem_type", "problem_family",
        "classical_members_used", "classical_incumbent_objective",
        "qubo_used", "quantum_component_invoked", "quantum_contribution_used",
        "quantum_artifact_source", "quantum_artifact_version",
        "quantum_contribution_score", "circular_optimizer_used",
        "candidate_selected", "final_route_source", "objective_before",
        "objective_after", "improvement", "incumbent_guard_triggered",
    ]

    def test_all_trace_fields_present(self, instance):
        from routing.ensemble import VBQEROptimizer
        s = VBQEROptimizer().solve(instance)
        for f in self.REQUIRED:
            assert hasattr(s, f), f"missing trace field: {f}"

    def test_trace_serialises_flat(self, instance):
        from routing.ensemble import VBQEROptimizer
        row = VBQEROptimizer().solve(instance).to_row()
        assert all(not isinstance(v, (list, dict)) for v in row.values())
        for f in self.REQUIRED:
            assert f in row

    def test_no_quantum_version_claimed_without_an_artifact(self, instance):
        from routing.ensemble import VBQEROptimizer
        s = VBQEROptimizer(priors=[]).solve(instance)
        assert s.quantum_artifact_source == "none"
        assert s.quantum_artifact_version == "none"
        assert s.quantum_contribution_score == 0.0

    def test_improvement_is_consistent_with_objectives(self, instance):
        from routing.ensemble import VBQEROptimizer
        s = VBQEROptimizer().solve(instance)
        assert s.improvement == pytest.approx(s.objective_before - s.objective_after)
