# VahaanBandhu — Routing Research

This directory holds the research behind **VB-QER**, the routing engine the
application uses. It documents how the routing problem is formulated, which
solvers were tried, what was measured, and — importantly — **what did not
work**.

The application never imports anything from this directory at request time. The
research produces *artifacts*; the runtime consumes only those artifacts that
passed validation.

---

## Contents

| Path | What it is |
|---|---|
| [`notebooks/route_optimization_classical_quantum.ipynb`](notebooks/route_optimization_classical_quantum.ipynb) | The main executable study: formulation, classical baselines, QUBO/QAOA, ensemble, hardware runs |
| [`notebooks/synthetic_data_generation.ipynb`](notebooks/synthetic_data_generation.ipynb) | How the dataset is generated and validated |
| [`docs/QUANTUM_ROUTE_OPTIMIZATION.md`](docs/QUANTUM_ROUTE_OPTIMIZATION.md) | The routing research report — results, ablations, negative findings |
| [`docs/ROUTE_OPTIMIZATION_DATA_SPEC.md`](docs/ROUTE_OPTIMIZATION_DATA_SPEC.md) | How one canonical dataset feeds classical, quantum and hybrid solvers identically |
| [`docs/QUANTUM_REFERENCES.md`](docs/QUANTUM_REFERENCES.md) | Papers and formulations the work builds on |
| [`docs/DATASET_METHODOLOGY.md`](docs/DATASET_METHODOLOGY.md) | Why each data-generation choice was made |
| [`docs/DATA_SOURCES.md`](docs/DATA_SOURCES.md) | Provenance, licences and acquisition status of every source |
| [`docs/data_dictionary.md`](docs/data_dictionary.md) | Column-level definitions for every table |
| [`docs/DATA_QA_REPORT.md`](docs/DATA_QA_REPORT.md) | Schema, geospatial, referential, statistical and leakage checks |

Code lives outside this directory, in [`routing/`](../routing); data in
[`Data/`](../Data) (see [`Data/README.md`](../Data/README.md)); computed
artifacts in `Res/`.

---

## The problem

Two distinct problems wear the same word "routing", and conflating them is the
main way this kind of work goes wrong.

**Shortest path.** Given a road graph, get from A to B. Solved *exactly* in
polynomial time by Dijkstra/A\*. There is no headroom here — an approximate
optimizer cannot beat an exact one, so the research does not aim at it.

**Circular return-load selection.** A truck has delivered to a mandi and is
about to drive home empty. Which return loads should it accept, given remaining
capacity, delivery windows, and the fact that two loads on the same corridor
are jointly cheaper than the sum of their separate detours? That interaction
term makes it a **quadratic knapsack** — NP-hard, with a measurably suboptimal
greedy baseline. This is where the optimization research is aimed.

---

## Code map

| Module | Role |
|---|---|
| [`routing/classical/`](../routing/classical) | Dijkstra/A\*, 2-opt, OR-Tools VRP, local search |
| [`routing/hybrid/`](../routing/hybrid) | Objective-unit costs, segment corridor, QUBO builders, hybrid optimizer |
| [`routing/quantum/`](../routing/quantum) | QUBO to Ising, QAOA, bitstring decoder, IBM Runtime (offline only) |
| [`routing/ensemble/`](../routing/ensemble) | VB-QER: members, scorer, problem-family classification, calibration, quantum priors, status |
| [`routing/evaluation/`](../routing/evaluation) | The **canonical evaluator** — every solver is scored by the same code |
| [`routing/providers/`](../routing/providers) | TomTom routing and traffic flow, with key rotation |
| [`routing/cache/`](../routing/cache) | Short-TTL operational result cache |

---

## Method — the rules that make the numbers meaningful

**One evaluator.** `routing/evaluation/metrics.py` scores every candidate from
every solver. No solver reports its own score. An early version of this work
was invalidated because classical solvers were optimizing distance while the
benchmark scored a multi-objective — the exact-solve baseline showed 2.4%
excess cost, which is impossible for an exact solver and exposed the bug.

