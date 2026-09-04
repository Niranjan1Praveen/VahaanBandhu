# Quantum-Enhanced Route Optimization

**VahaanBandhu · the routing research report**

Executable companion: [`route_optimization_classical_quantum.ipynb`](route_optimization_classical_quantum.ipynb)
References: [QUANTUM_REFERENCES.md](QUANTUM_REFERENCES.md)

---

## 0. Research objective

> **Can quantum or hybrid quantum-classical optimization improve candidate-route
> selection or constrained circular-logistics optimization, after the classical road
> network has already reduced the search space?**

The qualifier is the whole question. Nobody can encode the Delhi NCR + Haryana + Punjab
+ Uttar Pradesh road graph onto quantum hardware, and no amount of tuning will change
that. What is potentially tractable is the small discrete choice that remains once
classical routing has produced a handful of sensible corridors.

**the routing research answer (component level): standalone QAOA showed no improvement.** This is a finding about one VB-QER component, not about the architecture. Details in §6. What the routing research does establish
is a correct, validated encode → solve → decode pipeline and an honest benchmark
apparatus, which is the prerequisite for the question ever being answerable.


---

## 0a. PROJECT INVARIANT - VB-QER is the final algorithm

**VB-QER (VahaanBandhu Quantum-Enhanced Routing Ensemble) is VahaanBandhu's final
routing algorithm. Its architecture is FIXED and is not under evaluation.**

```
                         VB-QER
                           |
        +------------------+------------------+
        |                  |                  |
        v                  v                  v
   CLASSICAL          QUANTUM /          LOGISTICS
   ENSEMBLE             QUBO              OPTIMIZERS
        |                  |                  |
        +------------------+------------------+
                           v
                 ENSEMBLE DECISION
                           v
                FEASIBILITY VALIDATION
                           v
                  INCUMBENT GUARD
                           v
                      FINAL ROUTE
```

Dijkstra, A*, OR-Tools, 2-opt, simulated annealing, classical QUBO and standalone
QAOA are **components, baselines or research arms inside VB-QER**. None of them
is an alternative to it. The application entry point is always:

```python
solution = VBQEROptimizer().solve(instance)
```

never a conditional such as `if quantum_available: ... else: use_classical()`.

### Architecture status vs component status

These are reported separately from here on, because conflating them produced an
incorrect recommendation in an earlier revision of this document.

| Item | Status |
|---|---|
| **Final algorithm: VB-QER** | **FIXED** |
| Classical ensemble | ACTIVE |
| Circular-logistics QUBO formulation | ACTIVE |
| Objective-alignment layer | ACTIVE |
| Incumbent guard | ACTIVE |
| QAOA simulator research | ACTIVE OFFLINE |
| IBM Quantum hardware | OFFLINE ONLY |
| Quantum-derived production artifacts | VALIDATION-GATED |

The last row may move between EXPERIMENTAL / VALIDATED / ACTIVE / REJECTED /
STALE **without changing the identity of the final algorithm**. A component
failing validation means that component is not deployed; it does not mean the
ensemble should be replaced by one of its own members.

Machine-readable equivalent: `routing/ensemble/status.py`.

### Correction notice

An earlier revision of this report recommended "ship the return-load formulation
solved classically" in language that implied choosing classical routing *instead
of* VB-QER. That framing was wrong. The classical ensemble and the circular QUBO
are VB-QER components, and both are ACTIVE. The correct statement is: **ship
VB-QER, in which the classical members and the circular QUBO are active and the
quantum-derived artifacts remain validation-gated.**

The experimental results themselves are unchanged and are not restated
favourably: the route-track QAOA prior failed held-out validation (0/15) and is
REJECTED. See Part III.
---

## 1. Review of the QUAV paper

Innan et al., *QUAV: Quantum-Assisted Path Planning and Optimization for UAV Navigation
with Obstacle Avoidance* (arXiv:2508.21361v1).

### 1.1 Problem formulation used by the paper

