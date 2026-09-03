"""Distil quantum artifacts from the circular track, with family-matched transfer.

The route-track prior failed held-out validation (0/15 improved, mean delta 0.0)
and is REJECTED. Two plausible reasons, and they call for different fixes:

1. **Thin yield.** Only 12 of 30 route-track instances produced any feasible QAOA
   sample, so the marginals were estimated from very little signal. The circular
   track has a 16.4% feasible sampling rate and a demonstrated 85% optimal rate --
   a much better source.

2. **A single global prior may be the wrong object.** Return-load problems differ
   structurally: tight vs loose capacity, high-detour, shared-corridor synergy.
   A marginal averaged across all of them describes none of them.

This module tests the second point directly, as a hypothesis rather than an
assumption:

> Quantum-derived information may transfer within *matched* optimization families
> even when a global prior does not generalise.

Both a global prior and per-family priors are distilled, and both are validated
on held-out problems. Whichever passes is deployed; if neither does, neither is,
and that is reported.

Artifacts produced
------------------
* **selection marginals** -- per-option probability of being chosen in good samples
* **synergy priors** -- pairwise co-selection statistics
* **QAOA parameter priors** -- (gamma, beta) per family, for warm-starting
"""

from __future__ import annotations

import json
import logging
import time
from collections import defaultdict
from dataclasses import asdict, dataclass, field

import numpy as np

from routing.ensemble.problem_family import classify_circular
from routing.ensemble.quantum_priors import QuantumPrior, save_prior, validate_prior
from routing.hybrid.circular_builder import build_benchmark_set
from routing.hybrid.circular_qubo import (
    CircularProblem, build_circular_qubo, decode_circular, exhaustive_baseline,
    greedy_baseline,
)
from routing.quantum.decoder import bitstring_to_array
from routing.quantum.qaoa import run_qaoa
from vb import config as C
from vb.io import git_commit

log = logging.getLogger("vb.circular_distill")

ARTIFACT_FAMILY = "return_load_quadratic_knapsack"
EXPERIMENT_ID = "vbqer_circular_artifacts_v1"


