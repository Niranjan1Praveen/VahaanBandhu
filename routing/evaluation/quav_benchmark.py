"""Benchmark set and runner for the QUAV-inspired hybrid experiments.

Experiment identifier: ``quav_hybrid_v1``. Results are versioned separately from
the Phase-A benchmark and never overwrite it.

Benchmark design (Step 18): problems are stratified into categories that stress
different parts of the objective, rather than inflating the count by duplicating
one scenario. Each category is drawn with a fixed seed and the manifest records
exactly how it was built, so the set is reproducible.

    python -m routing.evaluation.quav_benchmark --n 40
"""

from __future__ import annotations

import argparse
import json
import logging
import time
from dataclasses import asdict

import numpy as np
import pandas as pd

from routing.hybrid.circular_builder import build_benchmark_set
from routing.hybrid.optimizer import (
    HYBRID_VERSION, hybrid_circular_selection, hybrid_route_refinement,
    solve_classical,
)
from routing.instances import list_instances, load_instance
from vb import config as C
from vb.io import git_commit

log = logging.getLogger("vb.quav")

EXPERIMENT_ID = "quav_hybrid_v1"

# Categories for the routing-refinement track. Each stresses a different part of
# the multi-objective, so a finding can be attributed rather than averaged away.
ROUTE_CATEGORIES = {
    "simple_alternatives": dict(size=(6, 12), problem_type=None),
    "multi_stop": dict(size=(13, 22), problem_type=None),
    "circular_vrp": dict(size=(6, 20), problem_type="CIRCULAR_VRP"),
    "time_windowed": dict(size=(6, 20), problem_type="VRPTW"),
}


def build_route_benchmark(n_per_category: int = 8, seed: int = 20260903) -> pd.DataFrame:
    """Stratified sample of routing instances, with a reproducible manifest."""
    rng = np.random.default_rng(seed)
    allinst = list_instances()
    rows = []
    for cat, spec in ROUTE_CATEGORIES.items():
        g = allinst
        if spec["problem_type"]:
            g = g[g["problem_type"] == spec["problem_type"]]
        lo, hi = spec["size"]
        g = g[(g["n_customers"] + 1).between(lo, hi)]
        if g.empty:
            log.warning("category %s has no matching instances", cat)
            continue
        take = min(n_per_category, len(g))
        idx = rng.choice(len(g), take, replace=False)
        for iid in g.iloc[idx]["instance_id"]:
            rows.append({"category": cat, "instance_id": iid})
    return pd.DataFrame(rows)


def run_route_track(bench: pd.DataFrame, *, seed: int = 42,
                    qaoa_layers: int = 2, qaoa_shots: int = 1024) -> pd.DataFrame:
    """Run BEST-CLASSICAL, HYBRID-1 and HYBRID-2 on identical instances."""
    rows = []
    for k, r in enumerate(bench.itertuples(), 1):
        inst = load_instance(r.instance_id)

        # Classical-only reference. Recorded as its own row so the comparison is
        # explicit rather than implied by the hybrid's own bookkeeping.
        t0 = time.perf_counter()
        tour, _, cls_ms = solve_classical(inst, seed=seed)
        from routing.evaluation.metrics import evaluate, tour_to_routes
        ev = evaluate(inst, tour_to_routes(tour, inst.depot_index))
        rows.append({
            "experiment": EXPERIMENT_ID, "category": r.category,
            "instance_id": r.instance_id, "algorithm": "BEST_CLASSICAL",
            "objective": ev.objective, "feasible": ev.feasible,
            "distance_km": ev.distance_km, "time_min": ev.time_min,
            "toll_inr": ev.toll_inr, "fuel_inr": ev.fuel_inr,
            "empty_km": ev.empty_km, "circular_score": ev.circular_score,
            "classical_objective": ev.objective, "improvement": 0.0,
            "total_ms": (time.perf_counter() - t0) * 1000,
            "classical_ms": cls_ms,
            "cost_snapshot_id": inst.cost_snapshot_id, "seed": seed,
            "q_quantum_invoked": False, "q_quantum_contribution_used": False,
            "q_final_route_source": "classical_incumbent",
        })

        for variant, warm in (("HYBRID-1", False), ("HYBRID-2", True)):
            res = hybrid_route_refinement(
                inst, variant=variant, warm_start=warm, use_qaoa=True,
                qaoa_layers=qaoa_layers, qaoa_shots=qaoa_shots, seed=seed)
            row = res.to_row()
            row.update({"experiment": EXPERIMENT_ID, "category": r.category,
                        "algorithm": variant})
            rows.append(row)

        if k % 5 == 0:
            log.info("  route track %d/%d", k, len(bench))
    return pd.DataFrame(rows)


def run_circular_track(n_problems: int = 40, *, seed: int = 42,
                       qaoa_layers: int = 2, qaoa_shots: int = 1024,
                       max_options: int = 6) -> tuple[pd.DataFrame, list]:
    """Run the HYBRID-3 circular return-load track.

    Also runs a classical-QUBO arm (same formulation, exhaustive solve) so the
    ablation can separate "the formulation helps" from "QAOA helps".
    """
    problems = build_benchmark_set(n_problems=n_problems, seed=20260903,
                                   max_options=max_options)
    log.info("built %d circular problems", len(problems))
    rows = []
    for k, p in enumerate(problems, 1):
        for variant, use_qaoa, warm in (
            ("HYBRID-3", True, False),
            ("HYBRID-3-WARM", True, True),
            ("QUBO_CLASSICAL", False, False),
        ):
            res = hybrid_circular_selection(
                p, variant=variant, use_qaoa=use_qaoa, warm_start=warm,
                qaoa_layers=qaoa_layers, qaoa_shots=qaoa_shots, seed=seed)
            row = res.to_row()
            row.update({"experiment": EXPERIMENT_ID, "category": "circular_return",
                        "algorithm": variant, "n_options": p.n_options})
            rows.append(row)
        if k % 10 == 0:
            log.info("  circular track %d/%d", k, len(problems))
    return pd.DataFrame(rows), problems


