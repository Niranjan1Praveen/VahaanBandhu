"""Distil quantum artifacts, calibrate the ensemble, and run the ablation.

Strict split discipline (Step 9 of the follow-up brief):

* **train**   -- QAOA is run here; measurement distributions are distilled into
                 priors.
* **validation** -- priors are validated here and weights are calibrated here.
                 A prior that does not help on validation is not deployed.
* **test**    -- touched exactly once, for the final ablation. Never used to
                 choose weights or to decide deployability.

Splits are keyed on the instance's structural hash (via the dataset's own
``split`` column where available), so two near-identical problems cannot land on
opposite sides.

Ablation arms (Step 17):

    A. Best classical only
    B. Classical ensemble, no quantum features
    C. Classical + simulator-derived quantum features
    D. Classical + hardware-derived quantum features
    E. Full quantum-enhanced ensemble

Without this, an ensemble improvement could not be attributed to quantum.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import asdict

import numpy as np
import pandas as pd

from routing.ensemble.inference import VBQEROptimizer
from routing.ensemble.members import compute_diversity, generate_candidates
from routing.ensemble.quantum_priors import (
    QuantumPrior, distil_marginals, save_prior, validate_prior,
)
from routing.evaluation.metrics import evaluate, tour_to_routes
from routing.hybrid.corridor import build_corridor
from routing.hybrid.objective_costs import objective_cost_matrix
from routing.hybrid.optimizer import solve_classical
from routing.hybrid.segment_qubo import build_segment_qubo, decode_segments
from routing.instances import list_instances, load_instance
from routing.quantum.decoder import bitstring_to_array
from routing.quantum.qaoa import run_qaoa
from vb import config as C
from vb.io import git_commit

log = logging.getLogger("vb.calibrate")

EXPERIMENT_ID = "vbqer_v1"


def make_splits(n_instances: int = 60, seed: int = 20260903,
                size_range: tuple[int, int] = (8, 18)) -> dict[str, list[str]]:
    """Train/validation/test instance ids, using the dataset's own split column.

    Reusing the dataset split rather than re-drawing one keeps this experiment
    consistent with the the routing research leakage guarantees (district, temporal,
    template-family and structural-hash holdouts already applied there).
    """
    df = list_instances()
    df = df[(df["n_customers"] + 1).between(*size_range)]
    rng = np.random.default_rng(seed)
    out: dict[str, list[str]] = {}
    per = {"train": int(n_instances * 0.5),
           "validation": int(n_instances * 0.25),
           "test": n_instances - int(n_instances * 0.5) - int(n_instances * 0.25)}
    for split, k in per.items():
        g = df[df["split"] == split]
        if g.empty:
            out[split] = []
            continue
        take = min(k, len(g))
        idx = rng.choice(len(g), take, replace=False)
        out[split] = g.iloc[idx]["instance_id"].tolist()
    return out


def _edge_labels(tour: list[int]) -> list[str]:
    return [f"{tour[i]}->{tour[(i + 1) % len(tour)]}" for i in range(len(tour))]


def distil_from_instances(
    instance_ids: list[str], *, qaoa_layers: int = 2, qaoa_shots: int = 1024,
    seed: int = 42, max_variables: int = 16,
) -> tuple[dict[str, float], dict]:
    """Run QAOA on training instances and distil edge marginals.

    Each feasible decoded sample contributes the edges of the tour it implies,
    weighted by how good that sample was. The result is a map from directed edge
    to a normalised preference, which is exactly what the ensemble scorer
    consumes.
    """
    samples: list[tuple[dict[str, int], dict[str, float]]] = []
    stats = {"n_instances": 0, "n_with_feasible_samples": 0,
             "feasible_rates": [], "params": []}

    for iid in instance_ids:
        try:
            inst = load_instance(iid)
        except Exception:
            continue
        Cm = objective_cost_matrix(inst)
        tour, _, _ = solve_classical(inst, seed=seed)
        corridor = build_corridor(inst, tour, max_variables=max_variables,
                                  cost_matrix=Cm, seed=seed)
        qubo = build_segment_qubo(corridor)
        if qubo.n_vars > 20:
            continue
        stats["n_instances"] += 1

        qa = run_qaoa(qubo, p=qaoa_layers, shots=qaoa_shots, seed=seed,
                      maxiter=50,
                      decode_fn=lambda v: decode_segments(v, corridor, qubo))
        stats["feasible_rates"].append(qa.feasible_rate)
        stats["params"].append(qa.optimal_params)

        counts: dict[str, int] = {}
        energies: dict[str, list[float]] = {}
        for bits, shots in qa.counts.items():
            x = bitstring_to_array(bits, qubo.n_vars)
            dec = decode_segments(x, corridor, qubo)
            if not dec["feasible"] or not dec["tour"]:
                continue
            e = qubo.energy(x)
            for lab in _edge_labels(dec["tour"]):
                counts[lab] = counts.get(lab, 0) + shots
                energies.setdefault(lab, []).append(e)
        if counts:
            stats["n_with_feasible_samples"] += 1
            samples.append((counts, {k: float(np.mean(v)) for k, v in energies.items()}))

    marginals = distil_marginals(samples, energy_weighting=True)
    stats["mean_feasible_rate"] = (float(np.mean(stats["feasible_rates"]))
                                   if stats["feasible_rates"] else None)
    stats["mean_params"] = (np.mean(stats["params"], axis=0).tolist()
                            if stats["params"] else None)
    stats.pop("params")
    stats.pop("feasible_rates")
    return marginals, stats


def evaluate_arm(
    instance_ids: list[str], *, use_quantum: bool, priors: list[QuantumPrior] | None,
    artifact_source: str | None = None, seed: int = 42,
    classical_only: bool = False,
) -> pd.DataFrame:
    """Evaluate one ablation arm on a set of instances."""
    rows = []
    for iid in instance_ids:
        try:
            inst = load_instance(iid)
        except Exception:
            continue

        if classical_only:
            # Arm A: the single best classical solver, no ensemble.
            t0 = time.perf_counter()
            tour, _, _ = solve_classical(inst, seed=seed)
            ev = evaluate(inst, tour_to_routes(tour, inst.depot_index))
            rows.append({
                "instance_id": iid, "objective": ev.objective,
                "feasible": ev.feasible, "distance_km": ev.distance_km,
                "empty_km": ev.empty_km,
                "total_ms": (time.perf_counter() - t0) * 1000,
                "final_route_source": "classical_only",
                "quantum_contribution_used": False, "n_candidates": 1,
                "cost_snapshot_id": inst.cost_snapshot_id,
            })
            continue

        opt = VBQEROptimizer(priors=priors, use_quantum_artifacts=use_quantum,
                             artifact_source=artifact_source, seed=seed)
        s = opt.solve(inst)
        rows.append({
            "instance_id": iid, "objective": s.objective, "feasible": s.feasible,
            "distance_km": s.distance_km, "empty_km": s.empty_km,
            "total_ms": s.total_ms, "final_route_source": s.final_route_source,
            "quantum_contribution_used": s.quantum_contribution_used,
            "n_candidates": s.n_candidates,
            "cost_snapshot_id": s.cost_snapshot_id,
        })
    return pd.DataFrame(rows)


def run(n_instances: int = 60, *, qaoa_layers: int = 2, qaoa_shots: int = 1024,
        seed: int = 42) -> dict:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    splits = make_splits(n_instances=n_instances, seed=seed)
    log.info("splits: train=%d validation=%d test=%d",
             len(splits["train"]), len(splits["validation"]), len(splits["test"]))

    # --- distil on TRAIN only
    log.info("distilling quantum priors from %d training instances", len(splits["train"]))
    marginals, stats = distil_from_instances(
        splits["train"], qaoa_layers=qaoa_layers, qaoa_shots=qaoa_shots, seed=seed)
    log.info("distilled %d edge marginals from %d instances (%d yielded feasible samples)",
             len(marginals), stats["n_instances"], stats["n_with_feasible_samples"])

    snapshots = []
    if splits["train"]:
        try:
            snapshots = [load_instance(splits["train"][0]).cost_snapshot_id]
        except Exception:
            snapshots = []

    prior = QuantumPrior(
        artifact_id=f"qaoa_segment_prior_{EXPERIMENT_ID}",
        artifact_version="v1",
        source="quantum_simulator",
        problem_family="segment_set_partition",
        variable_marginals=marginals,
        qaoa_params=stats.get("mean_params"),
        n_layers=qaoa_layers,
        dataset_version="v0.1",
        graph_version="g1",
        training_split="train",
        cost_snapshot_ids=snapshots,
        quantum_backend="aer_simulator",
        n_problems_distilled=stats["n_instances"],
        mean_feasible_rate=stats.get("mean_feasible_rate"),
        notes=("Edge marginals distilled from QAOA measurement distributions over "
               "segment set-partition QUBOs, energy-weighted."),
    )

    # --- validate on VALIDATION only
    log.info("validating the prior on %d held-out validation instances",
             len(splits["validation"]))
    base = evaluate_arm(splits["validation"], use_quantum=False, priors=None, seed=seed)
    prior.deployable = True  # provisional, so the arm can actually apply it
    withp = evaluate_arm(splits["validation"], use_quantum=True, priors=[prior],
                         artifact_source="quantum_simulator", seed=seed)
    pairs = []
    if not base.empty and not withp.empty:
        m = base.merge(withp, on="instance_id", suffixes=("_base", "_prior"))
        pairs = list(zip(m["objective_base"], m["objective_prior"]))
    prior.deployable = False
    prior = validate_prior(prior, pairs)
    log.info("prior deployable=%s validation=%s", prior.deployable, prior.validation)
    save_prior(prior)

    # --- ABLATION on TEST, touched once
    log.info("running ablation on %d test instances", len(splits["test"]))
    arms = {
        "A_best_classical_only": evaluate_arm(
            splits["test"], use_quantum=False, priors=None, seed=seed,
            classical_only=True),
        "B_classical_ensemble": evaluate_arm(
            splits["test"], use_quantum=False, priors=None, seed=seed),
        "C_simulator_quantum": evaluate_arm(
            splits["test"], use_quantum=True, priors=[prior],
            artifact_source="quantum_simulator", seed=seed),
        "D_hardware_quantum": evaluate_arm(
            splits["test"], use_quantum=True,
            priors=[p for p in [prior] if p.source == "quantum_hardware"],
            artifact_source="quantum_hardware", seed=seed),
        "E_full_ensemble": evaluate_arm(
            splits["test"], use_quantum=True, priors=[prior], seed=seed),
    }

    summary = {}
    for name, df in arms.items():
        if df.empty:
            summary[name] = {"n": 0}
            continue
        summary[name] = {
            "n": int(len(df)),
            "mean_objective": float(df["objective"].mean()),
            "median_objective": float(df["objective"].median()),
            "feasible_rate": float(df["feasible"].mean()),
            "mean_ms": float(df["total_ms"].mean()),
            "quantum_used_rate": float(df["quantum_contribution_used"].mean()),
            "mean_empty_km": float(df["empty_km"].mean()),
        }

    # Paired comparison against arm B isolates the quantum contribution.
    if not arms["B_classical_ensemble"].empty:
        b = arms["B_classical_ensemble"].set_index("instance_id")["objective"]
        for name in ("C_simulator_quantum", "D_hardware_quantum", "E_full_ensemble"):
            df = arms[name]
            if df.empty:
                continue
            a = df.set_index("instance_id")["objective"]
            common = b.index.intersection(a.index)
            if len(common) == 0:
                continue
            delta = b.loc[common] - a.loc[common]
            summary[name]["vs_B_n_improved"] = int((delta > 1e-9).sum())
            summary[name]["vs_B_n_degraded"] = int((delta < -1e-9).sum())
            summary[name]["vs_B_n_identical"] = int(np.isclose(delta, 0, atol=1e-9).sum())
            summary[name]["vs_B_mean_delta"] = float(delta.mean())

    out_dir = C.RES / "ensemble"
    for sub in ("models", "weights", "quantum_priors", "calibration",
                "ablations", "evaluations", "manifests"):
        (out_dir / sub).mkdir(parents=True, exist_ok=True)
    for name, df in arms.items():
        if not df.empty:
            df.to_csv(out_dir / "ablations" / f"{EXPERIMENT_ID}_{name}.csv", index=False)

    manifest = {
        "experiment_id": EXPERIMENT_ID,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "git_commit": git_commit(),
        "splits": {k: len(v) for k, v in splits.items()},
        "distillation": stats,
        "prior": {k: v for k, v in asdict(prior).items() if k != "variable_marginals"},
        "n_marginals": len(marginals),
        "ablation": summary,
    }
    (out_dir / "manifests" / f"{EXPERIMENT_ID}.json").write_text(
        json.dumps(manifest, indent=2, default=str), encoding="utf-8")
    (out_dir / "calibration" / f"{EXPERIMENT_ID}_splits.json").write_text(
        json.dumps(splits, indent=2), encoding="utf-8")
    return manifest


if __name__ == "__main__":
    m = run()
    print(json.dumps(m["ablation"], indent=2, default=str))
    print("\nprior deployable:", m["prior"]["deployable"])
    print("validation:", json.dumps(m["prior"]["validation"], indent=2))
