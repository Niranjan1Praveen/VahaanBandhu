"""QUBO correctness, decoding, and QAOA reproducibility.

The critical test here is ``test_qubo_optimum_equals_true_optimum``: it proves
the QUBO actually encodes the routing problem. Without it, a QAOA run could
converge beautifully on the wrong problem and nobody would notice.
"""

from __future__ import annotations

import itertools

import numpy as np
import pytest

from routing.classical.heuristics import brute_force_tsp, tour_cost
from routing.quantum.decoder import bitstring_to_array, decode, decode_counts
from routing.quantum.qaoa import build_qaoa_circuit, run_qaoa
from routing.quantum.qubo import (
    brute_force_qubo, build_edge_selection_qubo, build_tsp_qubo,
)


@pytest.fixture
def diamond():
    """0 -> {1, 2} -> 3, plus an expensive direct link.
    Cheapest path is 0->2->3 at cost 2.5."""
    edges = [(0, 1), (1, 3), (0, 2), (2, 3), (0, 3)]
    costs = np.array([2.0, 2.0, 1.0, 1.5, 9.0])
    return edges, costs


@pytest.fixture
def small_tsp():
    return np.array([
        [0.0, 3.0, 5.0, 8.0],
        [3.0, 0.0, 4.0, 6.0],
        [5.0, 4.0, 0.0, 2.0],
        [8.0, 6.0, 2.0, 0.0],
    ])


class TestEdgeSelectionQUBO:
    def test_optimum_is_the_true_shortest_path(self, diamond):
        edges, costs = diamond
        q = build_edge_selection_qubo(edges, costs, 0, 3, 4)
        x, energy = brute_force_qubo(q)
        dec = decode(x, q)
        assert dec.feasible
        assert dec.tour == [0, 2, 3]
        assert energy == pytest.approx(2.5)

    def test_energy_of_optimum_equals_path_cost(self, diamond):
        """No penalty residue at the optimum: a feasible solution's energy is
        exactly its route cost, which is what makes energies interpretable."""
        edges, costs = diamond
        q = build_edge_selection_qubo(edges, costs, 0, 3, 4)
        _, energy = brute_force_qubo(q)
        assert energy == pytest.approx(2.5)

    def test_infeasible_selections_cost_more_than_any_feasible_one(self, diamond):
        """The penalty-method requirement. If violating flow conservation could
        ever be cheaper, the QUBO is invalid regardless of the solver."""
        edges, costs = diamond
        q = build_edge_selection_qubo(edges, costs, 0, 3, 4)
        feasible, infeasible = [], []
        for bits in itertools.product([0, 1], repeat=len(edges)):
            x = np.array(bits, dtype=float)
            (feasible if decode(x, q).feasible else infeasible).append(q.energy(x))
        assert feasible and infeasible
        assert max(feasible) < min(infeasible)

    def test_has_genuine_quadratic_coupling(self, diamond):
        """A purely linear cost Hamiltonian is separable and needs no quantum
        computation. Flow conservation must produce real ZZ terms."""
        edges, costs = diamond
        q = build_edge_selection_qubo(edges, costs, 0, 3, 4)
        off_diag = q.Q[np.triu_indices_from(q.Q, k=1)]
        assert np.count_nonzero(off_diag) > 0

    def test_scales_with_edges_not_nodes_squared(self):
        edges = [(i, i + 1) for i in range(19)]
        q = build_edge_selection_qubo(edges, np.ones(19), 0, 19, 20)
        assert q.n_vars == 19  # not 400

    def test_rejects_empty_edge_set(self):
        with pytest.raises(ValueError):
            build_edge_selection_qubo([], np.array([]), 0, 1, 2)


class TestPermutationTSPQUBO:
    def test_optimum_matches_brute_force_tsp(self, small_tsp):
        q = build_tsp_qubo(small_tsp)
        x, _ = brute_force_qubo(q, max_vars=20)
        dec = decode(x, q, small_tsp)
        exact = brute_force_tsp(small_tsp)
        assert dec.feasible
        assert dec.route_cost == pytest.approx(exact.cost)

    def test_qubit_count_is_n_squared(self, small_tsp):
        assert build_tsp_qubo(small_tsp).n_vars == 16

    def test_rejects_tiny_instances(self):
        with pytest.raises(ValueError):
            build_tsp_qubo(np.zeros((2, 2)))


