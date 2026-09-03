# Quantum-Enhanced Route Optimization

**VahaanBandhu 2.0 · Phase-A research report**

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

**Phase-A answer: no improvement observed.** Details in §6. What Phase-A does establish
is a correct, validated encode → solve → decode pipeline and an honest benchmark
apparatus, which is the prerequisite for the question ever being answerable.

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

## 7. IBM Quantum hardware (Experiment H)

IBM Quantum connectivity was **verified** during Phase-A on the `ibm_cloud` channel, with
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
compromise; on the Phase-A evidence it would be worse on every axis — latency (queue
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

**Phase-B, in priority order:**

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
