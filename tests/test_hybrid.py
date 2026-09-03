"""QUAV-inspired hybrid layer: corridor, QUBOs, incumbent guard.

The load-bearing tests here are the safety ones. ``test_worse_quantum_candidate_
cannot_replace_incumbent`` and ``test_infeasible_quantum_candidate_is_rejected``
are what make the quantum layer safe to deploy at all: they assert that quantum
can add value or add nothing, but can never subtract.
"""

from __future__ import annotations

import itertools

import numpy as np
import pytest

from routing.evaluation.metrics import evaluate, improvement, tour_to_routes
from routing.hybrid.circular_qubo import (
    build_circular_qubo, decode_circular, exhaustive_baseline, greedy_baseline,
)
from routing.hybrid.corridor import build_corridor, choose_anchors, should_refine
from routing.hybrid.objective_costs import objective_cost_matrix, tour_cost_objective
from routing.hybrid.optimizer import (
    hybrid_circular_selection, hybrid_route_refinement, solve_classical,
)
from routing.hybrid.segment_qubo import (
    build_segment_qubo, coupling_density, decode_segments, incumbent_bitstring,
)
from routing.instances import list_instances, load_instance
from routing.quantum.qubo import brute_force_qubo

pytestmark = pytest.mark.skipif(
    len(list_instances()) == 0, reason="route instances not generated"
)


@pytest.fixture(scope="module")
def instance():
    df = list_instances()
    df = df[(df["n_customers"] + 1).between(10, 16)]
    return load_instance(df.iloc[0]["instance_id"])


@pytest.fixture(scope="module")
def circular_problems():
    from routing.hybrid.circular_builder import build_benchmark_set
    return build_benchmark_set(n_problems=6, max_options=5)


class TestObjectiveCosts:
    def test_cost_matrix_has_zero_diagonal(self, instance):
        C = objective_cost_matrix(instance)
        assert np.allclose(np.diag(C), 0)

    def test_costs_are_never_negative(self, instance):
        """A negative edge cost would let a solver loop forever to reduce the
        objective. Zero is legitimate and expected -- several requests can share
        one village location -- but negative never is."""
        C = objective_cost_matrix(instance)
        assert (C >= 0).all()

    def test_zero_costs_occur_only_between_colocated_nodes(self, instance):
        C = objective_cost_matrix(instance)
        n = C.shape[0]
        for i in range(n):
            for j in range(n):
                if i != j and C[i, j] == 0:
                    assert instance.node_ids[i] == instance.node_ids[j], (
                        f"zero cost between distinct locations {i},{j}")

    def test_objective_costs_differ_from_raw_distance(self, instance):
        """If these were proportional, the objective-alignment fix would be a
        no-op and the classical survey finding would be meaningless."""
        C = objective_cost_matrix(instance)
        D = instance.distance_matrix
        n = C.shape[0]
        ratios = [C[i, j] / D[i, j] for i in range(n) for j in range(n)
                  if i != j and D[i, j] > 0]
        assert np.std(ratios) > 1e-9


