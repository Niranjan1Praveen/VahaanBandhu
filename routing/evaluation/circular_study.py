"""Circular return-load study: the quantum component inside VB-QER.

Research framing (per the fixed architecture): this asks **how to improve the
quantum contribution inside VB-QER**, not whether VB-QER should be replaced.
Every arm below is a *VB-QER configuration*, not a competing algorithm.

    config A  classical members only        (greedy)
    config B  + exact selection              (ground truth where computable)
    config C  + classical QUBO               (same formulation, exact solve)
    config D  + QAOA at depth p              (p = 1..8)
    config E  + warm-start QAOA
    config F  + noise-model QAOA             (device-realistic simulation)

Shortest path is deliberately out of scope: Dijkstra/A* solve it exactly in
polynomial time, so there is no room for a quantum contribution, and those
members stay inside VB-QER unchanged. Return-load selection is a quadratic
knapsack -- NP-hard, with a measured 22.5% greedy suboptimality -- which is where
the room actually is.

    python -m routing.evaluation.circular_study --sizes 4,6,8,10,12 --depths 1,2,3,4,6,8
"""

from __future__ import annotations

import argparse
import json
import logging
import time
from dataclasses import asdict, dataclass, field

import numpy as np
import pandas as pd

from routing.hybrid.circular_builder import build_benchmark_set
from routing.hybrid.circular_qubo import (
    CircularProblem, build_circular_qubo, decode_circular, exhaustive_baseline,
    greedy_baseline,
)
from routing.hybrid.segment_qubo import coupling_density
from routing.quantum.decoder import bitstring_to_array
from routing.quantum.qaoa import run_qaoa
from routing.quantum.qubo import brute_force_qubo
from vb import config as C
from vb.io import git_commit

log = logging.getLogger("vb.circular_study")

EXPERIMENT_ID = "vbqer_circular_v1"

# Statevector budget. n_options + ~6 slack bits must stay under this.
MAX_QUBITS = 22
# Exhaustive selection is 2^n over options only (slack is not enumerated).
MAX_EXACT_OPTIONS = 20


@dataclass
class StudyRow:
    experiment: str
    problem_id: str
    family: str
    n_options: int
    config: str
    solver: str
    p_layers: int | None
    objective: float
    exact_objective: float | None
    optimality_gap: float | None
    is_optimal: bool
    feasible: bool
    n_selected: int
    capacity_utilization: float
    # Quantum-specific
    n_qubits: int | None = None
    circuit_depth: int | None = None
    shots: int | None = None
    feasible_sampling_rate: float | None = None
    solution_diversity: float | None = None
    noise_model: bool = False
    # Incumbent interaction
    incumbent_objective: float | None = None
    improvement_over_incumbent: float = 0.0
    degraded_before_guard: bool = False
    degraded_after_guard: bool = False
    guard_triggered: bool = False
    # Timing
    runtime_ms: float = 0.0
    seed: int = 0
    coupling_density: float | None = None


def classify_family(p: CircularProblem) -> str:
    """Assign a problem family, for the transfer hypothesis.

    The hypothesis under test is that quantum-derived information may transfer
    within *matched* optimization families even when a global prior does not.
    Families are defined on structural properties that plausibly change the
    optimization landscape, not on arbitrary bucketing.
    """
    demands = np.array([o.demand_kg for o in p.options])
    total = float(demands.sum())
    cap = p.remaining_capacity_kg
    tightness = total / cap if cap else np.inf

    off = p.synergy[np.triu_indices(p.n_options, k=1)]
    mean_syn = float(np.mean(off)) if off.size else 0.0
    syn_scale = float(np.mean(np.abs([o.solo_value for o in p.options]))) or 1.0
    rel_syn = mean_syn / syn_scale

    detours = np.array([o.detour_km for o in p.options])
    mean_detour = float(detours.mean())

    if rel_syn < -0.05:
        return "D_shared_corridor_synergy"
    if mean_detour > 25.0:
        return "C_high_detour"
    if tightness > 2.0:
        return "A_tight_capacity_dense"
    if tightness < 1.0:
        return "B_loose_capacity_sparse"
    return "E_balanced"