A drone navigates a 2D continuous environment E ⊆ ℝ² containing obstacle polygons
{Ωᵢ}. GPS coordinates are projected to UTM (Zone 49) with `pyproj`; each obstacle is
buffered by scaling factors (sₓ, s_y) > 1 to enforce a safety margin. The navigable space
is discretised into a grid of resolution r, a graph G = (V, E) is built over waypoints,
and candidate paths from P_start to P_end are enumerated.

The chosen path is then **segmented**: total distance D is divided by the qubit budget
(20), giving step size Δs, and the path is walked from P_start to P_end emitting one edge
per step.

### 1.2 Cost function

Each segment receives:

```
C(eᵢ) = −10³              if eᵢ is the start segment      (anchoring bias)
        10⁶               if eᵢ intersects an obstacle    (hard rejection)
        C_dist(eᵢ) + C_obs(eᵢ)   otherwise
```

with a proximity penalty `C(eᵢ) += λ · exp(−dᵢ/d_s)` where dᵢ is the distance to the
nearest obstacle and d_s the safety margin (5 m in the experiments).

### 1.3 Quantum method

- **Encoding:** one qubit per path segment. 20 qubits, 20 segments.
- **Initialisation:** |ψ₀⟩ = ⊗ H|0⟩ — equal superposition.
- **Cost Hamiltonian:** H_C = Σᵢ C(eᵢ) Zᵢ, applied as U_C(γ) = e^(−iγH_C).
- **Mixer:** H_B = Σᵢ Xᵢ, applied as Rx(2β) per qubit, U_B(β) = e^(−iβH_B).
- **Ansatz:** |ψ(γ,β)⟩ = Π_{p=1..k} U_B(β_p) U_C(γ_p) |ψ₀⟩.
- **Classical optimizer:** Adam, learning rate 0.1, 60 steps (20 allocated to QPU).
- **Simulation:** PennyLane. **Hardware:** IBM `ibm_kyiv` (127 qubits).

### 1.4 Experimental setup and reported results

Six start/end scenarios of varying complexity. Baselines A* (Euclidean heuristic, 0.5 m
grid, smoothing 0.2) and RRT (step 1.0 m, 1000 iterations, goal bias 0.05).

Reported: loss drops sharply over the first 5–10 optimization steps, stabilises between
steps 10–40, and converges around step 50. **All six scenarios produce collision-free
paths.** Some paths exhibit zigzag patterns, attributed to QAOA's probabilistic sampling
across near-degenerate solutions. Hardware runs show noise-induced fluctuation —
a spike near step 3 — before converging with residual noise. The authors note that
limited QPU connectivity forces SWAP insertion, raising error rates.

### 1.5 Limitations the paper acknowledges

NISQ noise, decoherence and readout error; connectivity constraints requiring careful
transpilation; and — stated plainly by the authors — that the work validates *viability*,
not superiority: baselines are included *"without making direct claims of superiority
over classical techniques."*

### 1.6 Critique: the cost Hamiltonian is separable

This is the finding that changed our design.

**H_C = Σᵢ C(eᵢ) Zᵢ contains only single-qubit terms.** A Hamiltonian with no ZᵢZⱼ
coupling is separable: its ground state is a product state, each qubit's optimal value is
determined independently by the sign of C(eᵢ), and the global optimum can be written down
in O(n) by inspection. QAOA on such a Hamiltonian is guaranteed to find the optimum, and
equally guaranteed to be pointless — no entanglement is needed, so there is no quantum
computation being exploited.

The paper's §IV *does* describe applying CNOT — Rz(2γ) — CNOT sequences between
consecutive qubits *"to ensure that dependencies between connected path segments are
accounted for, preserving path continuity"*, which would introduce ZZ coupling. But the
stated H_C contains no corresponding quadratic terms. The formulation as written and the
circuit as described are therefore inconsistent, and the paper does not resolve which is
authoritative.