@dataclass
class CircularArtifact:
    """A family-scoped quantum artifact for return-load selection."""

    artifact_id: str
    artifact_version: str
    source: str
    problem_family: str
    # Rank-normalised propensity to select an option, keyed by its rank in the
    # problem's value ordering. Keying on *rank* rather than option id is what
    # lets the artifact transfer to unseen problems at all -- option ids are
    # instance-specific, ranks are not.
    rank_marginals: dict[str, float]
    # Mean pairwise co-selection rate by rank pair, capturing learned synergy.
    pair_marginals: dict[str, float]
    qaoa_params: list[float] | None
    n_layers: int
    n_problems_distilled: int
    mean_feasible_rate: float | None
    deployable: bool = False
    validation: dict = field(default_factory=dict)
    dataset_version: str = "v0.1"
    created_at: str = field(
        default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    git_commit: str = field(default_factory=git_commit)

    def to_dict(self) -> dict:
        return asdict(self)


def _rank_key(problem: CircularProblem, idx: int) -> str:
    """Rank of an option by value density, as a transferable key."""
    order = sorted(range(problem.n_options),
                   key=lambda i: problem.options[i].solo_value
                   / max(problem.options[i].demand_kg, 1.0))
    return f"r{order.index(idx)}"


def distil_from_problems(
    problems: list[CircularProblem], *, p_layers: int = 3, shots: int = 1024,
    seed: int = 42,
) -> tuple[dict[str, float], dict[str, float], list[float] | None, dict]:
    """Run QAOA on training problems and distil rank-keyed marginals."""
    rank_hits: dict[str, list[float]] = defaultdict(list)
    pair_hits: dict[str, list[float]] = defaultdict(list)
    params: list[list[float]] = []
    rates: list[float] = []
    n_used = 0

    for p in problems:
        qubo = build_circular_qubo(p)
        if qubo.n_vars > 22:
            continue
        try:
            qa = run_qaoa(qubo, p=p_layers, shots=shots, seed=seed, maxiter=50,
                          decode_fn=lambda v: decode_circular(v, p, qubo))
        except Exception as e:
            log.warning("QAOA failed on %s: %s", p.instance_id, e)
            continue
        rates.append(qa.feasible_rate)
        params.append(qa.optimal_params)

        # Energy-weight the samples: an unweighted marginal would mostly encode
        # the mixer's uniform prior rather than anything the cost layer learned.
        counts_by_rank: dict[str, float] = defaultdict(float)
        pair_by_rank: dict[str, float] = defaultdict(float)
        total_w = 0.0
        for bits, shots_n in qa.counts.items():
            x = bitstring_to_array(bits, qubo.n_vars)
            dec = decode_circular(x, p, qubo)
            if not dec["feasible"] or not dec["selected_indices"]:
                continue
            w = shots_n / (1.0 + max(dec["objective"] - min(
                o.solo_value for o in p.options), 0.0))
            total_w += w
            sel = dec["selected_indices"]
            for i in sel:
                counts_by_rank[_rank_key(p, i)] += w
            for a in range(len(sel)):
                for b in range(a + 1, len(sel)):
                    ka, kb = sorted((_rank_key(p, sel[a]), _rank_key(p, sel[b])))
                    pair_by_rank[f"{ka}|{kb}"] += w
        if total_w <= 0:
            continue
        n_used += 1
        for k, v in counts_by_rank.items():
            rank_hits[k].append(v / total_w)
        for k, v in pair_by_rank.items():
            pair_hits[k].append(v / total_w)

    def norm(d: dict[str, list[float]]) -> dict[str, float]:
        if not d:
            return {}
        raw = {k: float(np.mean(v)) for k, v in d.items()}
        hi = max(raw.values()) or 1.0
        return {k: round(v / hi, 6) for k, v in raw.items()}

    stats = {
        "n_problems": len(problems),
        "n_with_feasible_samples": n_used,
        "mean_feasible_rate": float(np.mean(rates)) if rates else None,
    }
    mean_params = np.mean(params, axis=0).tolist() if params else None
    return norm(rank_hits), norm(pair_hits), mean_params, stats


def _objective(problem: CircularProblem, chosen: list[int]) -> float:
    obj = float(sum(problem.options[i].solo_value for i in chosen))
    for a in range(len(chosen)):
        for b in range(a + 1, len(chosen)):
            obj += float(problem.synergy[chosen[a], chosen[b]])
    return obj


def _demand(problem: CircularProblem, chosen: list[int]) -> float:
    return float(sum(problem.options[i].demand_kg for i in chosen))


def _moves(problem: CircularProblem, chosen: list[int]) -> list[tuple[str, tuple]]:
    """Add / drop / swap moves from a selection."""
    n = problem.n_options
    inside = set(chosen)
    outside = [i for i in range(n) if i not in inside]
    moves: list[tuple[str, tuple]] = []
    moves += [("add", (i,)) for i in outside]
    moves += [("drop", (i,)) for i in chosen]
    moves += [("swap", (i, j)) for i in chosen for j in outside]
    return moves


def _apply_move(chosen: list[int], kind: str, args: tuple) -> list[int]:
    s = list(chosen)
    if kind == "add":
        s.append(args[0])
    elif kind == "drop":
        s.remove(args[0])
    else:
        s.remove(args[0])
        s.append(args[1])
    return s


def local_search(
    problem: CircularProblem, start: list[int], *,
    artifact: CircularArtifact | None = None, influence: float = 1.0,
    max_iter: int = 50,
) -> dict:
    """Local search over selections, optionally guided by quantum pair priors.

    Greedy's weakness is *combinations*: its per-item marginal rule cannot see
    that two loads are worth taking together because they share a corridor. Pair
    marginals from the QAOA distribution encode exactly that, so they are used to
    order which moves get examined first.

    Crucially the prior only ever changes the *order in which moves are tried*,
    never whether a move is accepted -- acceptance is always the true objective
    under the true capacity constraint. A bad artifact can therefore waste
    effort, but cannot produce a worse or infeasible answer.

    Passing ``artifact=None`` gives the unguided control. Comparing the two is
    the only way to tell whether quantum information contributed anything beyond
    what plain local search already finds.
    """
    chosen = list(start)
    best_obj = _objective(problem, chosen)
    cap = problem.remaining_capacity_kg

    def move_priority(kind: str, args: tuple) -> float:
        """Higher is examined first. Zero for the unguided control."""
        if artifact is None:
            return 0.0
        score = 0.0
        touched = [a for a in args]
        for i in touched:
            score += artifact.rank_marginals.get(_rank_key(problem, i), 0.0)
        # Pair prior: does the quantum distribution like this option alongside
        # what is already selected?
        for i in touched:
            for j in chosen:
                if i == j:
                    continue
                ka, kb = sorted((_rank_key(problem, i), _rank_key(problem, j)))
                score += artifact.pair_marginals.get(f"{ka}|{kb}", 0.0)
        return influence * score

    for _ in range(max_iter):
        candidates = _moves(problem, chosen)
        candidates.sort(key=lambda m: -move_priority(*m))
        improved = False
        for kind, args in candidates:
            cand = _apply_move(chosen, kind, args)
            if _demand(problem, cand) > cap + 1e-9:
                continue
            obj = _objective(problem, cand)
            if obj < best_obj - 1e-9:
                chosen, best_obj, improved = cand, obj, True
                break
        if not improved:
            break

    return {"objective": best_obj, "selected": sorted(chosen),
            "total_demand_kg": _demand(problem, chosen)}


def apply_artifact_to_problem(
    problem: CircularProblem, artifact: CircularArtifact | None = None,
) -> dict:
    """Greedy incumbent, then artifact-guided local search."""
    start = greedy_baseline(problem)["selected_indices"]
    return local_search(problem, start, artifact=artifact)


def run(n_train: int = 30, n_val: int = 20, max_options: int = 6,
        p_layers: int = 3, shots: int = 1024, seed: int = 42) -> dict:
    """Distil global and per-family artifacts, validate both on held-out problems."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    # Disjoint seeds keep train and validation problems genuinely separate.
    train = build_benchmark_set(n_problems=n_train, seed=20260903, max_options=max_options)
    val = build_benchmark_set(n_problems=n_val, seed=77777, max_options=max_options)
    train_ids = {p.instance_id for p in train}
    val = [p for p in val if p.instance_id not in train_ids]
    log.info("train=%d  validation=%d (disjoint)", len(train), len(val))

    by_family_train: dict[str, list[CircularProblem]] = defaultdict(list)
    for p in train:
        by_family_train[classify_circular(p).value].append(p)
    log.info("train families: %s",
             {k: len(v) for k, v in by_family_train.items()})

    results: dict[str, object] = {"families": {}}
    artifacts: list[CircularArtifact] = []

    # --- global artifact
    log.info("distilling GLOBAL artifact from %d problems", len(train))
    rm, pm, params, stats = distil_from_problems(
        train, p_layers=p_layers, shots=shots, seed=seed)
    global_art = CircularArtifact(
        artifact_id=f"circular_global_{EXPERIMENT_ID}", artifact_version="v1",
        source="quantum_simulator", problem_family="ALL",
        rank_marginals=rm, pair_marginals=pm, qaoa_params=params,
        n_layers=p_layers, n_problems_distilled=stats["n_with_feasible_samples"],
        mean_feasible_rate=stats["mean_feasible_rate"])
    artifacts.append(global_art)
    results["global_distillation"] = stats

    # --- per-family artifacts
    for fam, probs in by_family_train.items():
        if len(probs) < 3:
            log.info("skipping family %s (only %d problems)", fam, len(probs))
            results["families"][fam] = {"skipped": "too few training problems",
                                        "n_train": len(probs)}
            continue
        log.info("distilling family artifact %s from %d problems", fam, len(probs))
        rm_f, pm_f, params_f, stats_f = distil_from_problems(
            probs, p_layers=p_layers, shots=shots, seed=seed)
        artifacts.append(CircularArtifact(
            artifact_id=f"circular_{fam}_{EXPERIMENT_ID}", artifact_version="v1",
            source="quantum_simulator", problem_family=fam,
            rank_marginals=rm_f, pair_marginals=pm_f, qaoa_params=params_f,
            n_layers=p_layers, n_problems_distilled=stats_f["n_with_feasible_samples"],
            mean_feasible_rate=stats_f["mean_feasible_rate"]))
        results["families"][fam] = {"distillation": stats_f}

    # --- validate every artifact on held-out problems
    log.info("validating %d artifacts on %d held-out problems", len(artifacts), len(val))
    for art in artifacts:
        applicable = [p for p in val
                      if art.problem_family == "ALL"
                      or classify_circular(p).value == art.problem_family]
        # Validate against the UNGUIDED local-search control, not against
        # greedy. Comparing to greedy would credit the artifact for whatever
        # plain local search finds on its own -- the classic way to manufacture
        # a quantum result that is really just a better classical baseline.
        pairs = []
        control_vs_greedy = []
        for p in applicable:
            greedy_obj = greedy_baseline(p)["objective"]
            control = local_search(p, greedy_baseline(p)["selected_indices"],
                                   artifact=None)["objective"]
            guided = apply_artifact_to_problem(p, art)["objective"]
            pairs.append((control, guided))
            control_vs_greedy.append(greedy_obj - control)

        tmp = QuantumPrior(
            artifact_id=art.artifact_id, artifact_version=art.artifact_version,
            source=art.source, problem_family=art.problem_family,
            variable_marginals=art.rank_marginals, qaoa_params=art.qaoa_params,
            n_layers=art.n_layers, dataset_version="v0.1", graph_version="g1",
            training_split="train", cost_snapshot_ids=["CST_CIRCULAR"],
            quantum_backend="aer_simulator",
            n_problems_distilled=art.n_problems_distilled,
            mean_feasible_rate=art.mean_feasible_rate)
        tmp = validate_prior(tmp, pairs)
        art.deployable = tmp.deployable
        art.validation = tmp.validation
        art.validation["n_applicable_heldout"] = len(applicable)
        art.validation["baseline"] = "unguided_local_search"
        art.validation["control_mean_gain_over_greedy"] = (
            float(np.mean(control_vs_greedy)) if control_vs_greedy else 0.0)
        save_prior(tmp)
        log.info("  %-46s applicable=%2d deployable=%s  %s",
                 art.artifact_id, len(applicable), art.deployable,
                 art.validation.get("reason", ""))

    out_dir = C.RES / "ensemble" / "quantum_priors"
    out_dir.mkdir(parents=True, exist_ok=True)
    for art in artifacts:
        (out_dir / f"{art.artifact_id}.json").write_text(
            json.dumps(art.to_dict(), indent=2, default=str), encoding="utf-8")

    manifest = {
        "experiment_id": EXPERIMENT_ID,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "git_commit": git_commit(),
        "hypothesis": ("Quantum-derived information may transfer within matched "
                       "optimization families even when a global prior does not."),
        "n_train": len(train), "n_validation": len(val),
        "p_layers": p_layers, "shots": shots,
        "artifacts": [
            {"artifact_id": a.artifact_id, "family": a.problem_family,
             "n_distilled": a.n_problems_distilled,
             "mean_feasible_rate": a.mean_feasible_rate,
             "deployable": a.deployable, "validation": a.validation}
            for a in artifacts
        ],
        "any_deployable": any(a.deployable for a in artifacts),
        "distillation": results,
    }
    (C.RES / "manifests" / f"{EXPERIMENT_ID}.json").write_text(
        json.dumps(manifest, indent=2, default=str), encoding="utf-8")
    return manifest


if __name__ == "__main__":
    m = run()
    print(json.dumps(
        {"any_deployable": m["any_deployable"],
         "artifacts": [{k: a[k] for k in
                        ("artifact_id", "family", "n_distilled", "deployable")}
                       for a in m["artifacts"]]},
        indent=2, default=str))
    for a in m["artifacts"]:
        print(f"\n{a['artifact_id']}:")
        print("  ", json.dumps(a["validation"], default=str))
