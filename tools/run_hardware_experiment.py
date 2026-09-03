"""Experiment H: execute one small QAOA circuit on IBM Quantum hardware.

This is an OFFLINE research activity, run deliberately and never from the live
request path. It submits a single 5-qubit circuit and records the full
provenance -- backend, job id, transpiled depth, feasible rate -- into
``Res/quantum/``.

Run:  python tools/run_hardware_experiment.py
"""

from __future__ import annotations

import json
import time

import numpy as np
from dotenv import load_dotenv

load_dotenv()

from routing.cache.result_store import ArtifactStore  # noqa: E402
from routing.quantum.decoder import decode_counts  # noqa: E402
from routing.quantum.ibm_runtime import IBMQuantumRunner  # noqa: E402
from routing.quantum.qaoa import build_qaoa_circuit, run_qaoa  # noqa: E402
from routing.quantum.qubo import brute_force_qubo, build_edge_selection_qubo  # noqa: E402
from vb.enums import Volatility  # noqa: E402

# The same diamond problem validated classically in the notebook, so the
# hardware result is directly comparable to a known optimum.
EDGES = [(0, 1), (1, 3), (0, 2), (2, 3), (0, 3)]
COSTS = np.array([2.0, 2.0, 1.0, 1.5, 9.0])
COST_SNAPSHOT = "CST_DEMO_DIAMOND"


def main() -> None:
    qubo = build_edge_selection_qubo(EDGES, COSTS, source=0, sink=3, n_nodes=4)
    _, optimum = brute_force_qubo(qubo)
    print(f"classical optimum: {optimum:.4f} (path 0->2->3)")

    # Optimize the parameters on a simulator first. Running the full variational
    # loop on hardware would consume enormous queue time for no scientific gain;
    # transferring simulator-optimized parameters and sampling once is the
    # standard, and honest, approach. It is recorded as such.
    print("optimizing QAOA parameters on the simulator...")
    sim = run_qaoa(qubo, p=1, shots=2048, seed=7, maxiter=60)
    print(f"  simulator best energy: {sim.best_energy:.4f}  "
          f"feasible rate: {sim.feasible_rate:.2%}")

    runner = IBMQuantumRunner()
    print(f"IBM status: {runner.status}")
    if not runner.available:
        print("BLOCKED: hardware unavailable. Nothing fabricated.")
        return

    backends = runner.list_backends(min_qubits=qubo.n_vars)
    print("backends:", [(b.name, b.pending_jobs) for b in backends])

    qc, params = build_qaoa_circuit(qubo, p=1)
    bound = qc.assign_parameters(dict(zip(params, sim.optimal_params)))

    backend = runner.least_busy(min_qubits=qubo.n_vars)
    print(f"submitting to {backend.name} ...")
    t0 = time.time()
    hw = runner.run_circuit(bound, shots=1024, backend=backend)
    print(f"elapsed {time.time() - t0:.0f}s")

    if not hw["executed"]:
        print(f"BLOCKED: {hw['reason']}")
        payload = {"executed": False, "reason": hw["reason"],
                   "simulator_reference": {"best_energy": sim.best_energy,
                                           "feasible_rate": sim.feasible_rate}}
    else:
        dec = decode_counts(hw["counts"], qubo)
        best = dec["best"]
        print(f"backend        : {hw['backend']}")
        print(f"job id         : {hw['job_id']}")
        print(f"transpiled depth: {hw['transpiled_depth']} "
              f"(logical {hw['logical_depth']})")
        print(f"feasible rate  : {dec['feasible_rate']:.2%}")
        print(f"best energy    : {best.energy if best else 'none feasible'}")
        print(f"decoded path   : {best.tour if best else None}")
        print(f"classical optimum: {optimum:.4f}")
        payload = {
            "executed": True,
            "backend": hw["backend"],
            "job_id": hw["job_id"],
            "shots": hw["shots"],
            "transpiled_depth": hw["transpiled_depth"],
            "logical_depth": hw["logical_depth"],
            "transpiled_n_qubits": hw["transpiled_n_qubits"],
            "logical_n_qubits": qubo.n_vars,
            "wall_clock_s": hw["wall_clock_s"],
            "feasible_rate": dec["feasible_rate"],
            "feasible_shots": dec["feasible_shots"],
            "total_shots": dec["total_shots"],
            "best_energy": best.energy if best else None,
            "decoded_path": best.tour if best else None,
            "classical_optimum": optimum,
            "matched_optimum": bool(best and abs(best.energy - optimum) < 1e-6),
            "parameters_source": (
                "optimized on a noiseless simulator, then transferred; the "
                "variational loop was NOT re-run on hardware"),
            "simulator_reference": {"best_energy": sim.best_energy,
                                    "feasible_rate": sim.feasible_rate},
            "counts_top10": dict(sorted(hw["counts"].items(),
                                        key=lambda kv: -kv[1])[:10]),
        }

    store = ArtifactStore()
    path = store.save(
        "quantum", "experiment_h_ibm_hardware", payload,
        instance_id="demo_diamond_graph", cost_snapshot_id=COST_SNAPSHOT,
        algorithm_family="quantum", algorithm_name="qaoa_p1_hardware",
        volatility=Volatility.STATIC,
    )
    print(f"\nsaved -> {path}")


if __name__ == "__main__":
    main()