Separately, the encoding gives each segment an independent on/off variable with no
structural guarantee that the selected segments form a connected path — continuity is
encouraged by the start-segment bias and the circuit structure rather than enforced.

**Consequence for our design:** we enforce connectivity explicitly, through squared
flow-conservation residuals, which produce genuine quadratic couplings. See §3.2.

### 1.7 What we took, and what we did not

Adopted: one qubit per **edge/segment** rather than per (node, timestep); the
classical-preprocess → small-quantum-subproblem → classical-decode architecture; sizing
the subproblem to the qubit budget; metric projection before distance math; and the
authors' scientific restraint about advantage claims.

Not applicable: continuous-space obstacle avoidance, grid discretisation of the plane,
and safety-buffer geometry. Trucks travel a constrained road network; the analogous
quantities (accessibility, surface risk) are edge attributes, not geometric exclusions.

Rejected: the purely linear cost Hamiltonian.

---

## 2. Classical baselines

Strong classical baselines come first, because a quantum result is only interesting
relative to what classical methods already achieve on the identical instance.

| Algorithm | Module | Role |
|---|---|---|
| Dijkstra | `routing/classical/shortest_path.py` | Shortest-path reference |
| A* | same | Same optimum, fewer expansions. Heuristic is **haversine**, which is admissible because road distance ≥ great-circle distance. Scaling it to "tighten" the search would silently break optimality. |
| k-shortest paths (Yen) | same | Generates genuinely distinct corridors for the selection layer |
| Brute-force TSP | `routing/classical/heuristics.py` | **Ground truth** for ≤9 nodes. Exists specifically so quantum results can be reported as a real optimality gap rather than "matched a heuristic". Refuses larger inputs instead of hanging. |
| Nearest neighbour | same | Fast greedy construction |
| 2-opt | same | Local search. Re-evaluates the full tour rather than using the symmetric delta shortcut, because our distance matrix is **asymmetric**. |
| Simulated annealing | same | Metaheuristic, seeded and reproducible |
| OR-Tools routing | `routing/classical/vrp.py` | CVRP / VRPTW with capacity and time-window dimensions. Distances scaled km→metres and minutes→seconds before integerisation, so rounding never produces a "better than optimal" tour. |

---

## 3. Quantum formulation

### 3.1 Permutation-encoded TSP

Binary x_{i,t} = 1 iff node i is visited at position t:

```
min  Σ_t Σ_{i≠j} D_ij · x_{i,t} · x_{j,t+1}
   + A · Σ_i ( Σ_t x_{i,t} − 1 )²          each node visited exactly once
   + A · Σ_t ( Σ_i x_{i,t} − 1 )²          each position filled exactly once
```

A is set above the largest achievable tour cost (`A = n·max(D) + 1`), so no constraint
violation can ever pay for itself.

**This encoding needs n² qubits, and that is decisive:**

| Nodes | Qubits | Statevector amplitudes |
|---|---|---|
| 3 | 9 | 512 |
| 4 | 16 | 65,536 |
| 5 | 25 | 3.4 × 10⁷ |
| 6 | 36 | 6.9 × 10¹⁰ |
| 7 | 49 | 5.6 × 10¹⁴ |

Our simulator budget is 22 qubits (~4M amplitudes). A 7-node instance requires 2⁴⁹
amplitudes — roughly 8 exabytes. We measured this the hard way: an early benchmark run
failed with *"Required memory: 8589934592M"*, which is why `QUANTUM_NODE_CEILING` is 3
customers and why the benchmark harness now records `NOT ENCODABLE` explicitly rather
than skipping silently.

### 3.2 Edge-selection encoding (the one that matters)

One binary variable y_e per candidate edge:

```
min  Σ_e c_e · y_e
   + A · Σ_{v∈V} ( Σ_{e ∈ δ⁺(v)} y_e − Σ_{e ∈ δ⁻(v)} y_e − b_v )²
```

with b_v = +1 at the source, −1 at the sink, 0 elsewhere.

Two properties this buys us:

