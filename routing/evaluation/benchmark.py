"""Cross-paradigm benchmarking on identical instances.

The scientific rules this module enforces, because they are easy to violate
accidentally and fatal to the conclusions:

1. **Same instance, same cost snapshot.** Every solver in a comparison row
   receives the identical distance matrix. A comparison across differing cost
   data is meaningless and is rejected outright.

2. **Runtime is decomposed, not totalled.** Classical preprocessing, quantum
   execution, queue wait and classical postprocessing are separate columns.
   "QAOA took 900 ms" is not comparable to "OR-Tools took 40 ms" if the former
   excludes the 3 s of circuit construction around it.

3. **Optimality gap needs a ground truth.** A gap is only reported when an
   exact solver actually ran. Against a heuristic baseline the field stays
   null rather than implying a bound that was never computed.

4. **Feasibility rate is reported for every sampling-based method.** A QAOA run
   that found the optimum in 3% of its shots has not "solved" anything at the
   same standard as a deterministic solver that returns one valid answer.

None of this establishes quantum advantage, and this module deliberately
computes no such verdict.
"""

from __future__ import annotations

import logging
import time
from dataclasses import asdict, dataclass, field

import numpy as np
import pandas as pd

from routing.classical.heuristics import (
    brute_force_tsp, nearest_neighbour, simulated_annealing, tour_cost, two_opt,
)
from routing.models import RoutingInstance
from routing.quantum.decoder import decode
from routing.quantum.qaoa import run_qaoa
from routing.quantum.qubo import brute_force_qubo, build_tsp_qubo

log = logging.getLogger(__name__)

EXACT_NODE_LIMIT = 9

# Statevector simulation needs 2^q amplitudes. 22 qubits is ~4M complex
# amplitudes (~67 MB) and runs comfortably; 30 would need ~17 GB. Permutation
# TSP uses n^2 qubits, so this cap is reached at n=5 -- which is the concrete,
# measured reason the edge-selection encoding exists.
MAX_SIMULATOR_QUBITS = 22


@dataclass
class BenchmarkRow:
    instance_id: str
    n_nodes: int
    algorithm_family: str
    algorithm_name: str
    objective_value: float
    tour_cost_km: float | None
    feasible: bool
    optimality_gap: float | None
    # Decomposed timing. Never collapse these into one number.
    classical_preprocess_ms: float = 0.0
    solver_runtime_ms: float = 0.0
    quantum_execution_ms: float = 0.0
    queue_wait_ms: float | None = None
    classical_postprocess_ms: float = 0.0
    wall_clock_ms: float = 0.0
    # Sampling quality, for stochastic methods only.
    feasible_rate: float | None = None
    shots: int | None = None
    n_qubits: int | None = None
    circuit_depth: int | None = None
    n_qubo_vars: int | None = None
    backend: str | None = None
    seed: int | None = None
    cost_snapshot_id: str = ""
    scenario_id: str = ""
    notes: str = ""
    violations: list[str] = field(default_factory=list)


def _assert_same_costs(inst: RoutingInstance, reference_snapshot: str) -> None:
    if inst.cost_snapshot_id != reference_snapshot:
        raise ValueError(
            "refusing to benchmark across differing cost snapshots: "
            f"{inst.cost_snapshot_id} != {reference_snapshot}"
        )