def _diversity(counts: dict[str, int], qubo, problem: CircularProblem,
               top_k: int = 20) -> float:
    """Fraction of distinct feasible selections among the most frequent samples.

    Solution diversity matters even when the objective does not improve: a
    quantum layer that surfaces several near-optimal alternatives is useful for
    a dispatcher choosing under constraints the model does not encode.
    """
    seen: set[tuple[int, ...]] = set()
    n_feasible = 0
    for bits, _ in sorted(counts.items(), key=lambda kv: -kv[1])[:top_k]:
        x = bitstring_to_array(bits, qubo.n_vars)
        dec = decode_circular(x, problem, qubo)
        if dec["feasible"]:
            n_feasible += 1
            seen.add(tuple(sorted(dec["selected_indices"])))
    return len(seen) / n_feasible if n_feasible else 0.0


def study_problem(
    p: CircularProblem, *, depths: list[int], shots: int = 1024,
    seed: int = 42, run_noise: bool = False,
) -> list[StudyRow]:
    fam = classify_family(p)
    rows: list[StudyRow] = []
    qubo = build_circular_qubo(p)
    cd = coupling_density(qubo)

    def row(**kw) -> StudyRow:
        base = dict(experiment=EXPERIMENT_ID, problem_id=p.instance_id, family=fam,
                    n_options=p.n_options, exact_objective=exact_obj,
                    incumbent_objective=greedy["objective"], seed=seed,
                    coupling_density=cd)
        base.update(kw)
        return StudyRow(**base)

    # --- config A: greedy incumbent
    t0 = time.perf_counter()
    greedy = greedy_baseline(p)
    greedy_ms = (time.perf_counter() - t0) * 1000

    # --- config B: exact ground truth
    exact_obj = None
    exact_ms = 0.0
    if p.n_options <= MAX_EXACT_OPTIONS:
        t0 = time.perf_counter()
        exact = exhaustive_baseline(p, max_options=MAX_EXACT_OPTIONS)
        exact_ms = (time.perf_counter() - t0) * 1000
        exact_obj = exact["objective"]

    def gap(obj: float | None) -> float | None:
        if obj is None or exact_obj is None:
            return None
        denom = abs(exact_obj) if abs(exact_obj) > 1e-9 else 1.0
        return (obj - exact_obj) / denom

    rows.append(row(config="A_greedy_only", solver="greedy", p_layers=None,
                    objective=greedy["objective"], optimality_gap=gap(greedy["objective"]),
                    is_optimal=bool(exact_obj is not None
                                    and abs(greedy["objective"] - exact_obj) < 1e-9),
                    feasible=True, n_selected=len(greedy["selected_indices"]),
                    capacity_utilization=greedy["total_demand_kg"] / p.remaining_capacity_kg
                    if p.remaining_capacity_kg else 0.0,
                    runtime_ms=greedy_ms))

    if exact_obj is not None:
        rows.append(row(config="B_exact", solver="exhaustive_exact", p_layers=None,
                        objective=exact_obj, optimality_gap=0.0, is_optimal=True,
                        feasible=True, n_selected=len(exact["selected_indices"]),
                        capacity_utilization=exact["total_demand_kg"] / p.remaining_capacity_kg
                        if p.remaining_capacity_kg else 0.0,
                        improvement_over_incumbent=greedy["objective"] - exact_obj,
                        runtime_ms=exact_ms))

    # --- config C: same QUBO, exact solve
    if qubo.n_vars <= MAX_QUBITS:
        t0 = time.perf_counter()
        x, _ = brute_force_qubo(qubo, max_vars=MAX_QUBITS)
        dec = decode_circular(x, p, qubo)
        ms = (time.perf_counter() - t0) * 1000
        accepted = dec["feasible"] and dec["objective"] < greedy["objective"] - 1e-9
        final = dec["objective"] if accepted else greedy["objective"]
        rows.append(row(config="C_classical_qubo", solver="qubo_exhaustive",
                        p_layers=None, objective=dec["objective"],
                        optimality_gap=gap(dec["objective"]),
                        is_optimal=bool(exact_obj is not None and dec["feasible"]
                                        and abs(dec["objective"] - exact_obj) < 1e-9),
                        feasible=dec["feasible"], n_selected=len(dec["selected_indices"]),
                        capacity_utilization=dec["capacity_utilization"],
                        n_qubits=qubo.n_vars,
                        improvement_over_incumbent=greedy["objective"] - final,
                        degraded_before_guard=bool(dec["feasible"] and
                                                   dec["objective"] > greedy["objective"] + 1e-9),
                        degraded_after_guard=bool(final > greedy["objective"] + 1e-9),
                        guard_triggered=not accepted, runtime_ms=ms))

    # --- config D/E/F: QAOA sweeps
    if qubo.n_vars <= MAX_QUBITS:
        variants = [("D_qaoa", False, False)]
        variants.append(("E_qaoa_warmstart", True, False))
        if run_noise:
            variants.append(("F_qaoa_noise", False, True))

        for config, warm, noisy in variants:
            for pl in depths:
                if config != "D_qaoa" and pl not in (2, 3):
                    continue  # warm-start / noise only at representative depths
                t0 = time.perf_counter()
                backend = None
                if noisy:
                    backend = _noisy_backend(qubo.n_vars, seed)
                    if backend is None:
                        continue
                init = ([0.15] * pl + [0.35] * pl) if warm else None
                try:
                    qa = run_qaoa(qubo, p=pl, shots=shots, seed=seed, maxiter=60,
                                  initial_params=init, backend=backend,
                                  decode_fn=lambda v: decode_circular(v, p, qubo))
                except Exception as e:
                    log.warning("QAOA p=%d failed on %s: %s", pl, p.instance_id, e)
                    continue
                ms = (time.perf_counter() - t0) * 1000

                obj = None
                feasible = False
                nsel = 0
                caputil = 0.0
                if qa.best_bitstring:
                    dec = decode_circular(
                        bitstring_to_array(qa.best_bitstring, qubo.n_vars), p, qubo)
                    feasible = dec["feasible"]
                    if feasible:
                        obj = dec["objective"]
                        nsel = len(dec["selected_indices"])
                        caputil = dec["capacity_utilization"]

                accepted = obj is not None and obj < greedy["objective"] - 1e-9
                final = obj if accepted else greedy["objective"]
                rows.append(row(
                    config=config, solver=f"qaoa_p{pl}", p_layers=pl,
                    objective=obj if obj is not None else float("nan"),
                    optimality_gap=gap(obj),
                    is_optimal=bool(exact_obj is not None and obj is not None
                                    and abs(obj - exact_obj) < 1e-9),
                    feasible=feasible, n_selected=nsel, capacity_utilization=caputil,
                    n_qubits=qa.n_qubits, circuit_depth=qa.circuit_depth,
                    shots=qa.shots, feasible_sampling_rate=qa.feasible_rate,
                    solution_diversity=_diversity(qa.counts, qubo, p),
                    noise_model=noisy,
                    improvement_over_incumbent=greedy["objective"] - final,
                    degraded_before_guard=bool(obj is not None
                                               and obj > greedy["objective"] + 1e-9),
                    degraded_after_guard=bool(final > greedy["objective"] + 1e-9),
                    guard_triggered=not accepted, runtime_ms=ms))
    return rows


