"""QAOA for VahaanBandhu routing QUBOs.

Circuit structure follows the standard alternating-operator ansatz, and matches
the one described in Innan et al., QUAV (arXiv 2508.21361): Hadamard
initialisation, a cost layer exp(-i*gamma*H_C), a transverse-field mixer layer
exp(-i*beta*H_B), repeated for p layers.

Where we differ from that paper, deliberately: our cost Hamiltonian carries
ZZ couplings from the flow-conservation and one-hot constraints, not just
single-qubit Z terms. A purely linear H_C is separable and needs no quantum
computation at all, so the two-qubit terms are what make running QAOA a
meaningful thing to do here.

Learned parameters are the reusable artifact. Good (gamma, beta) values
transfer across instances drawn from the same problem family, which is what
lets an offline hardware run contribute to online routing without the live
path ever calling a QPU.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
from qiskit_aer import AerSimulator
from scipy.optimize import minimize

from routing.quantum.decoder import bitstring_to_array, decode_counts
from routing.quantum.qubo import QUBO

QAOA_VERSION = "qaoa_v1"


@dataclass
class QAOAResult:
    best_bitstring: str | None
    best_energy: float
    optimal_params: list[float]
    n_layers: int
    n_qubits: int
    circuit_depth: int
    shots: int
    optimizer: str
    n_iterations: int
    cost_history: list[float]
    runtime_ms: float
    backend: str
    feasible_rate: float
    counts: dict[str, int] = field(default_factory=dict)
    decoded: dict = field(default_factory=dict)


def build_qaoa_circuit(qubo: QUBO, p: int) -> tuple[QuantumCircuit, list[Parameter]]:
    """Parameterised QAOA circuit for a QUBO, via its Ising form."""
    h, J, _ = qubo.to_ising()
    n = qubo.n_vars

    gammas = [Parameter(f"g{i}") for i in range(p)]
    betas = [Parameter(f"b{i}") for i in range(p)]

    qc = QuantumCircuit(n, n)
    qc.h(range(n))  # equal superposition over all candidate configurations

    for layer in range(p):
        g = gammas[layer]
        # Single-qubit Z terms.
        for i in range(n):
            if h[i] != 0:
                qc.rz(2 * g * h[i], i)
        # ZZ couplings: CNOT - RZ - CNOT. These are the entangling operations
        # that a purely linear cost Hamiltonian would not require.
        for i in range(n):
            for j in range(i + 1, n):
                if J[i, j] != 0:
                    qc.cx(i, j)
                    qc.rz(2 * g * J[i, j], j)
                    qc.cx(i, j)
        qc.barrier()
        qc.rx(2 * betas[layer], range(n))
        qc.barrier()

    qc.measure(range(n), range(n))
    return qc, gammas + betas


def _expectation(counts: dict[str, int], qubo: QUBO) -> float:
    total = sum(counts.values())
    return sum(
        shots * qubo.energy(bitstring_to_array(bits, qubo.n_vars))
        for bits, shots in counts.items()
    ) / total


def run_qaoa(
    qubo: QUBO, *, p: int = 2, shots: int = 2048, seed: int = 42,
    maxiter: int = 80, optimizer: str = "COBYLA",
    initial_params: list[float] | None = None,
    backend=None, D: np.ndarray | None = None, decode_fn=None,
) -> QAOAResult:
    """Run QAOA on a simulator (or a supplied backend) and decode the result.

    Args:
        initial_params: Warm-start (gamma, beta) values, typically loaded from
            a previous run on the same problem family. This is the mechanism by
            which offline hardware experiments pay off online.
    """
    t0 = time.perf_counter()
    backend = backend or AerSimulator(seed_simulator=seed)
    qc, params = build_qaoa_circuit(qubo, p)
    transpiled_depth = qc.decompose().depth()

    if initial_params is not None:
        if len(initial_params) != 2 * p:
            raise ValueError(f"expected {2 * p} initial parameters, got {len(initial_params)}")
        x0 = np.array(initial_params, dtype=float)
    else:
        rng = np.random.default_rng(seed)
        x0 = np.concatenate([rng.uniform(0, np.pi, p), rng.uniform(0, np.pi / 2, p)])

    history: list[float] = []

    def objective(theta: np.ndarray) -> float:
        bound = qc.assign_parameters(dict(zip(params, theta)))
        counts = backend.run(bound, shots=shots, seed_simulator=seed).result().get_counts()
        e = _expectation(counts, qubo)
        history.append(e)
        return e

    res = minimize(objective, x0, method=optimizer, options={"maxiter": maxiter})

    final = qc.assign_parameters(dict(zip(params, res.x)))
    counts = backend.run(final, shots=shots, seed_simulator=seed).result().get_counts()
    decoded = decode_counts(counts, qubo, D, decode_fn=decode_fn)

    best_bits = decoded["best_bitstring"]
    best_energy = decoded["best"].energy if decoded["best"] else float("inf")

    return QAOAResult(
        best_bitstring=best_bits,
        best_energy=best_energy,
        optimal_params=[float(v) for v in res.x],
        n_layers=p,
        n_qubits=qubo.n_vars,
        circuit_depth=transpiled_depth,
        shots=shots,
        optimizer=optimizer,
        n_iterations=len(history),
        cost_history=history,
        runtime_ms=(time.perf_counter() - t0) * 1000,
        backend=getattr(backend, "name", str(backend)),
        feasible_rate=decoded["feasible_rate"],
        counts=counts,
        decoded={k: v for k, v in decoded.items() if k != "best"},
    )