class TestIsingConversion:
    def test_ising_energies_match_qubo_energies(self, diamond):
        edges, costs = diamond
        q = build_edge_selection_qubo(edges, costs, 0, 3, 4)
        h, J, offset = q.to_ising()
        for bits in itertools.product([0, 1], repeat=q.n_vars):
            x = np.array(bits, dtype=float)
            z = 1 - 2 * x  # x=0 -> z=+1, x=1 -> z=-1
            ising = float(h @ z + z @ J @ z + offset)
            assert ising == pytest.approx(q.energy(x), abs=1e-8)


class TestDecoder:
    def test_rejects_disconnected_edge_sets(self, diamond):
        edges, costs = diamond
        q = build_edge_selection_qubo(edges, costs, 0, 3, 4)
        x = np.zeros(5)
        x[1] = 1  # edge (1,3) alone: never reaches the source
        dec = decode(x, q)
        assert not dec.feasible

    def test_rejects_empty_selection(self, diamond):
        edges, costs = diamond
        q = build_edge_selection_qubo(edges, costs, 0, 3, 4)
        dec = decode(np.zeros(5), q)
        assert not dec.feasible
        assert "no_edges_selected" in dec.violations

    def test_rejects_invalid_permutation(self, small_tsp):
        q = build_tsp_qubo(small_tsp)
        dec = decode(np.ones(16), q, small_tsp)  # every node at every position
        assert not dec.feasible

    def test_bitstring_endianness_roundtrip(self):
        # Qiskit is little-endian: leftmost character is the highest qubit.
        assert list(bitstring_to_array("0011", 4)) == [1.0, 1.0, 0.0, 0.0]

    def test_decode_counts_reports_feasible_rate(self, diamond):
        edges, costs = diamond
        q = build_edge_selection_qubo(edges, costs, 0, 3, 4)
        counts = {"00000": 900, "01100": 100}  # mostly junk
        out = decode_counts(counts, q)
        assert out["total_shots"] == 1000
        assert 0.0 <= out["feasible_rate"] <= 1.0


class TestQAOA:
    def test_circuit_shape(self, diamond):
        edges, costs = diamond
        q = build_edge_selection_qubo(edges, costs, 0, 3, 4)
        qc, params = build_qaoa_circuit(q, p=2)
        assert qc.num_qubits == q.n_vars
        assert len(params) == 4  # 2 gammas + 2 betas

    def test_circuit_contains_entangling_gates(self, diamond):
        """If the cost Hamiltonian produced no CNOTs, QAOA would be pointless."""
        edges, costs = diamond
        q = build_edge_selection_qubo(edges, costs, 0, 3, 4)
        qc, _ = build_qaoa_circuit(q, p=1)
        assert qc.count_ops().get("cx", 0) > 0

    def test_same_seed_reproduces_the_run(self, diamond):
        edges, costs = diamond
        q = build_edge_selection_qubo(edges, costs, 0, 3, 4)
        a = run_qaoa(q, p=1, shots=512, seed=3, maxiter=12)
        b = run_qaoa(q, p=1, shots=512, seed=3, maxiter=12)
        assert a.best_bitstring == b.best_bitstring
        assert a.optimal_params == pytest.approx(b.optimal_params)

    def test_finds_optimum_on_a_tiny_problem(self, diamond):
        edges, costs = diamond
        q = build_edge_selection_qubo(edges, costs, 0, 3, 4)
        _, optimum = brute_force_qubo(q)
        r = run_qaoa(q, p=3, shots=2048, seed=7, maxiter=60)
        assert r.best_energy == pytest.approx(optimum, abs=1e-6)

    def test_reports_feasible_rate_honestly(self, diamond):
        """Most QAOA shots violate constraints. That must be visible, not
        hidden behind the single best sample."""
        edges, costs = diamond
        q = build_edge_selection_qubo(edges, costs, 0, 3, 4)
        r = run_qaoa(q, p=2, shots=1024, seed=5, maxiter=25)
        assert 0.0 <= r.feasible_rate <= 1.0
        assert r.n_qubits == 5
        assert r.circuit_depth > 0

    def test_rejects_wrong_number_of_warm_start_params(self, diamond):
        edges, costs = diamond
        q = build_edge_selection_qubo(edges, costs, 0, 3, 4)
        with pytest.raises(ValueError):
            run_qaoa(q, p=2, initial_params=[0.1], maxiter=2)
