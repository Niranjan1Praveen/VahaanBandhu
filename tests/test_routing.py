"""Routing objective, candidate reduction, circular logistics and the engine."""

from __future__ import annotations

import numpy as np
import pytest

from routing.circular import evaluate_circular_trip, evaluate_direct_trip
from routing.classical.heuristics import (
    brute_force_tsp, nearest_neighbour, simulated_annealing, tour_cost, two_opt,
)
from routing.hybrid.candidate_reduction import (
    dominates, pareto_filter, reduce_candidates,
)
from routing.models import RouteCandidate, RoutingInstance
from routing.objective import DEFAULT_WEIGHTS, explain_selection, score_candidate, select_best


def candidate(rid, **kw):
    base = dict(
        route_id=rid, origin_id="O", destination_id="D",
        distance_km=100.0, travel_time_min=120.0, traffic_delay_min=0.0,
        toll_cost_inr=0.0, estimated_fuel_cost_inr=1800.0,
        road_risk_score=0.1, truck_accessibility_score=1.0,
    )
    base.update(kw)
    return RouteCandidate(**base)


class TestObjective:
    def test_shortest_route_is_not_always_selected(self):
        """The central product claim. A shorter route drowning in traffic must
        lose to a slightly longer free-flowing one."""
        short_jammed = candidate("short", distance_km=40, travel_time_min=50,
                                 traffic_delay_min=75)
        longer_clear = candidate("longer", distance_km=52, travel_time_min=58,
                                 traffic_delay_min=4)
        best, _, _ = select_best([short_jammed, longer_clear])
        assert best.route_id == "longer"

    def test_return_load_can_justify_a_longer_route(self):
        plain = candidate("plain", distance_km=60, travel_time_min=70,
                          empty_km=60, circular_logistics_score=0.0)
        circular = candidate("circular", distance_km=74, travel_time_min=86,
                             empty_km=8, circular_logistics_score=0.8)
        best, _, _ = select_best([plain, circular])
        assert best.route_id == "circular"

    def test_inaccessible_route_is_penalised(self):
        good = candidate("ok", distance_km=100)
        bad = candidate("bad", distance_km=60, truck_accessibility_score=0.0)
        best, _, _ = select_best([good, bad])
        assert best.route_id == "ok"

    def test_breakdown_terms_sum_to_total(self):
        b = score_candidate(candidate("x"))
        assert sum(b.terms.values()) == pytest.approx(b.total)

    def test_zero_weights_make_all_routes_tie(self):
        w = {k: 0.0 for k in DEFAULT_WEIGHTS}
        a = score_candidate(candidate("a", distance_km=10), w)
        b = score_candidate(candidate("b", distance_km=900), w)
        assert a.total == pytest.approx(b.total)

    def test_empty_candidate_list_is_rejected(self):
        with pytest.raises(ValueError):
            select_best([])

    def test_explanation_flags_a_near_tie(self):
        a = candidate("a", distance_km=100.0)
        b = candidate("b", distance_km=100.2)
        best, bd, ranking = select_best([a, b])
        exp = explain_selection(best, bd, ranking)
        assert not exp["margin_is_decisive"]

    def test_explanation_flags_a_clear_winner(self):
        a = candidate("a", distance_km=50.0)
        b = candidate("b", distance_km=300.0)
        best, bd, ranking = select_best([a, b])
        exp = explain_selection(best, bd, ranking)
        assert exp["margin_is_decisive"]
        assert exp["selected_route_id"] == "a"

    def test_objective_weights_match_the_dataset_definition(self):
        """Instances carry their weights; the engine has its own defaults. If
        these drift apart, offline benchmarks stop describing online behaviour."""
        from vb.generate.instances import DEFAULT_OBJECTIVE_WEIGHTS
        assert DEFAULT_WEIGHTS == DEFAULT_OBJECTIVE_WEIGHTS


class TestCandidateReduction:
    def test_dominated_candidate_is_removed(self):
        good = candidate("good", distance_km=50, travel_time_min=60,
                         estimated_fuel_cost_inr=900, road_risk_score=0.1)
        worse = candidate("worse", distance_km=80, travel_time_min=95,
                          estimated_fuel_cost_inr=1400, road_risk_score=0.3)
        assert dominates(good, worse)
        assert [c.route_id for c in pareto_filter([good, worse])] == ["good"]

    def test_non_dominated_tradeoffs_are_kept(self):
        fast = candidate("fast", distance_km=90, travel_time_min=70)
        short = candidate("short", distance_km=60, travel_time_min=110)
        kept = {c.route_id for c in pareto_filter([fast, short])}
        assert kept == {"fast", "short"}

    def test_reduction_reports_truncation(self):
        cands = [candidate(f"r{i}", distance_km=50 + i, travel_time_min=200 - i)
                 for i in range(20)]
        out, stats = reduce_candidates(cands, max_candidates=5)
        assert len(out) == 5
        assert stats["truncated_by_budget"]
        assert stats["truncation_may_discard_optimum"]

    def test_reduction_handles_empty_input(self):
        out, stats = reduce_candidates([])
        assert out == [] and stats["n_input"] == 0


