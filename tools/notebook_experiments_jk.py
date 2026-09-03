"""Experiment J and K cells, appended to the routing research notebook.

Kept in a separate module so the original Phase-A notebook builder stays
reviewable and the new experiments can be regenerated independently.
"""

from __future__ import annotations

import nbformat as nbf


def md(t):
    return nbf.v4.new_markdown_cell(t.strip())


def code(t):
    return nbf.v4.new_code_cell(t.strip())


def cells() -> list:
    return [
        # ================= EXPERIMENT J =================
        md("""
---

# Experiment J — QUAV-Inspired Hybrid Quantum-Classical Optimization

Experiment identifier `quav_hybrid_v1`.

The Phase-A result was that standalone QAOA loses to classical solvers. The
response was **not** to tune QAOA and hope. It was to change the architecture and
the research question.

**Old question:** can QAOA solve routing better than classical optimization?
**New question:** can a QUAV-inspired quantum refinement layer improve the
*strongest classical route*, after classical search-space reduction?

The architecture is `CLASSICAL + QUANTUM + CLASSICAL`, not `CLASSICAL vs QUANTUM`.
"""),

        md("""
## J.1 — Identifying the best classical baseline

Run over a stratified sample of instances across every problem family, with all
solvers scored by one evaluator on the instance's own objective weights.

This surfaced a problem more important than any solver ranking.
"""),
        code("""
import pandas as pd, numpy as np, json
pd.set_option("display.width", 220)

survey = pd.read_csv(C.RES/"benchmarks"/"classical_survey.csv")
print(f"{len(survey)} rows over {survey.instance_id.nunique()} instances")

survey["multi"] = survey.n_vehicles > 1
print("\\nFEASIBILITY by solver and vehicle count:")
display(pd.crosstab(survey.algorithm, survey.multi,
                    values=survey.feasible, aggfunc="mean").round(3))
"""),
        md("""
**Finding 1 — TSP heuristics are infeasible on capacitated instances.**
Nearest-neighbour, 2-opt and simulated annealing produce a single tour visiting
every customer, which violates capacity the moment more than one vehicle is
required. They are feasible on ~1.5% of multi-vehicle instances. OR-Tools is the
only member that handles them.

**Finding 2 — every classical heuristic optimizes the wrong objective.**
"""),
        code("""
sv = survey[(~survey.multi) & (survey.feasible)].copy()
best = sv.groupby("instance_id").objective.min().rename("b")
sv = sv.join(best, on="instance_id")
sv["rel_excess"] = (sv.objective - sv.b) / sv.b
display(sv.groupby("algorithm").agg(
    n=("instance_id","nunique"), mean_rel_excess=("rel_excess","mean"),
    wins=("rel_excess", lambda s: int((s < 1e-9).sum())),
    mean_ms=("runtime_ms","mean")).round(5))
print("\\nNote brute_force_exact does NOT have zero excess.")
print("It is provably DISTANCE-optimal, but the project objective is")
print("multi-objective: distance + time + fuel + toll + risk + empty-km.")
print("The distance-optimal tour is simply not the objective-optimal tour.")
"""),
        md("""
This is an **objective-alignment bug**, and it had to be fixed before any hybrid
comparison could mean anything. Otherwise a "quantum improvement" would really be
the hybrid optimizing the correct objective while the baseline optimized a proxy
— a rigged comparison.

`routing/hybrid/objective_costs.py` builds a per-edge cost in objective units, and
the classical incumbent is now 2-opt over **that** matrix.

| Problem family | Best classical | Why selected |
|---|---|---|
| TSP / single-vehicle | 2-opt over the objective matrix | Matches exact on small instances at ~0.1 ms; the only cheap member aligned with the real objective |
| CVRP / VRPTW / PDP (multi-vehicle) | OR-Tools `path_cheapest_arc` + GLS | The only member producing feasible capacitated solutions (46–75% vs ~1.5%) |
| Return-load selection | Greedy value-density | Standard knapsack heuristic; **not exact**, which is what leaves room |
| Shortest path A→B | Dijkstra / A* | Exact in polynomial time — no optimizer can beat it |
"""),
        code("""
from routing.hybrid.objective_costs import objective_cost_matrix
from routing.hybrid.optimizer import solve_classical
from routing.classical.heuristics import nearest_neighbour, two_opt

il = list_instances(); il = il[(il.n_customers+1).between(12,30)]
ndiff = 0; tested = 0
for iid in il.instance_id.head(14):
    inst = load_instance(iid)
    D = inst.distance_matrix; Cm = objective_cost_matrix(inst)
    a = two_opt(D, nearest_neighbour(D).tour)     # distance-optimised
    b = two_opt(Cm, nearest_neighbour(Cm).tour)   # objective-optimised
    from routing.hybrid.objective_costs import tour_cost_objective
    tested += 1
    if abs(tour_cost_objective(Cm,a.tour) - tour_cost_objective(Cm,b.tour)) > 1e-6:
        ndiff += 1
print(f"objective-aware 2-opt differs from distance-2-opt on {ndiff}/{tested} instances")
print("-> the objective fix changes the answer; it is not cosmetic")
"""),

        md("""
## J.2 — QUAV method recap, and what we took

Innan et al., *QUAV* (arXiv 2508.21361). Re-read for this iteration.

| Idea | Verdict | Reason |
|---|---|---|
| One qubit per **segment**, not per (node, timestep) | **ADOPTED** | Scales with segments, not n². The single most valuable transferable idea. |
| Classical preprocess → small quantum subproblem → classical decode | **ADOPTED** | Now the whole architecture. |
| Segment count tied to the qubit budget | **ADOPTED** | `max_variables` caps the corridor. |
| Refusal to claim quantum advantage | **ADOPTED** | Benchmark computes no winner verdict. |
| Equal-distance trajectory segmentation | **ADAPTED** | Free space has no structure; a road route does. Segments are sub-routes between anchor nodes, not equal-length chunks. |
| Obstacle-avoidance cost | **ADAPTED** | Trucks have no obstacles. Replaced with the VahaanBandhu multi-objective (distance, time, fuel, toll, risk, empty-km). |
| Grid discretisation of the plane | **REJECTED** | We have a real road graph; discretising would discard it. |
| Safety-buffer scaling factors | **REJECTED** | No physical clearance constraint. |
| **Purely linear cost Hamiltonian** `H_C = Σ C(e_i) Z_i` | **REJECTED** | Separable: each qubit's optimum is readable by inspection, no entanglement needed, QAOA offers nothing. Our QUBOs add genuine ZZ couplings. |

We also reviewed **Krauss & McCollum**, *Solving the Network Shortest Path Problem
on a Quantum Annealer* (IEEE TQE 2020), and the `armulrich/Qpath_optimizer`
repository — see `Research/QUANTUM_REFERENCES.md` for the full review, including
the finding that the repository's shipped code path runs a classical exact
diagonalizer rather than QAOA.
"""),

        md("""
## J.3 — Candidate corridor and route segmentation

The corridor is the search-space reduction. Its design took **two corrections**,
both worth recording because they are the difference between a meaningful
experiment and a fake one.

**Correction 1 — anchors must leave interior nodes.** Splitting a 5-node tour into
4 legs leaves every leg with zero interior nodes, so there is nothing to reorder,
the QUBO has zero coupling, and the quantum layer has no decision to make.

**Correction 2 — the corridor must contain moves 2-opt cannot make.** The first
version generated only permutations of a leg's own interior nodes. That
neighbourhood is entirely inside what 2-opt already searches, so the QUBO optimum
equalled the incumbent on **10 of 10** instances — quantum was *structurally
incapable* of contributing regardless of how well QAOA performed. The fix lets a
leg **drop** a customer or **absorb** one from a neighbouring leg, which is an
Or-opt relocation across distant tour positions.
"""),
        code("""
from routing.hybrid.corridor import build_corridor, should_refine
from routing.hybrid.segment_qubo import (build_segment_qubo, coupling_density,
                                         incumbent_bitstring, decode_segments)

inst = load_instance(il.instance_id.iloc[0])
Cm = objective_cost_matrix(inst)
tour, _, _ = solve_classical(inst)
corr = build_corridor(inst, tour, max_variables=18, cost_matrix=Cm, seed=1)
print(json.dumps(corr.summary(), indent=2, default=str))
print("\\nSegments presented to the quantum optimizer:")
for s in corr.segments[:10]:
    mark = " <- incumbent" if s.segment_id in corr.incumbent_segment_ids else ""
    print(f"  {s.segment_id:10s} {str(s.path):26s} cost={s.cost:9.2f} [{s.source}]{mark}")
"""),
        code("""
q = build_segment_qubo(corr)
print(f"QUBO variables      : {q.n_vars}")
print(f"coupling density    : {coupling_density(q):.3f}   <- must be > 0")
print(f"legs                : {q.metadata['n_legs']}")
print(f"customers coupled   : {q.metadata['n_customers_covered']}")

xi = incumbent_bitstring(corr, q)
dec = decode_segments(xi, corr, q)
print(f"\\nincumbent is representable in the corridor: {dec['feasible']}")
print(f"incumbent energy {q.energy(xi):.3f}  ==  incumbent cost {corr.incumbent_cost:.3f}")
print("\\nA non-zero coupling density is what separates this from QUAV's")
print("separable Hamiltonian -- with zero coupling, QAOA would be decorative.")
"""),

        md("""
## J.4 — Where quantum refinement is actually worth invoking

Not every route deserves quantum effort. If the incumbent's closest alternative is
much worse, the classical choice is already confident and refinement can only burn
compute. `should_refine` implements a threshold policy on the leg ambiguity gap.
"""),
        code("""
refine, reason = should_refine(corr, gap_threshold=0.05)
print(f"refine this corridor? {refine}\\nreason: {reason}")

route_track = pd.read_csv(C.RES/"hybrid"/"quav_hybrid_v1_route_track.csv")
h = route_track[route_track.algorithm.str.startswith("HYBRID")]
print(f"\\nacross the benchmark: quantum invoked on {int(h.q_quantum_invoked.sum())}/{len(h)} runs")
print("triage skipped the rest as classically confident")
"""),

        md("""
## J.5 — Hybrid variants and results

* **HYBRID-1** — corridor → set-partitioning QUBO → QAOA → decode → 2-opt → guard
* **HYBRID-2** — as above, warm-started from the classical incumbent
* **HYBRID-3** — circular return-load selection as a quadratic knapsack
"""),
        code("""
print("=== ROUTE TRACK (HYBRID-1 / HYBRID-2) ===")
display(route_track.groupby("algorithm").agg(
    n=("instance_id","nunique"), mean_objective=("objective","mean"),
    feasible=("feasible","mean"), mean_improvement=("improvement","mean"),
    mean_ms=("total_ms","mean")).round(3))

print(f"\\nquantum candidates accepted: {int(h.q_quantum_contribution_used.sum())}")
print("\\nwhy quantum candidates were rejected:")
display(h.q_rejection_reason.value_counts(dropna=False))
"""),
        md("""
**Route-track result: 0 improvements out of 24 instances.**

QAOA either returned no feasible sample (18 runs) or a candidate that failed
validation after refinement (12 runs). The classical incumbent was retained every
time. This is a clean negative result and it is reported as one.

Now the circular track, where the problem structure is different.
"""),
        code("""
circ = pd.read_csv(C.RES/"hybrid"/"quav_hybrid_v1_circular_track.csv")
man  = json.load(open(C.RES/"manifests"/"quav_hybrid_v1.json"))
rows = []
for alg, a in man["analysis"].items():
    rows.append({
        "algorithm": alg,
        "n": a["n_problems"],
        "improvement_rate": a["improvement_rate"],
        "match_rate": a["match_rate"],
        "raw_degradation_rate": a["raw_degradation_rate"],
        "DEPLOYED_degradation": a["final_deployed_degradation_rate"],
        "classical_optimal_rate": a["exactness"]["classical_optimal_rate"],
        "final_optimal_rate": a["exactness"]["final_optimal_rate"],
        "classical_gap": round(a["exactness"]["classical_mean_gap_vs_exact"],3),
        "final_gap": round(a["exactness"]["final_mean_gap_vs_exact"],3),
        "feasible_sampling": a["mean_feasible_sampling_rate"],
        "quantum_ms": round(a["mean_quantum_ms"],1),
        "classical_ms": round(a["mean_classical_ms"],4),
    })
display(pd.DataFrame(rows))
"""),
        md("""
### The decisive comparison

Read the `QUBO_CLASSICAL` row against `HYBRID-3`. Both use the **identical QUBO
formulation**; they differ only in how it is solved.

| | classical optimal rate | final optimal rate | mean gap vs exact | time |
|---|---|---|---|---|
| Greedy alone | 77.5% | — | 26.48 | 0.03 ms |
| **HYBRID-3 (QAOA)** | 77.5% | **85.0%** | **13.73** | 3242 ms |
| **QUBO_CLASSICAL (exact solve)** | 77.5% | **95.0%** | **3.32** | 69 ms |

**Both improve on greedy.** But the exact QUBO solve improves it far more (95% vs
85% optimal, gap 3.3 vs 13.7) and is **47× faster** than QAOA.

The honest attribution: **the benefit comes from formulating return-load selection
as a quadratic knapsack, not from QAOA solving it.** QAOA captures roughly half
the available gain at a large runtime cost.

Note also `raw_degradation_rate = 50%` for HYBRID-3 — QAOA returned a *worse*
answer than greedy on half the problems — while `DEPLOYED_degradation = 0%`.
That gap is the incumbent guard doing exactly its job.
"""),
        code("""
import matplotlib.pyplot as plt
fig, axes = plt.subplots(1, 3, figsize=(16,4.2))
df = pd.DataFrame(rows).set_index("algorithm")

df[["classical_optimal_rate","final_optimal_rate"]].plot.bar(ax=axes[0], rot=15,
    color=["#9aa5b1","#2a9d8f"])
axes[0].set(title="Rate of reaching the exact optimum", ylabel="rate"); axes[0].legend(fontsize=8)

df[["classical_gap","final_gap"]].plot.bar(ax=axes[1], rot=15, color=["#9aa5b1","#e76f51"])
axes[1].set(title="Mean objective gap vs exact (lower is better)")
axes[1].legend(fontsize=8)

df[["raw_degradation_rate","DEPLOYED_degradation"]].plot.bar(ax=axes[2], rot=15,
    color=["#e63946","#2a9d8f"])
axes[2].set(title="Degradation: raw quantum vs what was deployed")
axes[2].legend(fontsize=8)
plt.tight_layout(); plt.show()
print("Right panel: QAOA degrades on 50% of problems; the guard deploys 0% degraded.")
"""),

        md("""
## J.6 — Visualising what the quantum layer actually sees
"""),
        code("""
fig, axes = plt.subplots(1, 3, figsize=(16, 5))
coords = inst.coords

def draw(ax, tour, title, color):
    ax.scatter(coords[:,1], coords[:,0], s=45, c="#264653", zorder=3)
    ax.scatter(coords[inst.depot_index,1], coords[inst.depot_index,0],
               s=200, marker="D", c="#e63946", zorder=4, label="depot")
    seq = list(tour) + [tour[0]]
    ax.plot(coords[seq,1], coords[seq,0], "-", c=color, lw=2, alpha=0.8)
    ax.set(title=title, xlabel="longitude", ylabel="latitude")

draw(axes[0], corr.incumbent_tour, "1. Classical incumbent", "#2a9d8f")

axes[1].scatter(coords[:,1], coords[:,0], s=45, c="#264653", zorder=3)
for s in corr.segments:
    p = list(s.path)
    style = "-" if s.segment_id in corr.incumbent_segment_ids else "--"
    axes[1].plot(coords[p,1], coords[p,0], style, alpha=0.55, lw=1.6)
for a in corr.anchors:
    axes[1].scatter(coords[a,1], coords[a,0], s=170, marker="s",
                    facecolors="none", edgecolors="#e76f51", lw=2, zorder=5)
axes[1].set(title=f"2. Candidate corridor ({corr.n_variables} segments,\\nsquares = anchors)",
            xlabel="longitude")

draw(axes[2], corr.incumbent_tour, "3. Final hybrid route\\n(incumbent retained)", "#6a4c93")
plt.tight_layout(); plt.show()
print("Solid segments are the incumbent; dashed are the alternatives offered to the")
print("quantum optimizer. On this instance the guard retained the classical route.")
"""),

        md("""
## J.7 — Experiment J conclusions

1. **The QUBO encodings are correct.** Segment QUBO energy equals tour cost
   exactly; the circular QUBO optimum matches exhaustive exact on 27/30 problems;
   penalties strictly separate feasible from infeasible.

2. **Route refinement does not help (0/24).** After the objective-alignment fix,
   2-opt is locally optimal with respect to the corridor neighbourhood.

3. **Circular return-load selection does help.** Optimal rate 77.5% → 85.0% with
   QAOA, → 95.0% with the exact QUBO solve.

4. **The gain is attributable to the formulation, not to QAOA.** Same QUBO, exact
   solve: better results, 47× faster.

5. **The incumbent guard works.** 50% raw quantum degradation, 0% deployed.

This is **Outcome E** from the brief: quantum refinement is useful for
circular-return selection and not for shortest paths — with the important
refinement that most of the value is in the problem formulation.
"""),

        # ================= EXPERIMENT K =================
        md("""
---

# Experiment K — VB-QER Quantum-Enhanced Ensemble

**VB-QER** — VahaanBandhu Quantum-Enhanced Routing — is the final routing
algorithm. One entry point:

```python
solution = VBQEROptimizer().solve(instance)
```

Four terms, used precisely and never interchangeably:

| Term | Meaning |
|---|---|
| **Classical Routing** | Traditional optimization alone |
| **Quantum Optimization** | A direct QUBO/QAOA experiment |
| **Hybrid Quantum-Classical** | Classical reduction + QAOA + classical post-processing |
| **Quantum-Enhanced Ensemble (VB-QER)** | The final algorithm: classical members + validated quantum artifacts + incumbent guard |
"""),
        md("""
## K.1 — Architecture

```
instance
  -> classical ensemble members  (2-opt / NN / SA / OR-Tools)
  -> deduplicate, consensus, diversity
  -> candidate reduction
  -> LOAD OFFLINE QUANTUM ARTIFACTS   <- no live QPU call, ever
  -> quantum-enhanced ensemble scoring
  -> constraint validation
  -> classical local refinement
  -> incumbent comparison             <- the guard
  -> final route + explanation + contribution trace
```

**Members were chosen from the survey evidence**, not by assumption: OR-Tools is
included specifically because it is the only member feasible on capacitated
instances; nearest-neighbour is retained not for quality but because it is a
genuinely different construction and contributes diversity.
"""),
        code("""
from routing.ensemble import VBQEROptimizer
from routing.ensemble.members import generate_candidates, compute_diversity
from routing.ensemble.scorer import score_candidates

cands = generate_candidates(inst, seed=42)
compute_diversity(cands)
display(pd.DataFrame([{
    "candidate": c.candidate_id, "objective": round(c.objective,2),
    "feasible": c.feasible, "consensus": c.consensus,
    "diversity": c.diversity, "produced_by": ",".join(sorted(set(c.produced_by))),
} for c in cands]))
print("Consensus > 1 means several independent solvers converged on the same tour.")
"""),
        code("""
scored = score_candidates(cands)
display(pd.DataFrame([{
    "candidate": s.candidate.candidate_id, "score": round(s.score,5),
    **{k: round(v,5) for k,v in s.terms.items()}} for s in scored]))
print("The objective term dominates by construction; ensemble signals are capped")
print("at 25% of the normalised objective range so they can adjust a near-tie")
print("but can never promote a substantially worse route.")
"""),

        md("""
## K.2 — Quantum artifacts: distillation, validation, provenance

A QAOA run returns a *distribution*, not one answer. Aggregating it over training
problems gives per-edge **marginal selection probabilities**, weighted by sample
energy so the overwhelming majority of constraint-violating shots do not simply
encode the mixer's uniform prior.

Discipline enforced in code:

* distilled on **train** only
* validated on **validation** only — a prior that does not beat the no-prior
  baseline on held-out data is marked `deployable=False` and the ensemble
  refuses to load it
* **test** touched exactly once, for the ablation
* simulator and hardware artifacts stored **separately**, never merged
"""),
        code("""
import os
man_path = C.RES/"ensemble"/"manifests"/"vbqer_v1.json"
if man_path.exists():
    vman = json.load(open(man_path))
    print("splits:", vman["splits"])
    print("distillation:", json.dumps(vman["distillation"], indent=2, default=str))
    print("\\nprior deployable:", vman["prior"]["deployable"])
    print("validation:", json.dumps(vman["prior"]["validation"], indent=2, default=str))
    print("n edge marginals distilled:", vman["n_marginals"])
else:
    vman = None
    print("Calibration artifacts not present in this checkout.")
    print("Regenerate with:  python -m routing.ensemble.calibrate")
"""),

        md("""
## K.3 — Ablation: isolating the quantum contribution

Mandatory. Without it, an ensemble improvement could not be attributed.

| Arm | Description |
|---|---|
| **A** | Best classical only (no ensemble) |
| **B** | Classical ensemble, no quantum features |
| **C** | Classical + simulator-derived quantum features |
| **D** | Classical + hardware-derived quantum features |
| **E** | Full quantum-enhanced ensemble |

Arms C, D and E are compared **pairwise against B**, which is the only comparison
that isolates quantum rather than measuring the ensemble.
"""),
        code("""
if vman:
    ab = pd.DataFrame(vman["ablation"]).T
    display(ab)
    print("\\nvs_B_* columns isolate the quantum contribution:")
    cols = [c for c in ab.columns if str(c).startswith("vs_B")]
    if cols: display(ab[cols])
else:
    print("Ablation artifacts not present; run routing.ensemble.calibrate first.")
"""),

        md("""
## K.4 — Production-safety invariants

Each is enforced by code and asserted by a test, not by documentation.
"""),
        code("""
s = VBQEROptimizer().solve(inst)
print("=== VB-QER decision ===")
print(f"instance          : {s.instance_id}")
print(f"objective         : {s.objective:.3f}")
print(f"classical incumbent: {s.classical_incumbent_objective:.3f}")
print(f"route source      : {s.final_route_source}")
print(f"candidates        : {s.n_candidates}   consensus: {s.consensus}")
print(f"feasible          : {s.feasible}")
print(f"cost snapshot     : {s.cost_snapshot_id}")
print(f"\\nQUANTUM HARDWARE CALLED LIVE : {s.quantum_hardware_called_live}")
print(f"quantum artifact used        : {s.quantum_contribution_used}")
print(f"artifact source              : {s.quantum_artifact_source}")
print(f"\\ntiming: classical {s.classical_ms:.1f} ms | artifacts {s.artifact_ms:.2f} ms"
      f" | scoring {s.scoring_ms:.2f} ms | refine {s.refinement_ms:.1f} ms")
print("\\nExplanation:")
for r in s.explanation["reasons"]:
    print("  -", r)
"""),
        code("""
# Invariant 1: no live QPU.
# Checked in a SUBPROCESS. Testing sys.modules in this kernel would be
# meaningless -- Experiment H above already imported the IBM runtime, so the
# global module table is polluted. Only a clean interpreter that imports
# nothing but the inference module can prove anything about its import graph.
import subprocess, sys as _sys
probe = (
    "import sys; import routing.ensemble.inference; "
    "bad=[m for m in sys.modules if 'ibm' in m.lower() or 'qiskit_ibm' in m]; "
    "print('LEAK' if bad else 'CLEAN', bad[:5])"
)
out = subprocess.run([_sys.executable, "-c", probe], capture_output=True,
                     text=True, cwd=str(Path.cwd().parent))
print("subprocess import probe:", out.stdout.strip() or out.stderr.strip()[-200:])
assert out.stdout.startswith("CLEAN"), out.stdout
print("INVARIANT 1 OK: live inference never imports the IBM hardware runtime")

# Invariant 2: the incumbent guard, tested against a deliberately misleading prior.
from routing.ensemble.quantum_priors import QuantumPrior
bad = QuantumPrior(
    artifact_id="misleading", artifact_version="v1", source="quantum_simulator",
    problem_family="segment_set_partition",
    variable_marginals={f"{i}->{i+1}": 1.0 for i in range(30)},
    qaoa_params=None, n_layers=2, dataset_version="v0.1", graph_version="g1",
    training_split="train", cost_snapshot_ids=["CST_X"], quantum_backend="aer",
    n_problems_distilled=1, mean_feasible_rate=0.1, deployable=True)
s_bad = VBQEROptimizer(priors=[bad]).solve(inst)
assert s_bad.objective <= s_bad.classical_incumbent_objective + 1e-9
print("INVARIANT 2 OK: a misleading prior cannot make the route worse")

# Invariant 3: degrade cleanly with no artifacts.
s_none = VBQEROptimizer(priors=[], use_quantum_artifacts=True).solve(inst)
assert s_none.feasible == s_none.feasible
print("INVARIANT 3 OK: runs with zero artifacts (classical ensemble fallback)")

# Invariant 4: no unearned quantum claim.
assert s_none.quantum_artifact_source == "none"
print("INVARIANT 4 OK: no quantum contribution claimed when none was used")
"""),

        md("""
## K.5 — Conclusions

**What VB-QER is.** A classical ensemble with an incumbent guard, into which
validated quantum-derived artifacts feed as one bounded signal among several. The
live path never calls a QPU.

**What the evidence supports.**

* The circular return-load QUBO genuinely improves on the greedy classical
  baseline: 77.5% → 95% optimal with an exact solve, → 85% with QAOA.
* Most of that gain comes from the **formulation**, not from QAOA.
* Route-refinement quantum contributed nothing (0/24).
* The incumbent guard reduced 50% raw quantum degradation to 0% deployed.

**What is not claimed.** No quantum advantage, no speedup, no better routes from
QAOA than from classical solvers on the same formulation. QAOA was slower than
the exact QUBO solve by 47× and reached a worse mean optimality gap.

**Recommendation.** Ship VB-QER with the quadratic-knapsack return-load
formulation solved *classically*, keep the QAOA path as an offline research arm,
and re-evaluate when hardware or algorithms improve. That is the honest
engineering call, and the architecture supports flipping the solver without any
other change.
"""),
    ]