1. **It scales with edges, not nodes².** A 20-edge corridor problem is 20 qubits
   regardless of how large the underlying road network is. After classical candidate
   reduction, this is the formulation with a plausible path to useful scale.

2. **It has genuine quadratic structure.** Expanding the squared residual gives
   cross terms 2A·c_i·c_j·y_i·y_j — real ZᵢZⱼ couplings. This is precisely what the QUAV
   Hamiltonian lacks, and it is what makes running QAOA here a meaningful act rather than
   a decorative one.

### 3.3 QUBO → Ising

Substituting x = (1 − z)/2 yields (h, J, offset) with J strictly upper-triangular. The
conversion is verified **exactly** over all 2ⁿ states in
`test_ising_energies_match_qubo_energies` (max error < 1e-9).

### 3.4 QAOA circuit

Standard alternating-operator ansatz: Hadamard initialisation; per layer, Rz(2γh_i) for
single-qubit terms and CNOT — Rz(2γJ_ij) — CNOT for couplings; then Rx(2β) mixer.
Classical optimizer COBYLA (SciPy). Warm-start parameters accepted via `initial_params` —
this is the mechanism by which an offline hardware run can pay off online.

---

## 4. Mandatory classical validation

**A QUBO that does not encode the routing problem can still produce a beautifully
converging QAOA run — of the wrong problem.** Three properties are proven by exhaustive
enumeration before any quantum execution.

On the validation graph (0→{1,2}→3 plus an expensive direct 0→3 link; true cheapest path
0→2→3 costing 2.5):

| Check | Result |
|---|---|
| Brute-force QUBO optimum decodes to a valid route | **PASS** — decodes to `[0,2,3]` |
| Optimum energy equals the true path cost | **PASS** — 2.500 exactly, no penalty residue |
| Worst feasible energy < best infeasible energy | **PASS** — penalty separation holds over all 2⁵ states |
| Non-zero ZZ coupling terms present | **PASS** — 8 quadratic terms |
| Circuit contains CNOTs | **PASS** |
| Ising conversion energy-exact | **PASS** — max error < 1e-9 |

The permutation encoding is validated the same way against `brute_force_tsp`, on a
4-node instance where the QUBO optimum reproduces the exact optimal tour.

---

## 5. Hybrid architecture

```
full road graph  (10^5-10^6 edges)
      |  k-shortest paths                      classical, milliseconds
      v
candidate corridors  (4-10 paths)
      |  Pareto dominance filtering            classical, discards nothing reachable
      v
non-dominated candidates  (2-8)
      |  QUBO encoding
      v
reduced problem  (5-25 binary variables)       QAOA-scale
      |  simulator / hardware
      v
measured bitstrings
      |  decode + feasibility check            classical
      v
validated route
```

Pareto filtering is the honest step: a candidate that is longer, slower, costlier **and**
riskier than another cannot win under any non-negative weighting, so removing it discards
no reachable optimum. When dominance alone does not reach the variable budget, further
truncation is applied — and flagged in `reduction_stats` as
`truncation_may_discard_optimum`, because it can.

---

## 6. Experimental results

### 6.1 Setup

8 quantum-ready instances from `route_instances.csv`, all sharing one
`cost_snapshot_id`. The benchmark harness **refuses** to compare across differing cost
snapshots. QAOA at p=2, 1024 shots, seed 11.

### 6.2 Results

| Algorithm | Mean optimality gap | Feasible runs | Mean sampling feasible rate |
|---|---|---|---|
| `brute_force_exact` | 0.00% (ground truth) | 8/8 | — |
| `nearest_neighbour+2opt` | 0.00% | 8/8 | — |
| `simulated_annealing` | 0.00% | 8/8 | — |
| `qubo_brute_force` | 0.00% | 8/8 | — |
| `nearest_neighbour` | 1.56% | 8/8 | — |
| **`qaoa_p2_simulator`** | **16.0%** | **3/8** | **0.061%** |

