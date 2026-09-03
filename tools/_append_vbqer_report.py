"""One-shot: append Part III (VB-QER ensemble + ablation) to the quantum report."""

from __future__ import annotations

import json
import pathlib

SECTION = r"""
---

# Part III - VB-QER: The Quantum-Enhanced Ensemble

Experiment `vbqer_v1`. **VB-QER** (VahaanBandhu Quantum-Enhanced Routing) is the
final routing algorithm and the single canonical entry point:

```python
from routing.ensemble import VBQEROptimizer
solution = VBQEROptimizer().solve(instance)
```

## 19. Terminology, used precisely

| Term | Meaning |
|---|---|
| **Classical Routing** | Traditional optimization alone |
| **Quantum Optimization** | A direct QUBO/QAOA experiment |
| **Hybrid Quantum-Classical** | Classical reduction + QAOA + classical post-processing |
| **Quantum-Enhanced Ensemble (VB-QER)** | The final algorithm: classical members + *validated* quantum artifacts + incumbent guard |

These are not interchangeable, and the codebase uses them consistently.

## 20. Architecture

```
instance
  -> classical ensemble members  (2-opt / NN / SA x2 / OR-Tools)
  -> deduplicate -> consensus + diversity signals
  -> candidate reduction
  -> LOAD OFFLINE QUANTUM ARTIFACTS      <- never a live QPU call
  -> quantum-enhanced ensemble scoring   (signal influence capped at 25%)
  -> constraint validation
  -> classical local refinement (2-opt)
  -> incumbent comparison                <- the guard
  -> final route + explanation + contribution trace
```

Members were selected from survey evidence, not assumption: OR-Tools is included
because it is the only member feasible on capacitated instances; nearest-
neighbour is retained not for quality but because it is a structurally different
construction and therefore contributes diversity.

## 21. Quantum artifacts: distillation and the deployment gate

A QAOA run yields a *distribution*, not one answer. Aggregating it across
training problems gives per-edge marginal selection probabilities, energy-
weighted so that constraint-violating shots (the large majority) do not simply
re-encode the mixer's uniform prior.

Discipline: distilled on **train** only, validated on **validation** only, and
**test** touched exactly once for the ablation. Simulator and hardware artifacts
are stored separately and never merged.

### The gate fired

| Metric | Value |
|---|---|
| Training instances distilled | 30 |
| Instances yielding feasible QAOA samples | 12 |
| Edge marginals distilled | 90 |
| Held-out validation instances | 15 |
| **Instances improved by the prior** | **0** |
| Instances degraded | 0 |
| Mean delta | **0.0** |
| **Deployed** | **NO** |

The distilled prior did **not generalise** to held-out instances, so
`validate_prior` marked it `deployable=False` and the ensemble refuses to load
it. This is the guard against shipping a "quantum feature" that is really noise
fitted to the training set, and it worked on the first real test.

## 22. Ablation (test split, touched once)

| Arm | Mean objective | Median | Mean empty km | Mean ms | Quantum used | vs B improved / degraded / identical |
|---|---|---|---|---|---|---|
| **A** best classical only | 2342.20 | 2068.41 | 84.91 | 1.5 | 0% | - |
| **B** classical ensemble | **2279.99** | **2039.32** | **31.49** | 4054 | 0% | - |
| **C** + simulator quantum | 2279.99 | 2039.32 | 31.49 | 4065 | 0% | 0 / 0 / 15 |
| **D** + hardware quantum | 2279.99 | 2039.32 | 31.49 | 4037 | 0% | 0 / 0 / 15 |
| **E** full ensemble | 2279.99 | 2039.32 | 31.49 | 4058 | 0% | 0 / 0 / 15 |

### What this says, plainly

1. **The ensemble helps.** B beats A by 2.7% on mean objective and cuts mean
   empty kilometres by **63%** (84.9 -> 31.5). Combining several classical
   members with consensus and diversity signals is a real improvement over the
   single best classical solver.

2. **Quantum contributed exactly nothing.** Arms C, D and E are *identical* to B
   on all 15 test instances: 0 improved, 0 degraded, 15 identical, mean delta
   0.0. Because the prior failed validation, `quantum_used_rate` is 0% and the
   quantum path never engaged.

3. **Arm D is vacuous, and is reported as such.** No hardware-derived artifact
   exists (see §23), so arm D is arm B with an empty artifact filter. It is not
   evidence that hardware information is worthless; it is evidence that we do not
   yet have any.

4. **The ensemble costs 2700x more runtime than the best single classical
   solver** (4054 ms vs 1.5 ms), almost entirely from simulated-annealing
   restarts and OR-Tools. For a 2.7% objective gain that trade is defensible
   offline and questionable for live routing; the member set is configurable.

### Answers to the Step 18 questions

| Question | Answer |
|---|---|
| How often were quantum features invoked? | 0% - the prior failed the deployment gate |
| How often did they change candidate ranking? | 0 of 15 |
| How often did that improve the objective? | 0 |
| How often would quantum have degraded it without the guard? | In the HYBRID-3 track, **50%** of raw QAOA answers were worse than greedy |
| Average improvement when quantum genuinely helped | HYBRID-3 only: 127.5 mean, 119.8 median |
| Does hardware beat simulator information? | **Unknown** - no hardware artifact yet |
| Does quantum help more for circular logistics than shortest paths? | **Yes, clearly.** 0/24 on routes; 85% vs 77.5% optimal on return loads |
| Does quantum help when classical candidates are nearly tied? | Not measurable here - the triage threshold routed almost all corridors to "classically confident" |
| Does the benefit generalise to held-out instances? | **No.** 0/15 |

## 23. IBM Quantum hardware status

Connectivity was verified: `ibm_fez`, `ibm_marrakesh`, `ibm_kingston`
(156 qubits each) observed operational on the `ibm_cloud` channel.

A 5-qubit QAOA circuit with simulator-optimized parameters was **submitted to a
real backend and remained queued for the duration of this session**. No hardware
result is reported, and no simulator result has been relabelled as hardware.
Arm D of the ablation is therefore empty by necessity rather than by finding.

`Res/quantum/experiment_h_ibm_hardware.json` will record `executed: true` with
backend, job id, transpiled depth and feasible rate when the job returns, or
`executed: false` with a reason if it fails.

## 24. Production recommendation

**Ship VB-QER as the routing interface, with the quantum path disabled by
default until an artifact passes validation.**

This is not a retreat. The architecture is exactly what the brief specifies -
classical members, offline quantum artifacts, ensemble scoring, incumbent guard,
one entry point - and the quantum path is live code that engages the moment a
prior passes the gate. What the evidence does not currently support is *claiming*
a quantum contribution, and the system is built so that claim is measured rather
than asserted.

Concretely:

* **Adopt now:** the classical ensemble (2.7% objective, 63% empty-km reduction)
  and the quadratic-knapsack return-load formulation solved **classically**
  (77.5% -> 95% optimal).
* **Keep offline:** QAOA, as a research arm.
* **Do not claim:** any quantum advantage, speedup, or contribution to the live
  routing decision. There is none in the current evidence.

## 25. What would change the answer

1. **A hardware-derived artifact that passes validation.** The single biggest
   open question; blocked only on queue time.
2. **Distilling priors from the circular track rather than the route track.**
   The route track produced feasible QAOA samples on only 12 of 30 instances,
   which is a thin basis for a marginal. The circular track has a 16.4% feasible
   sampling rate and a demonstrated 85% optimal rate - a far better source.
   **This is the most promising next experiment.**
3. **A genuine warm-start study** - transferring parameters between matched
   problem families rather than the crude fixed initial angles used here.
4. **Depth sweep p in 1..8** with noise modelling.
5. **Larger option sets** in the return-load problem, where greedy degrades
   further and the formulation advantage should widen.
"""


def main() -> None:
    p = pathlib.Path("Research/QUANTUM_ROUTE_OPTIMIZATION.md")
    s = p.read_text(encoding="utf-8")
    if "# Part III - VB-QER" in s:
        print("already applied")
        return
    marker = "\n---\n\n# Part I (continued)"
    assert marker in s, "insertion marker not found"
    s = s.replace(marker, "\n" + SECTION.rstrip() + marker, 1)
    p.write_text(s, encoding="utf-8")
    print(f"updated {p} ({len(s.splitlines())} lines)")


if __name__ == "__main__":
    main()