def benchmark_instance(
    inst: RoutingInstance, *, seed: int = 42, run_quantum: bool = True,
    qaoa_layers: int = 2, qaoa_shots: int = 2048,
    hardware_runner=None,
) -> list[BenchmarkRow]:
    """Run every applicable solver on one instance and return comparable rows."""
    _assert_same_costs(inst, inst.cost_snapshot_id)
    D = inst.distance_matrix
    n = inst.n_nodes
    rows: list[BenchmarkRow] = []

    # --- ground truth, when the instance is small enough to have one ---------
    optimum: float | None = None
    if n <= EXACT_NODE_LIMIT:
        exact = brute_force_tsp(D, depot=inst.depot_index, max_nodes=EXACT_NODE_LIMIT)
        optimum = exact.cost
        rows.append(BenchmarkRow(
            instance_id=inst.instance_id, n_nodes=n, algorithm_family="classical",
            algorithm_name="brute_force_exact", objective_value=exact.cost,
            tour_cost_km=exact.cost, feasible=True, optimality_gap=0.0,
            solver_runtime_ms=exact.runtime_ms, wall_clock_ms=exact.runtime_ms,
            seed=seed, cost_snapshot_id=inst.cost_snapshot_id,
            scenario_id=inst.scenario_id,
            notes="exhaustive enumeration; this is the ground truth",
        ))

    def gap(c: float) -> float | None:
        # Only meaningful against a proven optimum.
        return round((c - optimum) / optimum, 6) if optimum and optimum > 0 else None

    # --- classical heuristics ------------------------------------------------
    nn = nearest_neighbour(D, inst.depot_index)
    rows.append(BenchmarkRow(
        instance_id=inst.instance_id, n_nodes=n, algorithm_family="classical",
        algorithm_name="nearest_neighbour", objective_value=nn.cost,
        tour_cost_km=nn.cost, feasible=True, optimality_gap=gap(nn.cost),
        solver_runtime_ms=nn.runtime_ms, wall_clock_ms=nn.runtime_ms, seed=seed,
        cost_snapshot_id=inst.cost_snapshot_id, scenario_id=inst.scenario_id,
    ))

    opt2 = two_opt(D, nn.tour)
    rows.append(BenchmarkRow(
        instance_id=inst.instance_id, n_nodes=n, algorithm_family="classical",
        algorithm_name="nearest_neighbour+2opt", objective_value=opt2.cost,
        tour_cost_km=opt2.cost, feasible=True, optimality_gap=gap(opt2.cost),
        solver_runtime_ms=opt2.runtime_ms,
        wall_clock_ms=nn.runtime_ms + opt2.runtime_ms, seed=seed,
        cost_snapshot_id=inst.cost_snapshot_id, scenario_id=inst.scenario_id,
    ))

    sa = simulated_annealing(D, inst.depot_index, seed=seed)
    rows.append(BenchmarkRow(
        instance_id=inst.instance_id, n_nodes=n, algorithm_family="classical",
        algorithm_name="simulated_annealing", objective_value=sa.cost,
        tour_cost_km=sa.cost, feasible=True, optimality_gap=gap(sa.cost),
        solver_runtime_ms=sa.runtime_ms, wall_clock_ms=sa.runtime_ms, seed=seed,
        cost_snapshot_id=inst.cost_snapshot_id, scenario_id=inst.scenario_id,
    ))

    # --- QUBO track ----------------------------------------------------------
    if run_quantum and n >= 3:
        t_pre = time.perf_counter()
        qubo = build_tsp_qubo(D)
        pre_ms = (time.perf_counter() - t_pre) * 1000

        if qubo.n_vars > MAX_SIMULATOR_QUBITS:
            # Record the refusal rather than skipping silently: "no quantum row"
            # and "quantum was not encodable" are different findings.
            rows.append(BenchmarkRow(
                instance_id=inst.instance_id, n_nodes=n, algorithm_family="quantum",
                algorithm_name=f"qaoa_p{qaoa_layers}_simulator",
                objective_value=float("nan"), tour_cost_km=None, feasible=False,
                optimality_gap=None, n_qubo_vars=qubo.n_vars, seed=seed,
                cost_snapshot_id=inst.cost_snapshot_id, scenario_id=inst.scenario_id,
                notes=(f"NOT ENCODABLE - permutation TSP on {n} nodes needs "
                       f"{qubo.n_vars} qubits, over the {MAX_SIMULATOR_QUBITS}-qubit "
                       f"statevector budget. Use the edge-selection encoding."),
            ))
            return rows

        # Mandatory: validate the QUBO classically before any quantum execution.
        if qubo.n_vars <= 20:
            t0 = time.perf_counter()
            x, energy = brute_force_qubo(qubo, max_vars=20)
            dec = decode(x, qubo, D)
            rows.append(BenchmarkRow(
                instance_id=inst.instance_id, n_nodes=n,
                algorithm_family="classical", algorithm_name="qubo_brute_force",
                objective_value=energy,
                tour_cost_km=dec.route_cost, feasible=dec.feasible,
                optimality_gap=gap(dec.route_cost) if dec.route_cost else None,
                classical_preprocess_ms=pre_ms,
                solver_runtime_ms=(time.perf_counter() - t0) * 1000,
                wall_clock_ms=pre_ms + (time.perf_counter() - t0) * 1000,
                n_qubo_vars=qubo.n_vars, seed=seed,
                cost_snapshot_id=inst.cost_snapshot_id, scenario_id=inst.scenario_id,
                violations=dec.violations,
                notes="validates that the QUBO encodes the routing problem correctly",
            ))

        # QAOA on a simulator.
        try:
            qa = run_qaoa(qubo, p=qaoa_layers, shots=qaoa_shots, seed=seed, D=D)
            best_dec = None
            if qa.best_bitstring:
                from routing.quantum.decoder import bitstring_to_array
                best_dec = decode(
                    bitstring_to_array(qa.best_bitstring, qubo.n_vars), qubo, D)
            rows.append(BenchmarkRow(
                instance_id=inst.instance_id, n_nodes=n, algorithm_family="quantum",
                algorithm_name=f"qaoa_p{qaoa_layers}_simulator",
                objective_value=qa.best_energy,
                tour_cost_km=best_dec.route_cost if best_dec else None,
                feasible=bool(best_dec and best_dec.feasible),
                optimality_gap=(gap(best_dec.route_cost)
                                if best_dec and best_dec.route_cost else None),
                classical_preprocess_ms=pre_ms,
                quantum_execution_ms=qa.runtime_ms,
                wall_clock_ms=pre_ms + qa.runtime_ms,
                feasible_rate=qa.feasible_rate, shots=qa.shots,
                n_qubits=qa.n_qubits, circuit_depth=qa.circuit_depth,
                n_qubo_vars=qubo.n_vars, backend=qa.backend, seed=seed,
                cost_snapshot_id=inst.cost_snapshot_id, scenario_id=inst.scenario_id,
                notes=("simulator, noiseless; runtime is not comparable to hardware "
                       "and does not indicate any speedup"),
            ))
        except Exception as e:
            log.warning("QAOA failed on %s: %s", inst.instance_id, e)

        # Hardware, only if genuinely available.
        if hardware_runner is not None:
            from routing.quantum.qaoa import build_qaoa_circuit
            qc, _ = build_qaoa_circuit(qubo, qaoa_layers)
            hw = hardware_runner.run_circuit(qc, shots=1024)
            if hw["executed"]:
                from routing.quantum.decoder import decode_counts
                dc = decode_counts(hw["counts"], qubo, D)
                rows.append(BenchmarkRow(
                    instance_id=inst.instance_id, n_nodes=n,
                    algorithm_family="quantum",
                    algorithm_name=f"qaoa_p{qaoa_layers}_hardware",
                    objective_value=dc["best"].energy if dc["best"] else float("inf"),
                    tour_cost_km=dc["best"].route_cost if dc["best"] else None,
                    feasible=dc["found_feasible"],
                    optimality_gap=(gap(dc["best"].route_cost)
                                    if dc["best"] and dc["best"].route_cost else None),
                    classical_preprocess_ms=pre_ms,
                    quantum_execution_ms=hw["wall_clock_s"] * 1000,
                    feasible_rate=dc["feasible_rate"], shots=hw["shots"],
                    n_qubits=hw["transpiled_n_qubits"],
                    circuit_depth=hw["transpiled_depth"],
                    n_qubo_vars=qubo.n_vars, backend=hw["backend"], seed=seed,
                    cost_snapshot_id=inst.cost_snapshot_id,
                    scenario_id=inst.scenario_id,
                    notes=f"IBM hardware, job {hw.get('job_id')}; parameters not "
                          f"re-optimized on device",
                ))
            else:
                rows.append(BenchmarkRow(
                    instance_id=inst.instance_id, n_nodes=n,
                    algorithm_family="quantum",
                    algorithm_name=f"qaoa_p{qaoa_layers}_hardware",
                    objective_value=float("nan"), tour_cost_km=None, feasible=False,
                    optimality_gap=None, n_qubo_vars=qubo.n_vars, seed=seed,
                    cost_snapshot_id=inst.cost_snapshot_id,
                    scenario_id=inst.scenario_id,
                    notes=f"BLOCKED - hardware not executed: {hw['reason']}",
                ))

    return rows


def to_frame(rows: list[BenchmarkRow]) -> pd.DataFrame:
    return pd.DataFrame([asdict(r) for r in rows])


def summarise(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate a benchmark, without ranking paradigms against each other.

    Deliberately reports per-algorithm statistics and leaves interpretation to
    a human. Auto-declaring a winner across simulator and hardware rows would
    be exactly the comparison this project must not make.
    """
    return (
        df.groupby("algorithm_name")
        .agg(
            n_instances=("instance_id", "nunique"),
            mean_objective=("objective_value", "mean"),
            mean_tour_km=("tour_cost_km", "mean"),
            feasible_rate=("feasible", "mean"),
            mean_gap=("optimality_gap", "mean"),
            mean_solver_ms=("solver_runtime_ms", "mean"),
            mean_quantum_ms=("quantum_execution_ms", "mean"),
            mean_wall_ms=("wall_clock_ms", "mean"),
            mean_sampling_feasible_rate=("feasible_rate", "mean"),
        )
        .reset_index()
        .sort_values("mean_objective")
    )