def _noisy_backend(n_qubits: int, seed: int):
    """A device-realistic noisy simulator, if a noise model can be built.

    Uses a generic depolarising + readout model rather than a specific backend's
    calibration, so the result describes "QAOA under realistic noise" rather
    than "QAOA on ibm_fez on a particular day".
    """
    try:
        from qiskit_aer import AerSimulator
        from qiskit_aer.noise import (
            NoiseModel, depolarizing_error, ReadoutError,
        )
        nm = NoiseModel()
        nm.add_all_qubit_quantum_error(depolarizing_error(0.001, 1), ["rz", "rx", "h"])
        nm.add_all_qubit_quantum_error(depolarizing_error(0.01, 2), ["cx"])
        nm.add_all_qubit_readout_error(ReadoutError([[0.98, 0.02], [0.03, 0.97]]))
        return AerSimulator(noise_model=nm, seed_simulator=seed)
    except Exception as e:  # noise modelling unavailable
        log.warning("noise model unavailable: %s", e)
        return None


def run(sizes: list[int], depths: list[int], n_per_size: int = 6,
        shots: int = 1024, seed: int = 42, run_noise: bool = True) -> pd.DataFrame:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    all_rows: list[StudyRow] = []

    for size in sizes:
        log.info("=== option-set size %d ===", size)
        problems = build_benchmark_set(n_problems=n_per_size, seed=20260903 + size,
                                       max_options=size)
        problems = [p for p in problems if p.n_options >= min(size, 4)]
        log.info("  %d problems", len(problems))
        for k, p in enumerate(problems, 1):
            all_rows.extend(study_problem(p, depths=depths, shots=shots,
                                          seed=seed, run_noise=run_noise))
            log.info("  %d/%d done (%d rows)", k, len(problems), len(all_rows))

    df = pd.DataFrame([asdict(r) for r in all_rows])
    out = C.RES / "hybrid" / f"{EXPERIMENT_ID}_study.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    log.info("wrote %s (%d rows)", out, len(df))
    return df