Runtime is reported decomposed — classical preprocess, solver, quantum execution,
postprocess — and never totalled into a single comparable figure.

### 6.3 What these numbers support

1. **The encoding pipeline is correct.** On the smallest problems QAOA reaches the exact
   optimum (gap 0.0). The mathematics is sound.

2. **QAOA at p=2 substantially underperforms classical solvers here.** It returns a
   feasible solution in 3 of 8 runs with a 16% mean gap, while nearest-neighbour+2-opt
   solves the same instances optimally in under 0.05 ms.

3. **The 0.061% feasible sampling rate is the headline caveat.** Roughly 6 shots in
   10,000 satisfy the constraints. Reporting only the best sample without this figure
   would badly misrepresent the method.

4. **The binding constraint is encoding cost, not tuning.** More layers and more shots
   would improve quality at these sizes, but nothing changes n² qubit scaling.

### 6.4 What is explicitly not claimed

- **No speedup.** A noiseless simulator's wall-clock time is not comparable to a
  classical solver's; it includes circuit construction, transpilation and many circuit
  executions inside a variational loop, on classical hardware.
- **No better routes.** Classical methods matched or beat QAOA on every instance.
- **No exponential anything.**
- **No claim that this generalises.** Eight small synthetic instances.

---

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
safety net rather than a competitor. Both halves live inside VB-QER; this is a
question about one component's contribution, not about which algorithm to ship.

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

**Within VB-QER**, activate the quadratic-knapsack return-load formulation with
the **exact classical solver** as its current backend, and keep QAOA as an
offline research arm feeding the same formulation.

This is a component-level decision, not an architecture-level one. The QUBO
formulation is a VB-QER component either way; only the solver behind it changes,
and the architecture supports swapping that solver without touching anything
else. When QAOA or hardware improves, the backend flips and no interface moves.


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

## 23. IBM Quantum hardware status -- COMPLETED

**Real hardware execution is now complete on three QPUs.** The earlier
"still queued" status is superseded.

The controlled H1 validation -- identical QUBO, QAOA depth p=1, simulator-
optimized parameters, 1024 shots, identical decoding and objective -- was run on
three 156-qubit IBM Heron-class systems. Only hardware and transpilation varied.

| Source | Kind | Job id | Feasible rate | Best E | Decoded path | Matched optimum |
|---|---|---|---|---|---|---|
| classical exact | ground truth | — | — | 2.5 | `[0,2,3]` | — |
| Aer simulator | noiseless sim | — | 19.82% | 2.5 | `[0,2,3]` | yes |
| **ibm_marrakesh** | **REAL QPU** | `dacmbvbdd5gc73d69bag` | **18.65%** | **2.5** | `[0,2,3]` | **yes** |
| **ibm_fez** | **REAL QPU** | `dacmbq5nj4cs73acr6lg` | **16.11%** | **2.5** | `[0,2,3]` | **yes** |
| **ibm_kingston** | **REAL QPU** | `dacft8l1ierc738ji9a0` | **12.30%** | **2.5** | `[0,2,3]` | **yes** |

Kingston queued roughly eight hours behind 76 pending jobs; Fez and Marrakesh
had empty queues at submission and returned in minutes. That is a scheduling
observation, not a device-quality one.

### Conclusion, stated precisely

> Real IBM Quantum hardware execution has now been completed on three 156-qubit
> IBM Heron-class systems for the controlled VahaanBandhu hardware validation.
> All three produced feasible samples containing the classical ground-state
> solution. This validates the hardware execution and decoding pipeline. **It
> does not demonstrate quantum advantage.**

A classical exact solve returns the same optimum in microseconds. What the data
shows is expected degradation in *feasible sampling rate* under hardware noise
(19.82% noiseless → 18.65% / 16.11% / 12.30%), with solution quality unaffected
at this circuit size. Three devices is far too small a sample to rank hardware.