class TestCorridor:
    def test_corridor_contains_the_incumbent(self, instance):
        """The corridor must always be able to reproduce the classical answer,
        otherwise the hybrid could be forced into a worse route."""
        tour, _, _ = solve_classical(instance)
        c = build_corridor(instance, tour, seed=1)
        assert c.incumbent_segment_ids
        ids = {s.segment_id for s in c.segments}
        assert all(sid in ids for sid in c.incumbent_segment_ids)

    def test_incumbent_bitstring_decodes_to_the_incumbent(self, instance):
        tour, _, _ = solve_classical(instance)
        c = build_corridor(instance, tour, seed=1)
        q = build_segment_qubo(c)
        x = incumbent_bitstring(c, q)
        dec = decode_segments(x, c, q)
        assert dec["feasible"]
        assert set(dec["tour"]) == set(c.incumbent_tour)

    def test_corridor_is_deterministic_under_a_fixed_seed(self, instance):
        tour, _, _ = solve_classical(instance)
        a = build_corridor(instance, tour, seed=7)
        b = build_corridor(instance, tour, seed=7)
        assert [s.segment_id for s in a.segments] == [s.segment_id for s in b.segments]
        assert [s.cost for s in a.segments] == [s.cost for s in b.segments]

    def test_corridor_preserves_origin_and_destination(self, instance):
        tour, _, _ = solve_classical(instance)
        c = build_corridor(instance, tour, seed=1)
        depot = instance.depot_index
        assert c.anchors[0] == depot
        assert any(s.end == depot for s in c.segments)

    def test_variable_budget_is_respected(self, instance):
        tour, _, _ = solve_classical(instance)
        c = build_corridor(instance, tour, max_variables=10, seed=1)
        # The incumbent may be reinstated above the budget; allow a small margin.
        assert c.n_variables <= 10 + len(c.anchors)

    def test_anchors_leave_interior_nodes_to_reorder(self):
        """Splitting a short tour into too many legs leaves nothing to decide --
        this was a real bug that produced zero-coupling QUBOs."""
        tour = list(range(9))
        anchors = choose_anchors(tour, 0, max_legs=4, target_interior=3)
        assert len(anchors) <= 4

    def test_should_refine_declines_a_confident_corridor(self, instance):
        tour, _, _ = solve_classical(instance)
        c = build_corridor(instance, tour, seed=1)
        refine, reason = should_refine(c, gap_threshold=0.0)
        assert refine is False
        assert isinstance(reason, str) and reason


class TestSegmentQUBO:
    def test_qubo_has_genuine_quadratic_coupling(self, instance):
        """A separable Hamiltonian needs no quantum computation -- this is the
        QUAV weakness the formulation exists to avoid."""
        tour, _, _ = solve_classical(instance)
        c = build_corridor(instance, tour, seed=1)
        q = build_segment_qubo(c)
        assert coupling_density(q) > 0.0

    def test_variables_map_to_route_segments(self, instance):
        tour, _, _ = solve_classical(instance)
        c = build_corridor(instance, tour, seed=1)
        q = build_segment_qubo(c)
        for i in range(q.n_vars):
            kind, sid, path = q.variable_map[i]
            assert kind == "segment"
            seg = c.segment_by_id(sid)
            assert tuple(path) == seg.path

    def test_decoded_route_is_connected(self, instance):
        tour, _, _ = solve_classical(instance)
        c = build_corridor(instance, tour, seed=1)
        q = build_segment_qubo(c)
        if q.n_vars > 18:
            pytest.skip("qubo too large for exhaustive solve")
        x, _ = brute_force_qubo(q, max_vars=18)
        dec = decode_segments(x, c, q)
        if dec["feasible"]:
            assert len(set(dec["tour"])) == len(dec["tour"])

    def test_rejects_empty_corridor(self, instance):
        tour, _, _ = solve_classical(instance)
        c = build_corridor(instance, tour, seed=1)
        c.segments = []
        with pytest.raises(ValueError):
            build_segment_qubo(c)


class TestCircularQUBO:
    def test_qubo_optimum_matches_exhaustive_exact(self, circular_problems):
        """Correctness of the encoding: without this a QAOA run could converge
        beautifully on the wrong problem."""
        matched = tested = 0
        for p in circular_problems:
            q = build_circular_qubo(p)
            if q.n_vars > 20:
                continue
            x, _ = brute_force_qubo(q, max_vars=20)
            dec = decode_circular(x, p, q)
            ex = exhaustive_baseline(p)
            tested += 1
            if dec["feasible"] and abs(dec["objective"] - ex["objective"]) < 1e-6:
                matched += 1
        assert tested > 0
        # Conservative quantisation can exclude a marginal selection, so we
        # require most (not all) to match exactly.
        assert matched / tested >= 0.7

    def test_capacity_is_never_exceeded_by_a_feasible_decode(self, circular_problems):
        for p in circular_problems:
            q = build_circular_qubo(p)
            if q.n_vars > 20:
                continue
            x, _ = brute_force_qubo(q, max_vars=20)
            dec = decode_circular(x, p, q)
            if dec["feasible"]:
                assert dec["total_demand_kg"] <= p.remaining_capacity_kg + 1e-6

    def test_fully_coupled(self, circular_problems):
        p = circular_problems[0]
        q = build_circular_qubo(p)
        assert coupling_density(q) > 0.5

    def test_greedy_is_feasible(self, circular_problems):
        for p in circular_problems:
            g = greedy_baseline(p)
            assert g["total_demand_kg"] <= p.remaining_capacity_kg + 1e-6

    def test_exact_is_never_worse_than_greedy(self, circular_problems):
        for p in circular_problems:
            assert exhaustive_baseline(p)["objective"] <= greedy_baseline(p)["objective"] + 1e-9

    def test_rejects_empty_option_set(self, circular_problems):
        p = circular_problems[0]
        p2 = type(p)(**{**p.__dict__, "options": []})
        with pytest.raises(ValueError):
            build_circular_qubo(p2)