class TestCircularLogistics:
    def test_return_load_reduces_empty_running(self):
        village, mandi = (29.0, 76.5), (29.4, 76.9)
        supplier, shop, home = (29.45, 76.95), (29.2, 76.7), (29.0, 76.5)
        direct = evaluate_direct_trip(village, mandi, home, 5.0, 9000, 4000)
        circ = evaluate_circular_trip(village, mandi, supplier, shop, home,
                                      5.0, 9000, 4000, 3000)
        assert circ.empty_km < direct.empty_km
        assert circ.avoided_empty_km > 0
        assert circ.truck_utilization > direct.truck_utilization

    def test_far_detour_is_rejected_as_not_worthwhile(self):
        """A 'return load' far off the homeward path is a separate job."""
        village, mandi, home = (29.0, 76.5), (29.4, 76.9), (29.0, 76.5)
        far_supplier, far_shop = (31.6, 74.8), (31.5, 74.9)  # Amritsar-ish
        circ = evaluate_circular_trip(village, mandi, far_supplier, far_shop,
                                      home, 5.0, 9000, 4000, 3000)
        assert not circ.worthwhile
        assert circ.circular_score == 0.0

    def test_score_is_zero_without_a_return_load(self):
        v, m, h = (29.0, 76.5), (29.4, 76.9), (29.0, 76.5)
        circ = evaluate_circular_trip(v, m, (29.42, 76.92), (29.2, 76.7), h,
                                      5.0, 9000, 4000, 0.0)
        assert circ.circular_score == 0.0

    def test_fuel_and_emissions_track_distance(self):
        v, m, h = (29.0, 76.5), (29.4, 76.9), (29.0, 76.5)
        d = evaluate_direct_trip(v, m, h, 5.0, 9000, 4000)
        # Both figures are rounded to 2dp for reporting, so compare with a
        # tolerance rather than exactly.
        assert d.fuel_litres == pytest.approx(d.total_km / 5.0, abs=0.01)
        assert d.co2_proxy_kg > 0


class TestClassicalSolvers:
    @pytest.fixture
    def D(self):
        rng = np.random.default_rng(0)
        pts = rng.uniform(0, 100, (7, 2))
        return np.linalg.norm(pts[:, None] - pts[None, :], axis=-1)

    def test_two_opt_never_worsens_the_tour(self, D):
        nn = nearest_neighbour(D)
        opt = two_opt(D, nn.tour)
        assert opt.cost <= nn.cost + 1e-9

    def test_heuristics_never_beat_the_exact_optimum(self, D):
        exact = brute_force_tsp(D)
        for r in (nearest_neighbour(D), simulated_annealing(D, seed=1)):
            assert r.cost >= exact.cost - 1e-6

    def test_every_node_is_visited_exactly_once(self, D):
        tour = nearest_neighbour(D).tour
        assert sorted(tour) == list(range(D.shape[0]))

    def test_exact_solver_refuses_oversized_instances(self):
        with pytest.raises(ValueError):
            brute_force_tsp(np.zeros((15, 15)), max_nodes=10)

    def test_tour_cost_closes_the_loop(self):
        D = np.array([[0, 1, 9], [1, 0, 2], [9, 2, 0]], float)
        assert tour_cost([0, 1, 2], D) == pytest.approx(1 + 2 + 9)


class TestRoutingInstanceValidation:
    def _instance(self, **over):
        n = 4
        D = np.ones((n, n)) * 5
        np.fill_diagonal(D, 0)
        kw = dict(
            instance_id="INS_TEST", problem_type="TSP", depot_index=0,
            node_ids=[f"LOC_{i}" for i in range(n)],
            coords=np.zeros((n, 2)), distance_matrix=D, time_matrix=D.copy(),
            demands=np.array([0.0, 100.0, 200.0, 150.0]),
            vehicle_capacities=[5000.0], time_windows=None,
            objective_weights=DEFAULT_WEIGHTS, cost_snapshot_id="CST_X",
            scenario_id="SCN_BASELINE", dataset_version="v0.1", graph_version="g1",
        )
        kw.update(over)
        return RoutingInstance(**kw)

    def test_valid_instance_passes(self):
        self._instance().validate()

    def test_nonzero_depot_demand_is_rejected(self):
        with pytest.raises(ValueError, match="depot"):
            self._instance(demands=np.array([50.0, 100.0, 200.0, 150.0])).validate()

    def test_nonzero_diagonal_is_rejected(self):
        D = np.ones((4, 4)) * 5
        with pytest.raises(ValueError, match="diagonal"):
            self._instance(distance_matrix=D).validate()

    def test_shape_mismatch_is_rejected(self):
        with pytest.raises(ValueError):
            self._instance(distance_matrix=np.zeros((3, 3))).validate()
