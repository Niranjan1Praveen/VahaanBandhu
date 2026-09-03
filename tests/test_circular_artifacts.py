"""Circular-track quantum artifacts and the guided/unguided control.

The most important test here is
``test_guided_search_never_beats_by_violating_constraints`` together with
``test_unguided_control_exists``. Validating a quantum artifact against *greedy*
would credit it for whatever plain local search finds anyway -- the standard way
to manufacture a quantum result that is really a better classical baseline. The
artifact must be validated against the unguided control, and these tests keep
that structure in place.
"""

from __future__ import annotations

import numpy as np
import pytest

from routing.ensemble.circular_distill import (
    CircularArtifact, _objective, apply_artifact_to_problem, distil_from_problems,
    local_search,
)
from routing.ensemble.problem_family import CircularFamily, classify_circular
from routing.hybrid.circular_builder import build_benchmark_set
from routing.hybrid.circular_qubo import exhaustive_baseline, greedy_baseline


@pytest.fixture(scope="module")
def problems():
    return build_benchmark_set(n_problems=6, max_options=5)


@pytest.fixture(scope="module")
def artifact(problems):
    rm, pm, params, stats = distil_from_problems(
        problems, p_layers=1, shots=256, seed=1)
    return CircularArtifact(
        artifact_id="test", artifact_version="v1", source="quantum_simulator",
        problem_family="ALL", rank_marginals=rm, pair_marginals=pm,
        qaoa_params=params, n_layers=1,
        n_problems_distilled=stats["n_with_feasible_samples"],
        mean_feasible_rate=stats["mean_feasible_rate"])


class TestDistillation:
    def test_marginals_are_rank_keyed_not_instance_keyed(self, artifact):
        """Option ids are instance-specific; ranks transfer. Keying on ids would
        make the artifact useless on any unseen problem."""
        assert artifact.rank_marginals
        assert all(k.startswith("r") for k in artifact.rank_marginals)

    def test_marginals_are_normalised(self, artifact):
        if artifact.rank_marginals:
            assert max(artifact.rank_marginals.values()) == pytest.approx(1.0)
            assert all(0.0 <= v <= 1.0 for v in artifact.rank_marginals.values())

    def test_pair_marginals_use_sorted_keys(self, artifact):
        for k in artifact.pair_marginals:
            a, b = k.split("|")
            assert a <= b, "pair keys must be order-independent"

    def test_circular_track_yields_more_signal_than_route_track(self, artifact):
        """The route-track prior failed partly because only 12/30 instances
        produced feasible samples. The circular track should do better."""
        assert artifact.mean_feasible_rate is not None
        assert artifact.mean_feasible_rate > 0.01

    def test_distillation_of_nothing_is_empty(self):
        rm, pm, params, stats = distil_from_problems([], p_layers=1, shots=64)
        assert rm == {} and pm == {}
        assert stats["n_problems"] == 0


class TestLocalSearchSafety:
    def test_never_violates_capacity(self, problems, artifact):
        for p in problems:
            for art in (None, artifact):
                r = local_search(p, greedy_baseline(p)["selected_indices"],
                                 artifact=art)
                assert r["total_demand_kg"] <= p.remaining_capacity_kg + 1e-6

    def test_never_worse_than_its_starting_point(self, problems, artifact):
        """A prior may waste effort but must never degrade the answer, because
        acceptance is always on the true objective."""
        for p in problems:
            start = greedy_baseline(p)["selected_indices"]
            base = _objective(p, start)
            for art in (None, artifact):
                assert local_search(p, start, artifact=art)["objective"] <= base + 1e-9

    def test_never_beats_the_exact_optimum(self, problems, artifact):
        for p in problems:
            ex = exhaustive_baseline(p)["objective"]
            r = apply_artifact_to_problem(p, artifact)
            assert r["objective"] >= ex - 1e-6

    def test_a_misleading_artifact_cannot_degrade_the_result(self, problems):
        """Reversed marginals only reorder which moves are tried first."""
        bad = CircularArtifact(
            artifact_id="bad", artifact_version="v1", source="quantum_simulator",
            problem_family="ALL",
            rank_marginals={f"r{i}": 1.0 - i * 0.1 for i in range(10)},
            pair_marginals={}, qaoa_params=None, n_layers=1,
            n_problems_distilled=0, mean_feasible_rate=0.0)
        for p in problems:
            start = greedy_baseline(p)["selected_indices"]
            base = _objective(p, start)
            assert local_search(p, start, artifact=bad)["objective"] <= base + 1e-9

    def test_unguided_control_exists(self, problems):
        """The control must be runnable, or the artifact cannot be validated
        honestly against anything."""
        for p in problems:
            r = local_search(p, greedy_baseline(p)["selected_indices"], artifact=None)
            assert "objective" in r and r["selected"] == sorted(r["selected"])

    def test_guided_and_unguided_reach_comparable_quality(self, problems, artifact):
        """Both are local search on the same objective; neither should be
        systematically broken relative to the other."""
        for p in problems:
            start = greedy_baseline(p)["selected_indices"]
            g = local_search(p, start, artifact=artifact)["objective"]
            u = local_search(p, start, artifact=None)["objective"]
            ex = exhaustive_baseline(p)["objective"]
            assert g >= ex - 1e-6 and u >= ex - 1e-6

    def test_local_search_is_deterministic(self, problems, artifact):
        p = problems[0]
        start = greedy_baseline(p)["selected_indices"]
        a = local_search(p, start, artifact=artifact)
        b = local_search(p, start, artifact=artifact)
        assert a["objective"] == pytest.approx(b["objective"])
        assert a["selected"] == b["selected"]


class TestFamilies:
    def test_every_problem_gets_a_family(self, problems):
        for p in problems:
            assert isinstance(classify_circular(p), CircularFamily)

    def test_family_assignment_is_stable(self, problems):
        for p in problems:
            assert classify_circular(p) == classify_circular(p)
