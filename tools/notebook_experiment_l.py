"""Experiment L: improving the quantum component inside VB-QER."""

from __future__ import annotations

import nbformat as nbf


def md(t):
    return nbf.v4.new_markdown_cell(t.strip())


def code(t):
    return nbf.v4.new_code_cell(t.strip())


def cells() -> list:
    return [
        md("""
---

# Experiment L — Improving the Quantum Component Inside VB-QER

**Framing.** VB-QER is the fixed final algorithm. This experiment asks *how to
raise the quantum contribution within it* — not whether to use it. Every arm
below is a **VB-QER configuration**, not a competing algorithm.

| Config | VB-QER with... |
|---|---|
| A | classical members only (greedy) |
| B | + exact selection (ground truth) |
| C | + classical QUBO backend |
| D | + QAOA at depth p ∈ {1,2,3,4,6,8} |
| E | + warm-start QAOA |
| F | + noise-model QAOA |

**Scope decision.** Shortest path is deliberately excluded. Dijkstra/A\\* solve it
exactly in polynomial time, so no optimizer — quantum or otherwise — can improve
on it; those members stay inside VB-QER unchanged. Return-load selection is a
quadratic knapsack with measured greedy suboptimality, which is where the room
actually is.
"""),
        code("""
from routing.ensemble.status import render, summary
print(render())
"""),
        md("""
## L.1 — The circular optimizer components, measured

Before any quantum question, establish what VB-QER's classical circular
components achieve. All three are components *inside* VB-QER.
"""),
        code("""
import json, numpy as np, pandas as pd
from vb import config as C

man_path = C.RES/"manifests"/"vbqer_circular_v1.json"
if man_path.exists():
    cman = json.load(open(man_path))
    print(f"sizes {cman['sizes']}  depths {cman['depths']}  "
          f"{cman['n_rows']} rows over {cman['n_problems']} problems")
    an = cman["analysis"]
    display(pd.DataFrame(an["by_config"]))
else:
    cman = None
    print("Study artifacts not present. Regenerate with:")
    print("  python -m routing.evaluation.circular_study --sizes 4,6,8,10,12 --depths 1,2,3,4,6,8")
"""),
        code("""
if cman:
    print("=== Incumbent guard behaviour per configuration ===")
    guard = pd.DataFrame(cman["analysis"]["guard"])
    display(guard)
    print("\\ndegraded_before_guard vs degraded_after_guard is the guard's work.")
    print("after-guard degradation must be 0.0 for every arm.")
"""),
        md("""
## L.2 — QAOA depth sweep

Does more circuit depth help? This is the question a "just tune QAOA harder"
response assumes the answer to.
"""),
        code("""
if cman and "by_depth" in cman["analysis"]:
    bd = pd.DataFrame(cman["analysis"]["by_depth"])
    display(bd)

    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 3, figsize=(16, 4))
    axes[0].plot(bd.p_layers, bd.mean_gap, "o-", color="#e76f51")
    axes[0].set(title="Mean optimality gap vs QAOA depth", xlabel="p layers", ylabel="gap")
    axes[1].plot(bd.p_layers, bd.optimal_rate, "o-", color="#2a9d8f")
    axes[1].set(title="Rate of reaching the exact optimum", xlabel="p layers")
    axes[2].plot(bd.p_layers, bd.mean_runtime_ms, "o-", color="#6a4c93")
    axes[2].set(title="Runtime vs depth", xlabel="p layers", ylabel="ms")
    axes[2].set_yscale("log")
    plt.tight_layout(); plt.show()
"""),
        md("""
## L.3 — Scaling with option-set size

Qubit count is `n_options + ~6 slack bits`. This is the hard ceiling on what the
quantum component can address.
"""),
        code("""
if cman and "by_size" in cman["analysis"]:
    display(pd.DataFrame(cman["analysis"]["by_size"]))
    print("\\nGreedy headroom by size -- this bounds any possible gain:")
    print(json.dumps(cman["analysis"]["greedy_headroom"], indent=2, default=str))
"""),

        md("""
## L.4 — Artifact distillation and the transfer hypothesis

The route-track prior failed validation (0/15). Two candidate explanations, and
they call for different fixes:

1. **Thin yield** — only 12/30 route-track instances produced feasible samples.
2. **A single global prior may be the wrong object** — return-load problems differ
   structurally, and a marginal averaged across all of them describes none.

The hypothesis under test:

> Quantum-derived information may transfer within **matched** optimization
> families even when a global prior does not generalise.

### The methodological point that decides this experiment

Artifacts are validated against an **unguided local-search control**, not against
greedy. Validating against greedy would credit the artifact for whatever plain
local search finds on its own — the standard way to manufacture a quantum result
that is really just a better classical baseline.
"""),
        code("""
apath = C.RES/"manifests"/"vbqer_circular_artifacts_v1.json"
if apath.exists():
    aman = json.load(open(apath))
    print("hypothesis:", aman["hypothesis"])
    print(f"\\ntrain={aman['n_train']}  validation={aman['n_validation']} (disjoint)")
    rows = []
    for a in aman["artifacts"]:
        v = a["validation"]
        rows.append({
            "artifact": a["artifact_id"].replace("_vbqer_circular_artifacts_v1",""),
            "family": a["family"],
            "n_distilled": a["n_distilled"],
            "feasible_rate": round(a["mean_feasible_rate"] or 0, 4),
            "n_heldout": v.get("n_applicable_heldout"),
            "improved": v.get("n_improved"),
            "degraded": v.get("n_degraded"),
            "mean_delta": v.get("mean_delta"),
            "DEPLOYABLE": a["deployable"],
            "control_gain_over_greedy": round(v.get("control_mean_gain_over_greedy", 0), 2),
        })
    display(pd.DataFrame(rows))
    print(f"\\nany artifact deployable: {aman['any_deployable']}")
else:
    aman = None
    print("Run:  python -m routing.ensemble.circular_distill")
"""),
        md("""
### Result: the transfer hypothesis is **not supported**

All three artifacts failed independently — the global prior and *both*
family-specific priors. 0 improved, 0 degraded, mean delta 0.0.

Two things this rules out:

* **It is not a data-volume problem.** The circular track produced feasible QAOA
  samples on 30/30 problems, against the route track's 12/30. More and better
  signal did not help.
* **It is not a family-mismatch problem.** Matching on structural family — the
  specific fix this experiment was designed to test — changed nothing.

Note the `control_gain_over_greedy` column: the unguided control gains 33–51
objective units over greedy. That gain is real, and it is entirely classical.
The quantum prior adds nothing on top of it.
"""),
        code("""
# The component ranking that came out of the control arm, on 60 held-out problems.
from routing.hybrid.circular_builder import build_benchmark_set
from routing.hybrid.circular_qubo import (greedy_baseline, exhaustive_baseline,
                                          build_circular_qubo, decode_circular)
from routing.ensemble.circular_distill import local_search
from routing.quantum.qubo import brute_force_qubo

ps = build_benchmark_set(n_problems=30, seed=31337, max_options=7)
rows = []
for p in ps:
    ex = exhaustive_baseline(p)["objective"]
    g = greedy_baseline(p)
    ls = local_search(p, g["selected_indices"], artifact=None)["objective"]
    q = build_circular_qubo(p); qo = None
    if q.n_vars <= 22:
        x, _ = brute_force_qubo(q, max_vars=22)
        d = decode_circular(x, p, q)
        qo = d["objective"] if d["feasible"] else None
    rows.append({"greedy": g["objective"], "local_search": ls,
                 "classical_qubo": qo, "exact": ex})
df = pd.DataFrame(rows)
summary_rows = []
for col in ["greedy", "local_search", "classical_qubo"]:
    ok = df[col].notna()
    summary_rows.append({
        "VB-QER circular component": col,
        "optimal_rate": float(np.isclose(df.loc[ok, col], df.loc[ok, "exact"]).mean()),
        "mean_gap": float((df.loc[ok, col] - df.loc[ok, "exact"]).mean()),
    })
display(pd.DataFrame(summary_rows).round(4))
print("\\nAll three are VB-QER components. The QUBO is the primary circular")
print("optimizer; local search is the fallback where exact solve is intractable.")
"""),

        md("""
## L.5 — Experiment L conclusions

**Component status after this experiment** (the architecture is unchanged and
was never in question):

| VB-QER component | Status | Change |
|---|---|---|
| Circular QUBO (exact backend) | ACTIVE | confirmed primary — 98.3% optimal |
| Circular local search | **ACTIVE (new)** | promoted; 85.0% optimal, +14.5 over greedy |
| QAOA research arm | ACTIVE OFFLINE | unchanged |
| Global circular prior | **REJECTED** | 0/20 held-out |
| Per-family circular priors | **REJECTED** | 0/14 and 0/6 — transfer hypothesis not supported |
| Artifact slot | VALIDATION-GATED | still open; nothing has passed |

**What was learned that is actionable.** The unguided control arm — included
purely as an honesty mechanism — turned out to be a genuinely better classical
component than greedy, and is now an active part of VB-QER. The experiment
improved VB-QER; it just did not improve it *via quantum*.

**What is still not claimed.** No quantum advantage, no deployable quantum
artifact, no quantum contribution to any live decision.

**Where the remaining room is.** The exact QUBO solve reaches 98.3% optimal, so
on problems of this size there is only ~1.7% headroom left for *any* optimizer.
A quantum contribution would have to come from problem sizes where the exact
solve stops being tractable — that is `n_options` beyond ~16, where the QUBO
exceeds the statevector budget and exhaustive selection becomes expensive. That
is the regime worth attacking next, and it is a scaling question rather than a
tuning question.
"""),
    ]