def analyse(df: pd.DataFrame) -> dict:
    """Per-configuration and per-depth summaries, plus family breakdown."""
    out: dict[str, object] = {}

    feas = df[df["feasible"]]
    by_config = feas.groupby("config").agg(
        n=("problem_id", "count"),
        mean_gap=("optimality_gap", "mean"),
        optimal_rate=("is_optimal", "mean"),
        mean_runtime_ms=("runtime_ms", "mean"),
        mean_feasible_sampling=("feasible_sampling_rate", "mean"),
        mean_diversity=("solution_diversity", "mean"),
    ).round(5)
    out["by_config"] = by_config.reset_index().to_dict("records")

    # Guard behaviour must be reported for every arm, feasible or not.
    guard = df.groupby("config").agg(
        n=("problem_id", "count"),
        feasible_rate=("feasible", "mean"),
        degraded_before_guard=("degraded_before_guard", "mean"),
        degraded_after_guard=("degraded_after_guard", "mean"),
        guard_trigger_rate=("guard_triggered", "mean"),
        mean_improvement=("improvement_over_incumbent", "mean"),
    ).round(5)
    out["guard"] = guard.reset_index().to_dict("records")

    qa = feas[feas["config"] == "D_qaoa"]
    if not qa.empty:
        out["by_depth"] = qa.groupby("p_layers").agg(
            n=("problem_id", "count"),
            mean_gap=("optimality_gap", "mean"),
            optimal_rate=("is_optimal", "mean"),
            mean_feasible_sampling=("feasible_sampling_rate", "mean"),
            mean_circuit_depth=("circuit_depth", "mean"),
            mean_runtime_ms=("runtime_ms", "mean"),
            mean_diversity=("solution_diversity", "mean"),
        ).round(5).reset_index().to_dict("records")

        out["by_size"] = qa.groupby("n_options").agg(
            n=("problem_id", "count"),
            mean_gap=("optimality_gap", "mean"),
            optimal_rate=("is_optimal", "mean"),
            mean_qubits=("n_qubits", "mean"),
            mean_feasible_sampling=("feasible_sampling_rate", "mean"),
        ).round(5).reset_index().to_dict("records")

    # Where does greedy actually leave room? This bounds any possible gain.
    g = df[df["config"] == "A_greedy_only"]
    if not g.empty:
        out["greedy_headroom"] = {
            "n": int(len(g)),
            "optimal_rate": float(g["is_optimal"].mean()),
            "mean_gap": float(g["optimality_gap"].mean()),
            "by_size": g.groupby("n_options")["is_optimal"].mean().round(4).to_dict(),
            "by_family": g.groupby("family")["is_optimal"].mean().round(4).to_dict(),
        }

    out["family_counts"] = df.drop_duplicates("problem_id")["family"].value_counts().to_dict()
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sizes", default="4,6,8,10,12")
    ap.add_argument("--depths", default="1,2,3,4,6,8")
    ap.add_argument("--per-size", type=int, default=6)
    ap.add_argument("--shots", type=int, default=1024)
    ap.add_argument("--no-noise", action="store_true")
    a = ap.parse_args()

    sizes = [int(x) for x in a.sizes.split(",")]
    depths = [int(x) for x in a.depths.split(",")]
    df = run(sizes, depths, n_per_size=a.per_size, shots=a.shots,
             run_noise=not a.no_noise)
    analysis = analyse(df)

    manifest = {
        "experiment_id": EXPERIMENT_ID,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "git_commit": git_commit(),
        "sizes": sizes, "depths": depths, "shots": a.shots,
        "n_rows": int(len(df)), "n_problems": int(df.problem_id.nunique()),
        "analysis": analysis,
    }
    (C.RES / "manifests" / f"{EXPERIMENT_ID}.json").write_text(
        json.dumps(manifest, indent=2, default=str), encoding="utf-8")
    print(json.dumps(analysis, indent=2, default=str)[:4000])


if __name__ == "__main__":
    main()