Artifacts: `Res/quantum/H1_ibm_{fez,marrakesh,kingston}_result.json`,
`Res/quantum/H1_cross_hardware_comparison.json`, and the ownership-scoped
registry `Res/quantum/hardware_job_registry.json`.

**Totals (VahaanBandhu-owned jobs only):** 3 submitted, 3 completed, 0 queued,
0 failed, 3 analysed. The IBM account also holds 11 older DONE jobs from
unrelated prior work; those are excluded from every total.

Arm D of the ablation (hardware-derived quantum features) remains empty: these
runs validate the pipeline but have not yet been distilled into an artifact that
passes held-out validation.

## 24. Production recommendation

**Ship VB-QER.** That is the fixed architecture and it is not in question here.
What this section reports is the *current status of VB-QER's components*.

| VB-QER component | Status | Contribution measured |
|---|---|---|
| Classical ensemble | **ACTIVE** | +2.7% objective, -63% empty km vs the best single member |
| Circular-logistics QUBO | **ACTIVE** (exact backend) | 77.5% -> 95.0% optimal |
| Objective-alignment layer | **ACTIVE** | corrected a 2.4% systematic excess |
| Incumbent guard | **ACTIVE** | 50% raw degradation -> 0% deployed |
| QAOA research arm | **ACTIVE OFFLINE** | 85.0% optimal; not yet a deployable artifact |
| Route-track quantum prior | **REJECTED** | failed held-out validation, 0/15 |
| Circular-track quantum artifacts | **VALIDATION-GATED** | under active investigation |

The quantum path is live code inside VB-QER that engages the moment an artifact
passes the gate. The classical ensemble and the circular QUBO are VB-QER
components, not alternatives to it -- activating them *is* shipping VB-QER.

**Do not claim:** any quantum advantage, speedup, or contribution to the live
routing decision. There is none in the current evidence.

## 25. Improving the quantum contribution inside VB-QER

The question is not whether to use VB-QER. It is how to raise the quantum
component's contribution within it. In priority order:

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

---

# Part IV - Improving the Quantum Component Inside VB-QER

Experiment `vbqer_circular_v1` / `vbqer_circular_artifacts_v1`.

Framing per the project invariant: this asks **how to raise the quantum
contribution within VB-QER**, not whether to use VB-QER. Every arm is a VB-QER
configuration.

## 26. Scope decision: shortest path is out

Dijkstra and A* solve shortest path exactly in polynomial time. No optimizer,
quantum or otherwise, can improve on an exact polynomial algorithm, so those
members stay inside VB-QER unchanged and receive no further quantum research
effort. `routing/ensemble/problem_family.py` encodes this: a shortest-path
classification disables the QUBO and artifact layers outright.

Effort is concentrated on return-load selection, a quadratic knapsack with
measured greedy suboptimality.

## 27. VB-QER circular components, measured on 60 held-out problems

| VB-QER circular component | Optimal rate | Mean gap vs exact |
|---|---|---|
| Greedy value-density | 71.7% | 32.57 |
| **Greedy + local search** | **85.0%** | **18.05** |
| **Classical QUBO (exact backend)** | **98.3%** | **0.88** |

All three are components inside VB-QER. The QUBO is the primary circular
optimizer; local search is the fallback where the exact solve is not tractable.

**Local search was discovered by accident, as the honesty control.** It was added
purely so quantum artifacts could be validated against something other than
greedy. It turned out to be a materially better classical component (+14.52
objective units over greedy) and is now ACTIVE. The experiment improved VB-QER --
just not via quantum.

## 28. Artifact distillation and the transfer hypothesis

The route-track prior failed (0/15). Two candidate explanations were tested.

**Hypothesis:** quantum-derived information may transfer within *matched*
optimization families even when a global prior does not generalise.

### Methodology: the control that decides the experiment

Artifacts are validated against an **unguided local-search control**, never
against greedy. Validating against greedy would credit the artifact for whatever
plain local search finds on its own -- the standard way to manufacture a quantum
result that is really just a better classical baseline.