def analyse_circular(df: pd.DataFrame) -> dict:
    """Improvement / match / degradation analysis (Step 19)."""
    out: dict[str, object] = {}
    for alg, g in df.groupby("algorithm"):
        comparable = g[g["quantum_objective"].notna()]
        improved = (comparable["quantum_objective"]
                    < comparable["classical_objective"] - 1e-9)
        matched = np.isclose(comparable["quantum_objective"],
                             comparable["classical_objective"], atol=1e-9)
        degraded = (comparable["quantum_objective"]
                    > comparable["classical_objective"] + 1e-9)

        # Raw quantum degradation vs what was actually deployed after the guard.
        deployed_worse = (g["final_objective"] > g["classical_objective"] + 1e-9)

        gaps = None
        if "exact_objective" in g and g["exact_objective"].notna().any():
            h = g[g["exact_objective"].notna()]
            gaps = {
                "classical_mean_gap_vs_exact": float(
                    (h["classical_objective"] - h["exact_objective"]).mean()),
                "final_mean_gap_vs_exact": float(
                    (h["final_objective"] - h["exact_objective"]).mean()),
                "classical_optimal_rate": float(
                    np.isclose(h["classical_objective"], h["exact_objective"],
                               atol=1e-9).mean()),
                "final_optimal_rate": float(
                    np.isclose(h["final_objective"], h["exact_objective"],
                               atol=1e-9).mean()),
            }

        wins = comparable[improved]
        out[alg] = {
            "n_problems": int(len(g)),
            "n_comparable": int(len(comparable)),
            "quantum_invocation_rate": float(g["q_quantum_invoked"].mean()),
            "improvement_rate": float(improved.mean()) if len(comparable) else 0.0,
            "match_rate": float(matched.mean()) if len(comparable) else 0.0,
            "raw_degradation_rate": float(degraded.mean()) if len(comparable) else 0.0,
            "final_deployed_degradation_rate": float(deployed_worse.mean()),
            "n_quantum_accepted": int(g["q_quantum_contribution_used"].sum()),
            "n_quantum_rejected": int((~g["q_quantum_contribution_used"].astype(bool)).sum()),
            "mean_improvement_when_wins": float(
                (wins["classical_objective"] - wins["quantum_objective"]).mean())
            if len(wins) else 0.0,
            "median_improvement_when_wins": float(
                (wins["classical_objective"] - wins["quantum_objective"]).median())
            if len(wins) else 0.0,
            "mean_raw_degradation": float(
                (comparable[degraded]["quantum_objective"]
                 - comparable[degraded]["classical_objective"]).mean())
            if degraded.any() else 0.0,
            "mean_feasible_sampling_rate": float(
                g["q_feasible_sampling_rate"].dropna().mean())
            if g["q_feasible_sampling_rate"].notna().any() else None,
            "mean_quantum_ms": float(g["quantum_ms"].mean()),
            "mean_classical_ms": float(g["classical_ms"].mean()),
            "exactness": gaps,
        }
    return out


def save(route_df: pd.DataFrame, circ_df: pd.DataFrame, analysis: dict,
         bench: pd.DataFrame) -> dict:
    d = C.RES / "hybrid"
    d.mkdir(parents=True, exist_ok=True)
    route_df.to_csv(d / f"{EXPERIMENT_ID}_route_track.csv", index=False)
    circ_df.to_csv(d / f"{EXPERIMENT_ID}_circular_track.csv", index=False)
    bench.to_csv(d / f"{EXPERIMENT_ID}_benchmark_manifest.csv", index=False)

    manifest = {
        "experiment_id": EXPERIMENT_ID,
        "hybrid_version": HYBRID_VERSION,
        "git_commit": git_commit(),
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "n_route_instances": int(route_df["instance_id"].nunique()),
        "n_circular_problems": int(circ_df["problem_id"].nunique()),
        "cost_snapshots": sorted(route_df["cost_snapshot_id"].dropna().unique().tolist()),
        "analysis": analysis,
    }
    (C.RES / "manifests" / f"{EXPERIMENT_ID}.json").write_text(
        json.dumps(manifest, indent=2, default=str), encoding="utf-8")
    return manifest


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=40, help="circular problems")
    ap.add_argument("--per-category", type=int, default=6)
    ap.add_argument("--layers", type=int, default=2)
    ap.add_argument("--shots", type=int, default=1024)
    a = ap.parse_args()

    bench = build_route_benchmark(n_per_category=a.per_category)
    log.info("route benchmark: %d instances across %d categories",
             len(bench), bench["category"].nunique())
    route_df = run_route_track(bench, qaoa_layers=a.layers, qaoa_shots=a.shots)

    circ_df, _ = run_circular_track(n_problems=a.n, qaoa_layers=a.layers,
                                    qaoa_shots=a.shots)
    analysis = analyse_circular(circ_df)
    manifest = save(route_df, circ_df, analysis, bench)

    print(json.dumps(analysis, indent=2, default=str))
    print(f"\nsaved -> Res/hybrid/{EXPERIMENT_ID}_*.csv")
    print(f"manifest -> Res/manifests/{EXPERIMENT_ID}.json")


if __name__ == "__main__":
    main()
