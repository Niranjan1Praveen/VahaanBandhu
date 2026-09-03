"""VB-QER ensemble: members, scoring, artifacts and production-safety invariants.

The most important test in this file is
``test_no_live_quantum_hardware_import``. It enforces the architectural promise
by inspection of the actual import graph rather than by documentation: if anyone
ever wires a QPU call into live inference, this fails.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from routing.ensemble.inference import VBQEROptimizer, VBQERSolution
from routing.ensemble.members import (
    Candidate, compute_diversity, deduplicate, generate_candidates,
)
from routing.ensemble.quantum_priors import (
    QuantumPrior, distil_marginals, load_priors, save_prior, validate_prior,
)
from routing.ensemble.scorer import (
    MAX_SIGNAL_INFLUENCE, apply_quantum_prior, normalise_objectives,
    score_candidates,
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


def _cand(cid, obj, tour, feasible=True, consensus=1, prior=0.0, diversity=0.0):
    return Candidate(candidate_id=cid, tour=tour, routes=[tour + [0]],
                     objective=obj, feasible=feasible, violations=[],
                     produced_by=[cid], consensus=consensus,
                     quantum_prior_score=prior, diversity=diversity)


class TestProductionSafety:
    def test_no_live_quantum_hardware_import(self):
        """Live inference must never reach IBM Quantum.

        Checked in a subprocess. Asserting on this process's ``sys.modules``
        would prove nothing -- any other test or notebook cell that touched the
        IBM runtime would pollute the table and the check would fail (or, worse,
        a reordering could make it pass vacuously). A clean interpreter that
        imports only the inference module is the only sound test.
        """
        import subprocess
        import sys

        probe = (
            "import sys; import routing.ensemble.inference; "
            "bad=[m for m in sys.modules if 'ibm' in m.lower()]; "
            "print('LEAK' if bad else 'CLEAN', bad[:5])"
        )
        out = subprocess.run([sys.executable, "-c", probe], capture_output=True,
                             text=True, cwd=str(Path(__file__).resolve().parents[1]))
        assert out.returncode == 0, out.stderr[-500:]
        assert out.stdout.startswith("CLEAN"), (
            f"live inference pulled in an IBM module: {out.stdout}")

    def test_solution_reports_no_live_hardware_call(self, instance):
        s = VBQEROptimizer().solve(instance)
        assert s.quantum_hardware_called_live is False

    def test_works_with_no_artifacts_at_all(self, instance):
        """Degradation, not failure, when the artifact store is empty."""
        s = VBQEROptimizer(priors=[], use_quantum_artifacts=True).solve(instance)
        assert isinstance(s, VBQERSolution)
        assert s.quantum_contribution_used is False
        assert s.final_route_source in (
            "classical_incumbent", "ensemble_refined", "quantum_refined")

    def test_works_with_quantum_disabled(self, instance):
        s = VBQEROptimizer(use_quantum_artifacts=False).solve(instance)
        assert s.quantum_contribution_used is False

    def test_non_deployable_prior_is_not_used(self, instance):
        bad = QuantumPrior(
            artifact_id="bad", artifact_version="v1", source="quantum_simulator",
            problem_family="segment_set_partition",
            variable_marginals={"0->1": 1.0}, qaoa_params=None, n_layers=2,
            dataset_version="v0.1", graph_version="g1", training_split="train",
            cost_snapshot_ids=["CST_X"], quantum_backend="aer",
            n_problems_distilled=5, mean_feasible_rate=0.1, deployable=False,
        )
        s = VBQEROptimizer(priors=[bad]).solve(instance)
        assert s.quantum_contribution_used is False


class TestIncumbentInvariant:
    def test_final_objective_never_exceeds_incumbent(self, instance):
        s = VBQEROptimizer().solve(instance)
        assert s.objective <= s.classical_incumbent_objective + 1e-9

    def test_holds_with_a_misleading_prior(self, instance):
        """Even a prior that strongly favours a bad route cannot make the final
        answer worse than the classical incumbent."""
        misleading = QuantumPrior(
            artifact_id="misleading", artifact_version="v1",
            source="quantum_simulator", problem_family="segment_set_partition",
            variable_marginals={f"{i}->{i+1}": 1.0 for i in range(20)},
            qaoa_params=None, n_layers=2, dataset_version="v0.1",
            graph_version="g1", training_split="train",
            cost_snapshot_ids=["CST_X"], quantum_backend="aer",
            n_problems_distilled=5, mean_feasible_rate=0.1, deployable=True,
        )
        s = VBQEROptimizer(priors=[misleading]).solve(instance)
        assert s.objective <= s.classical_incumbent_objective + 1e-9

    def test_cost_snapshot_is_preserved(self, instance):
        s = VBQEROptimizer().solve(instance)
        assert s.cost_snapshot_id == instance.cost_snapshot_id


class TestMembers:
    def test_generates_multiple_candidates(self, instance):
        c = generate_candidates(instance, seed=1)
        assert len(c) >= 1
        assert all(len(x.tour) == instance.n_nodes for x in c)

    def test_deduplication_accumulates_consensus(self):
        t = [0, 1, 2, 3]
        merged = deduplicate([_cand("a", 10, t), _cand("b", 10, list(t))])
        assert len(merged) == 1
        assert merged[0].consensus == 2

    def test_rotated_tours_are_the_same_candidate(self):
        merged = deduplicate([_cand("a", 10, [0, 1, 2, 3]),
                              _cand("b", 10, [2, 3, 0, 1])])
        assert len(merged) == 1

    def test_diversity_is_zero_for_a_single_candidate(self):
        c = [_cand("a", 10, [0, 1, 2, 3])]
        compute_diversity(c)
        assert c[0].diversity == 0.0

    def test_diversity_is_positive_for_different_tours(self):
        c = [_cand("a", 10, [0, 1, 2, 3]), _cand("b", 11, [0, 3, 1, 2])]
        compute_diversity(c)
        assert all(x.diversity > 0 for x in c)

    def test_determinism_under_fixed_seed(self, instance):
        a = generate_candidates(instance, seed=11)
        b = generate_candidates(instance, seed=11)
        assert sorted(x.objective for x in a) == pytest.approx(
            sorted(x.objective for x in b))


class TestScorer:
    def test_lower_objective_wins_absent_other_signals(self):
        cands = [_cand("good", 10.0, [0, 1, 2]), _cand("bad", 100.0, [0, 2, 1])]
        assert score_candidates(cands)[0].candidate.candidate_id == "good"

    def test_infeasible_candidate_is_penalised(self):
        cands = [_cand("infeasible", 1.0, [0, 1, 2], feasible=False),
                 _cand("feasible", 50.0, [0, 2, 1])]
        assert score_candidates(cands)[0].candidate.candidate_id == "feasible"

    def test_signals_cannot_override_a_large_objective_gap(self):
        """The ensemble must optimize, not vote."""
        cands = [_cand("far_worse", 1000.0, [0, 1, 2], consensus=99, prior=1.0,
                       diversity=1.0),
                 _cand("best", 1.0, [0, 2, 1])]
        assert score_candidates(cands)[0].candidate.candidate_id == "best"

    def test_signal_influence_is_capped(self):
        cands = [_cand("a", 10.0, [0, 1, 2], consensus=50, prior=1.0, diversity=1.0),
                 _cand("b", 20.0, [0, 2, 1])]
        s = score_candidates(cands)[0]
        signal = sum(v for k, v in s.terms.items()
                     if k in ("consensus", "diversity", "quantum_prior"))
        assert abs(signal) <= MAX_SIGNAL_INFLUENCE + 1e-9

    def test_consensus_breaks_a_near_tie(self):
        cands = [_cand("solo", 100.0, [0, 1, 2]),
                 _cand("agreed", 100.0, [0, 2, 1], consensus=3)]
        assert score_candidates(cands)[0].candidate.candidate_id == "agreed"

    def test_normalisation_handles_identical_objectives(self):
        cands = [_cand("a", 5.0, [0, 1]), _cand("b", 5.0, [1, 0])]
        assert set(normalise_objectives(cands).values()) == {0.0}

    def test_empty_pool_returns_empty(self):
        assert score_candidates([]) == []


class TestQuantumPriors:
    def test_prior_application_is_counted(self):
        cands = [_cand("a", 10.0, [0, 1, 2])]
        n = apply_quantum_prior(cands, {"0->1": 0.9, "1->2": 0.8, "2->0": 0.7})
        assert n == 1
        assert cands[0].quantum_prior_score > 0
        assert cands[0].source == "quantum_informed"

    def test_empty_prior_touches_nothing(self):
        cands = [_cand("a", 10.0, [0, 1, 2])]
        assert apply_quantum_prior(cands, {}) == 0
        assert cands[0].quantum_prior_score == 0.0

    def test_distillation_normalises_to_unit_max(self):
        m = distil_marginals([({"a": 10, "b": 5}, {}), ({"a": 8, "b": 2}, {})],
                             energy_weighting=False)
        assert max(m.values()) == pytest.approx(1.0)
        assert m["a"] > m["b"]

    def test_distillation_of_nothing_is_empty(self):
        assert distil_marginals([]) == {}

    def test_validation_rejects_a_prior_that_does_not_help(self):
        p = QuantumPrior(
            artifact_id="p", artifact_version="v1", source="quantum_simulator",
            problem_family="f", variable_marginals={}, qaoa_params=None,
            n_layers=2, dataset_version="v0.1", graph_version="g1",
            training_split="train", cost_snapshot_ids=[], quantum_backend="aer",
            n_problems_distilled=3, mean_feasible_rate=0.1)
        # with_prior is worse (higher objective) on every held-out problem
        p = validate_prior(p, [(10.0, 12.0), (20.0, 25.0)])
        assert p.deployable is False
        assert p.validation["n_degraded"] == 2

    def test_validation_accepts_a_prior_that_helps(self):
        p = QuantumPrior(
            artifact_id="p2", artifact_version="v1", source="quantum_simulator",
            problem_family="f", variable_marginals={}, qaoa_params=None,
            n_layers=2, dataset_version="v0.1", graph_version="g1",
            training_split="train", cost_snapshot_ids=[], quantum_backend="aer",
            n_problems_distilled=3, mean_feasible_rate=0.1)
        p = validate_prior(p, [(10.0, 9.0), (20.0, 18.0)])
        assert p.deployable is True
        assert p.validation["improvement_rate"] == 1.0

    def test_validation_without_heldout_data_refuses_deployment(self):
        p = QuantumPrior(
            artifact_id="p3", artifact_version="v1", source="quantum_simulator",
            problem_family="f", variable_marginals={}, qaoa_params=None,
            n_layers=2, dataset_version="v0.1", graph_version="g1",
            training_split="train", cost_snapshot_ids=[], quantum_backend="aer",
            n_problems_distilled=3, mean_feasible_rate=0.1)
        p = validate_prior(p, [])
        assert p.deployable is False

    def test_unknown_artifact_source_is_rejected(self):
        p = QuantumPrior(
            artifact_id="p4", artifact_version="v1", source="wishful_thinking",
            problem_family="f", variable_marginals={}, qaoa_params=None,
            n_layers=2, dataset_version="v0.1", graph_version="g1",
            training_split="train", cost_snapshot_ids=["CST"],
            quantum_backend=None, n_problems_distilled=1,
            mean_feasible_rate=None, deployable=True)
        with pytest.raises(ValueError):
            save_prior(p)


class TestExplainability:
    def test_explanation_names_its_sources(self, instance):
        s = VBQEROptimizer().solve(instance)
        e = s.explanation
        assert "selected_candidate" in e and "reasons" in e
        assert e["quantum_hardware_called_live"] is False
        assert isinstance(e["reasons"], list) and e["reasons"]

    def test_no_quantum_claim_without_a_quantum_artifact(self, instance):
        s = VBQEROptimizer(priors=[]).solve(instance)
        joined = " ".join(s.explanation["reasons"]).lower()
        assert s.quantum_artifact_source == "none"
        # It must not claim a quantum contribution it did not make.
        assert "quantum-derived segment prior favoured" not in joined

    def test_row_serialisation_is_flat(self, instance):
        row = VBQEROptimizer().solve(instance).to_row()
        assert all(not isinstance(v, (list, dict)) for v in row.values())