**One cost snapshot.** Comparisons are made against frozen costs. Live traffic
changing between two runs would otherwise be indistinguishable from a solver
improvement.

**The incumbent guard.** The best feasible classical solution is always
retained. Any alternative — QUBO, QAOA, a distilled prior — replaces it only if
it is *feasible* **and** *better* under the same objective and the same cost
snapshot. An enhancement can add value or add nothing; it cannot subtract. This
turned a 50% raw-QAOA degradation rate into 0% as deployed.

**Validation gates artifacts.** A quantum-derived signal may influence the
ensemble only after passing held-out validation. To date none has.

**No quantum in the request path.** Enforced, not assumed: a test imports the
API in a clean subprocess and asserts no IBM module is present, and the backend
container does not install the IBM runtime at all.

---

## Results

### Formulation beat the solver

On the return-load benchmark, measured as the share of instances where the true
optimum was found:

| Approach | Finds true optimum |
|---|---|
| Greedy baseline | 71.7% |
| QAOA on the quadratic-knapsack QUBO | 85.0% |
| Exact classical solve of the same QUBO | **98.3%** |

The gain came from **framing the problem as a quadratic knapsack**, not from
the quantum solver. That is a real and useful result. It is not quantum
advantage and is not presented as one.

### Real IBM hardware

An identical experiment — same QUBO, QAOA depth, optimized parameters, shot
count, decoding and objective — run on three 156-qubit Heron-class systems.
Only hardware and transpilation varied.

| Source | Kind | Feasible sampling | Best energy | Decoded path | Found optimum |
|---|---|---|---|---|---|
| Classical exact | ground truth | — | 2.5 | `[0,2,3]` | — |
| Aer simulator | noiseless | 19.82% | 2.5 | `[0,2,3]` | yes |
| **ibm_marrakesh** | **real QPU** | **18.65%** | **2.5** | `[0,2,3]` | **yes** |
| **ibm_fez** | **real QPU** | **16.11%** | **2.5** | `[0,2,3]` | **yes** |
| **ibm_kingston** | **real QPU** | **12.30%** | **2.5** | `[0,2,3]` | **yes** |

All three decoded the true optimal path. Noise reduced the share of feasible
samples; the optimum survived every run. **This validates the execution and
decoding pipeline — not computational advantage.** A classical exact solve
returns the same answer in microseconds, and three devices cannot rank
hardware.

### Negative results (kept, not buried)

- **Route-track quantum enhancement: 0/24 improvements.** Shortest path is
  already exact; there was nothing to improve, exactly as predicted.
- **Distilled route priors: rejected.** Global priors 0/20, per-family 0/14,
  and 0/6 on the narrowest family. They did not generalise to held-out
  instances and the validation gate refused them — which is its purpose.
- **The transfer hypothesis is not supported.** Structure learned on one
  problem family did not carry to another.
- **A separable linear Hamiltonian was rejected.** A formulation with one qubit
  per segment and no coupling term cannot express the corridor interaction that
  makes the problem hard. Using it would have produced a quantum circuit that
  was decorative.

---

## Reproducing

```bash
pip install -r requirements.txt
```

```bash
pytest
```

```bash
jupyter lab research/notebooks
```

Hardware execution requires `IBM_QUANTUM_TOKEN` and is **offline research
only** — see [`.env.example`](../.env.example). Everything else runs from the
committed dataset with no credentials.

---

## Honest limitations

- The dataset is **synthetic** (see [`Data/README.md`](../Data/README.md)).
  Results characterise the algorithms, not Indian road logistics.
- Instances sized for current hardware are small. Nothing here says anything
  about scaling.
- Three QPUs and one experiment is not a hardware benchmark.
- No quantum advantage was observed, and none is claimed.