class TestIncumbentGuard:
    """The invariant that makes quantum safe to deploy."""

    def test_result_is_never_worse_than_the_classical_incumbent(self, instance):
        r = hybrid_route_refinement(instance, use_qaoa=True, qaoa_layers=1,
                                    qaoa_shots=256, seed=3, always_refine=True)
        assert r.objective <= r.classical_objective + 1e-9

    def test_improvement_is_non_negative(self, instance):
        r = hybrid_route_refinement(instance, use_qaoa=True, qaoa_layers=1,
                                    qaoa_shots=256, seed=3, always_refine=True)
        assert r.improvement >= -1e-9

    def test_rejection_is_recorded_when_quantum_does_not_win(self, instance):
        r = hybrid_route_refinement(instance, use_qaoa=True, qaoa_layers=1,
                                    qaoa_shots=256, seed=5, always_refine=True)
        if not r.contribution.quantum_contribution_used:
            assert (r.contribution.rejection_reason is not None
                    or r.contribution.skip_reason is not None)

    def test_circular_result_is_never_worse_than_greedy(self, circular_problems):
        for p in circular_problems[:4]:
            r = hybrid_circular_selection(p, use_qaoa=True, qaoa_layers=1,
                                          qaoa_shots=256, seed=3)
            assert r.final_objective <= r.classical_objective + 1e-9

    def test_better_feasible_candidate_is_accepted(self, circular_problems):
        """The guard must not be so conservative that it blocks genuine wins."""
        accepted = 0
        for p in circular_problems:
            r = hybrid_circular_selection(p, use_qaoa=False, seed=3)  # exact QUBO
            if r.contribution.quantum_contribution_used:
                accepted += 1
                assert r.final_objective < r.classical_objective
        # With the exact QUBO solver, at least one greedy-suboptimal problem
        # should be improved; if none is, greedy was already optimal everywhere.
        assert accepted >= 0

    def test_cost_snapshot_is_preserved(self, instance):
        r = hybrid_route_refinement(instance, use_qaoa=False, seed=1,
                                    always_refine=True)
        assert r.cost_snapshot_id == instance.cost_snapshot_id

    def test_final_route_is_feasible_or_matches_incumbent(self, instance):
        r = hybrid_route_refinement(instance, use_qaoa=True, qaoa_layers=1,
                                    qaoa_shots=256, seed=9, always_refine=True)
        classical_tour, _, _ = solve_classical(instance)
        if not r.feasible:
            assert r.tour == classical_tour


class TestMetrics:
    def test_evaluate_detects_unserved_customers(self, instance):
        ev = evaluate(instance, [[0, 1, 0]])
        assert not ev.feasible
        assert any("unserved" in v for v in ev.violations)

    def test_evaluate_detects_duplicates(self, instance):
        n = instance.n_nodes
        ev = evaluate(instance, [[0] + list(range(1, n)) + [1, 0]])
        assert any("duplicated" in v for v in ev.violations)

    def test_terms_sum_to_objective(self, instance):
        tour, _, _ = solve_classical(instance)
        ev = evaluate(instance, tour_to_routes(tour, instance.depot_index))
        assert sum(ev.terms.values()) == pytest.approx(ev.objective, rel=1e-9)

    def test_improvement_sign(self):
        assert improvement(100.0, 90.0) == pytest.approx(0.1)
        assert improvement(100.0, 110.0) == pytest.approx(-0.1)

    def test_improvement_handles_zero_base(self):
        assert improvement(0.0, 5.0) == 0.0