Artifacts are keyed on value-density **rank**, not option id, since ids are
instance-specific and could not transfer to any unseen problem.

### Result: NOT SUPPORTED

| Artifact | Held-out | Improved | Degraded | Mean delta | Deployable | Control gain over greedy |
|---|---|---|---|---|---|---|
| Global | 20 | **0** | 0 | 0.0 | **NO** | 38.73 |
| `D_shared_corridor_synergy` | 14 | **0** | 0 | 0.0 | **NO** | 33.40 |
| `C_high_detour` | 6 | **0** | 0 | 0.0 | **NO** | 51.18 |

All three failed independently. Two explanations are ruled out:

* **Not a data-volume problem.** The circular track produced feasible QAOA
  samples on **30/30** problems, against the route track's 12/30. More and better
  signal did not help.
* **Not a family-mismatch problem.** Matching on structural family -- the specific
  fix this experiment existed to test -- changed nothing.

The `control gain over greedy` column is the important one: the unguided control
gains 33-51 objective units. That improvement is real and entirely classical.

## 29. QAOA depth sweep

Six problems, 5 options each (11 qubits), p in {1,2,3,4,6,8}, 1024 shots.

| p | Optimal rate | Mean gap | Feasible sampling | Circuit depth | Runtime |
|---|---|---|---|---|---|
| 1 | 66.7% | 79.86 | 23.7% | 61 | 1478 ms |
| 2 | 50.0% | 101.44 | 23.2% | 120 | 2873 ms |
| 3 | 83.3% | 42.04 | 24.8% | 179 | 4911 ms |
| **4** | **100%** | **0.00** | 24.6% | 238 | 5676 ms |
| 6 | 66.7% | 52.36 | 24.1% | 356 | 7692 ms |
| **8** | **100%** | **0.00** | 25.8% | 474 | 9289 ms |

Greedy on the same problems: 83.3% optimal.

**Read this cautiously.** QAOA at p=4 and p=8 did reach 100% optimal, above
greedy's 83.3%. But the sequence is **non-monotonic** -- p=2 is worse than p=1,
p=6 worse than p=4 -- which is characteristic of COBYLA settling in different
basins of the variational landscape rather than of a depth trend. On six
problems this is optimizer variance, not evidence that depth helps. A depth
conclusion needs a far larger sample with multiple restarts per depth.

Note also that the exact QUBO solve reaches 98.3% optimal in ~70 ms. QAOA
matching the optimum at p=8 in 9.3 seconds confirms the encoding is correct; it
is not an advantage.

## 30. Where the remaining room actually is

The exact QUBO backend reaches **98.3%** optimal at current problem sizes, so
there is roughly **1.7% headroom left for any optimizer** in this regime. A
quantum contribution cannot come from here.

It would have to come from problem sizes where the exact solve stops being
tractable: `n_options` beyond ~16, where the QUBO exceeds the 22-qubit
statevector budget and exhaustive selection becomes expensive. **That is a
scaling question, not a tuning question**, and it is the next thing worth
attacking.

## 31. Component status after Part IV

| VB-QER component | Status | Change in Part IV |
|---|---|---|
| Classical ensemble | ACTIVE | unchanged |
| Circular QUBO (exact backend) | ACTIVE | confirmed primary, 98.3% optimal |
| **Circular local search** | **ACTIVE** | **newly promoted**, 85.0% optimal |
| Objective-alignment layer | ACTIVE | unchanged |
| Incumbent guard | ACTIVE | 0% deployed degradation maintained |
| QAOA simulator research | ACTIVE OFFLINE | depth sweep added |
| IBM Quantum hardware | OFFLINE ONLY | job still queued |
| Route-track prior | REJECTED | unchanged |
| **Global circular prior** | **REJECTED** | new, 0/20 |
| **Per-family circular priors** | **REJECTED** | new, 0/14 and 0/6 |
| Artifact slot | VALIDATION-GATED | still open; nothing has passed |

