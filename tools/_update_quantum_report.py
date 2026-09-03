"""One-shot: append Part II (QUAV hybrid results) to the quantum research report."""

from __future__ import annotations

import pathlib

SECTION = r"""
---

# Part II - QUAV-Inspired Hybrid Quantum-Classical Refinement

Experiment `quav_hybrid_v1`. This part supersedes Part I's framing, though not
its findings.

## 11. Hypothesis and the changed research question

Part I asked whether QAOA could *solve* routing better than classical
optimization. The answer was no, and tuning QAOA further would not have changed
it. The question was therefore replaced:

> **Can a QUAV-inspired quantum refinement layer improve the strongest classical
> route, after classical search-space reduction?**

Architecture: `CLASSICAL + QUANTUM + CLASSICAL`, with the classical solution as a
safety net rather than a competitor.

## 12. Identifying the best classical baseline (Step 1)

A stratified survey across every problem family, all solvers scored by one
evaluator on the instance's own objective weights. Two findings, both of which
changed the implementation:

**Finding 1 - TSP heuristics are infeasible on capacitated instances.**
Nearest-neighbour, 2-opt and simulated annealing emit a single tour covering
every customer, which violates capacity as soon as more than one vehicle is
needed. Feasibility on multi-vehicle instances: ~1.5% for those three, 46-75%
for OR-Tools.

**Finding 2 - every classical heuristic was optimizing the wrong objective.**
Even `brute_force_exact`, which is provably distance-optimal, showed a 2.4% mean
excess against the best objective found. The project objective is
distance + time + fuel + toll + risk + empty-km; the distance-optimal tour is
simply not the objective-optimal tour.

This was an objective-alignment bug, not a quantum question, and it had to be
fixed first. Otherwise any "quantum improvement" would really have been the
hybrid optimizing the correct objective against a baseline optimizing a proxy.
`routing/hybrid/objective_costs.py` now builds per-edge costs in objective units,
and the incumbent is 2-opt over that matrix. The fix changes the chosen tour on
**8 of 14** test instances, so it is not cosmetic.

### Best classical per family

| Problem | Best classical | Objective | Runtime | Feasible | Why selected |
|---|---|---|---|---|---|
| TSP / single-vehicle | 2-opt over the objective matrix | matches exact on small instances | ~0.10 ms | 57% | Cheapest member aligned with the real objective |
| CVRP (multi-vehicle) | OR-Tools `path_cheapest_arc` + GLS | 2.0% mean rel. excess | ~5000 ms | 46-75% | Only member producing feasible capacitated solutions |
| VRPTW / PDP | OR-Tools `path_cheapest_arc` | 0.1% mean rel. excess | ~5000 ms | 46% | Handles time windows natively |
| Return-load selection | Greedy value-density | 77.5% optimal | 0.03 ms | 100% | Standard knapsack heuristic; **not exact** |
| Shortest path A to B | Dijkstra / A* | exact | <1 ms | 100% | Polynomial-time exact; unbeatable by any optimizer |

Feasibility rates below 100% reflect single-tour solutions applied to
capacitated instances, which is a property of the instance set rather than a
solver defect.

## 13. Two corrections that made the experiment meaningful

**Correction 1 - anchors must leave interior nodes.** Splitting a 5-node tour
into 4 legs leaves each leg with zero interior nodes: nothing to reorder, zero
QUBO coupling, no decision for the quantum layer. Anchor count is now derived
from a target interior size.

**Correction 2 - the corridor must contain moves 2-opt cannot make.** The first
corridor generated only permutations of a leg's own interior nodes. That
neighbourhood lies entirely inside what 2-opt already searches, so the QUBO
optimum equalled the incumbent on **10 of 10** instances. The quantum layer was
*structurally incapable* of contributing, independent of QAOA quality. Legs can
now **drop** a customer or **absorb** one from a neighbour - an Or-opt
relocation across distant tour positions, outside the 2-opt neighbourhood, and
coupled across legs through the coverage constraint.

Recording these matters: without them, a null result would have been
misattributed to QAOA rather than to a corridor that could not express an
improvement.

## 14. Quantum formulations

### 14.1 Segment set-partitioning (HYBRID-1/2)

```
x_s = 1  iff candidate segment s is selected

min  sum_s c_s x_s
   + A_leg   * sum_L (sum_{s in L} x_s - 1)^2       exactly one segment per leg
   + A_cover * sum_v (sum_{s covers v} x_s - 1)^2   each customer served once
```

Set partitioning is NP-hard, and segments overlap in coverage, so leg choices are
genuinely coupled. Measured coupling density 0.2-0.6.

### 14.2 Return-load quadratic knapsack (HYBRID-3)

```
x_i = 1  iff return load i is accepted

min  sum_i (detour_i - revenue_i) x_i
   + sum_{i<j} synergy_ij x_i x_j        shared-corridor interaction
   + A_cap * (capacity equality with binary slack)^2
```

`synergy_ij` is the extra cost of serving both loads relative to serving each
alone - negative when they share a corridor. This is what makes the problem
quadratic rather than a per-item ranking. Coupling density 1.00.

**Why this problem and not shortest path.** Dijkstra is exact for shortest path;
no optimizer can beat it. Quadratic knapsack is NP-hard and the greedy baseline
is measurably suboptimal, so there is genuine room. This is also the most
VahaanBandhu-specific decision in the system: it is what converts an empty return
leg into revenue.

**Capacity encoding, and a bug worth recording.** The constraint is an inequality,
which a QUBO cannot express directly, so binary slack converts it to an equality.
With real-valued kilogram demands that equality is *never* exactly satisfiable, so
every assignment incurred the squared penalty and the optimizer returned the empty
set on every problem. Demands and capacity are now quantised to a common integer
grid, with demands rounded **up** and capacity **down** so quantised feasibility
implies true feasibility. Capacity is re-checked exactly at decode regardless.

## 15. Classical validation before any quantum execution

| Check | Result |
|---|---|
| Segment QUBO: incumbent energy equals incumbent tour cost | exact |
| Segment QUBO: optimum decodes to a connected covering tour | pass |
| Circular QUBO optimum vs exhaustive exact | **27/30 identical** |
| Circular QUBO proposes an infeasible set | 2/30, all caught at decode |
| Penalty separation (worst feasible < best infeasible) | holds over all 2^n states |
| Coupling density > 0 (not separable) | 0.2-0.6 segment, 1.00 circular |

## 16. Results

### 16.1 Route-refinement track (HYBRID-1, HYBRID-2)

24 instances across four categories, one cost snapshot.

| Algorithm | Instances | Mean objective | Mean improvement | Mean runtime |
|---|---|---|---|---|
| BEST_CLASSICAL | 24 | 2225.45 | - | 1.4 ms |
| HYBRID-1 | 24 | 2225.45 | **0.0** | 1634 ms |
| HYBRID-2 (warm-start) | 24 | 2225.45 | **0.0** | 1611 ms |

Quantum was invoked on 30 of 48 runs (triage skipped the rest as classically
confident) and **accepted 0 times**. Rejections: no feasible QAOA sample (18),
candidate infeasible after refinement (12).

**This is a clean negative result and is reported as one.** After the
objective-alignment fix, 2-opt is locally optimal with respect to the corridor.

### 16.2 Circular return-load track (HYBRID-3)

40 problems, 4-6 options each.

| Method | Optimal rate | Mean gap vs exact | Improvement rate | Raw degradation | **Deployed degradation** | Time |
|---|---|---|---|---|---|---|
| Greedy (classical) | 77.5% | 26.48 | - | - | - | 0.03 ms |
| **HYBRID-3 (QAOA)** | **85.0%** | **13.73** | 10% | 50% | **0%** | 3242 ms |
| HYBRID-3 warm-start | 85.0% | 15.69 | 10% | 45% | **0%** | 3275 ms |
| **QUBO_CLASSICAL** | **95.0%** | **3.32** | 18.4% | 0% | **0%** | 69 ms |

Mean improvement when QAOA won: 127.5 (median 119.8). Mean feasible sampling
rate 16.4% - far healthier than Part I's 0.061%, because the QUBO is smaller
and better conditioned.

### 16.3 The decisive attribution

`QUBO_CLASSICAL` and `HYBRID-3` use the **identical QUBO**; they differ only in
the solver. The exact solve reaches 95% optimal with a 3.32 gap in 69 ms; QAOA
reaches 85% with a 13.73 gap in 3242 ms - **47x slower and measurably worse**.

**The benefit is attributable to the formulation, not to QAOA.** Framing
return-load selection as a quadratic knapsack is what improves on greedy. QAOA
captures roughly half of that available gain at large runtime cost.

### 16.4 The incumbent guard

QAOA returned a worse answer than greedy on **50%** of problems. Deployed
degradation was **0%**. The guard is not decorative; it is doing continuous work.

## 17. Limitations of Part II

1. **Small scale.** 24 route instances, 40 circular problems, 4-6 options each.
2. **Synthetic costs** from the offline detour model, not measured routing.
3. **Fixed p=2**; no systematic depth sweep.
4. **Noiseless simulator**; optimistic relative to hardware.
5. **Route-track feasibility is low** (single-tour solutions on capacitated
   instances). The objective comparison is valid because all algorithms share it,
   but absolute feasibility should not be read as a system property.
6. **Warm-start was crude** - fixed small initial angles rather than parameters
   transferred from a matched problem family. A negative warm-start result here
   does not close the question.

## 18. Recommendation

Ship the quadratic-knapsack return-load formulation solved **classically**. Keep
QAOA as an offline research arm. The architecture supports swapping the solver
without any other change, so this is reversible when hardware or algorithms
improve.

---

# Part I (continued)
"""


def main() -> None:
    p = pathlib.Path("Research/QUANTUM_ROUTE_OPTIMIZATION.md")
    s = p.read_text(encoding="utf-8")
    marker = "\n## 7. IBM Quantum hardware (Experiment H)"
    if "# Part II - QUAV-Inspired Hybrid" in s:
        print("already applied")
        return
    assert marker in s, "insertion marker not found"
    s = s.replace(marker, SECTION.rstrip() + "\n" + marker, 1)
    p.write_text(s, encoding="utf-8")
    print(f"updated {p} ({len(s.splitlines())} lines)")


if __name__ == "__main__":
    main()