**The architecture is unchanged and was not under evaluation.** VB-QER remains
the final algorithm; this experiment moved component statuses and added one new
active component.
---

# Part I (continued)

## 7. IBM Quantum hardware (Experiment H)

IBM Quantum connectivity was **verified** during the routing research on the `ibm_cloud` channel, with
`ibm_fez`, `ibm_marrakesh` and `ibm_kingston` (156 qubits each) observed operational.

Execution protocol, and its honest limitation: QAOA parameters are optimized on a
**noiseless simulator** and then transferred to hardware for a single sampling run.
Running the full variational loop on a QPU would consume enormous queue time for no
scientific gain at this scale. This means the hardware result measures **how a
simulator-optimized circuit behaves under real device noise**, not hardware-native
optimization — and it is recorded as such in the artifact's `parameters_source` field.

Execution status, backend, job id, transpiled depth and feasibility rate are recorded in
`Res/quantum/experiment_h_ibm_hardware.json`. Where hardware could not be reached, the
artifact records `executed: false` with a reason. **No simulator result is ever relabelled
as hardware.**

---

## 8. Production recommendation

**Do not call quantum hardware in the live request path.** This is not a resource-limit
compromise; on the the routing research evidence it would be worse on every axis — latency (queue
times in minutes to hours), reliability (37% of runs returned nothing feasible), and
solution quality (16% gap).

The architecture is therefore:

```
OFFLINE (research / benchmarking)
  canonical instances -> classical baselines -> QUBO -> simulator
    -> selected hardware runs -> benchmarks, learned parameters, route priors
                                              |
                                              |  artifacts only, never a live call
                                              v
LIVE (production)
  user request -> TomTom candidates -> normalize -> candidate reduction
    -> fast classical scoring (+ optional stored prior) -> constraint check
    -> best route + explanation -> UI
```

Stored priors may adjust the circular-logistics term within a bounded range (±0.25), so a
stale artifact can shade a decision but never override live cost data. **The live system
remains fully functional with no quantum backend of any kind**, and is tested that way.

A note on integrity: a lookup table is not "quantum AI". An artifact may only be
described as quantum-derived where quantum computation materially contributed to
producing it, and every artifact in `Res/` records the algorithm family that created it.

---

## 9. Limitations

1. **Small scale.** 8 instances, ≤4 nodes each. No claim generalises beyond this.
2. **Synthetic costs.** `route_edges` uses an offline detour model, not measured routing.
   Real TomTom cost matrices could change relative solver performance.
3. **Fixed p=2.** No systematic depth sweep was performed.
4. **Simulator is noiseless.** Aer without a noise model is optimistic relative to hardware.
5. **Parameter transfer, not hardware-native optimization** (§7).
6. **The one-hot candidate-selection QUBO is classically trivial.** Selecting the minimum
   of n numbers is O(n). It is retained as a pipeline validation vehicle and labelled as
   such in `build_one_hot_qubo`; it is not evidence of anything.
7. **No noise mitigation.** No zero-noise extrapolation or readout-error correction.

---

## 10. Future work

**the application, in priority order:**

1. Move the primary quantum track fully onto the **edge-selection encoding** over
   reduced candidate corridors — the only formulation with plausible scaling.
2. Formulate **return-load matching** as a QUBO. It is a bipartite assignment problem
   with capacity and detour constraints, which is a genuinely quadratic, genuinely
   VahaanBandhu-specific problem — a better fit for QUBO than TSP.
3. Depth sweep p ∈ {1..8} with warm-starting, measuring the feasible-rate/depth trade-off.
4. Noise-model simulation before further hardware runs, plus readout-error mitigation.
5. Test whether learned (γ, β) parameters genuinely transfer across instances in the same
   problem family — this is the entire premise of offline-to-online artifact reuse and is
   currently **assumed, not demonstrated**.
6. Rebuild cost matrices from measured TomTom routing once storage terms are verified, and
   re-run the full benchmark against real road costs.
