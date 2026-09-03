# Quantum Route Optimization — References

**VahaanBandhu 2.0 · Phase-A**

---

## 1. Primary research paper reviewed

**QUAV: Quantum-Assisted Path Planning and Optimization for UAV Navigation with
Obstacle Avoidance**
Nouhaila Innan, Muhammad Kashif, Alberto Marchisio, Yung-Sze Gan, Frederic Barbaresco,
Muhammad Shafique.
eBRAIN Lab / Center for Quantum and Topological Systems, NYU Abu Dhabi; Thales.
arXiv:2508.21361v1 · 8 pages.

Full review: [QUANTUM_ROUTE_OPTIMIZATION.md](QUANTUM_ROUTE_OPTIMIZATION.md#1-review-of-the-quav-paper).

### What the paper actually reports

- QAOA-based UAV trajectory planning in a 2D continuous environment with polygonal
  obstacles and safety buffers.
- GPS → UTM projection via `pyproj` for metric accuracy.
- Space discretised into a grid; candidate paths enumerated; the chosen path **segmented
  into exactly 20 segments, one per qubit** (step size = total distance / 20).
- Cost Hamiltonian **H_C = Σᵢ C(eᵢ) Zᵢ**, with C(eᵢ) = −10³ for the start segment, 10⁶ for
  obstacle intersection, otherwise distance + an exponential proximity penalty
  C(eᵢ) + λ·exp(−dᵢ/d_s).
- Mixer **H_B = Σᵢ Xᵢ**; alternating layers; Adam optimizer, learning rate 0.1, 60 steps
  (20 on QPU).
- Simulation in PennyLane; hardware validation on IBM's `ibm_kyiv` (127 qubits).
- Baselines: A* (Euclidean heuristic, 0.5 m grid) and RRT (1.0 m step, 1000 iterations).
- Six scenarios; all produce collision-free paths. Hardware runs show noise-induced
  cost fluctuation before convergence.

### What the paper explicitly does *not* claim

The authors are careful, and we follow their lead: they state the objective is *"to
validate the fundamental viability of a QAOA-based planner rather than to outperform
mature classical methods"*, and that baselines serve *"without making direct claims of
superiority over classical techniques."*

### Applicability to VahaanBandhu

| Element | Verdict | Reason |
|---|---|---|
| One qubit per path **segment** rather than per (node, timestep) | **Adopted** | Scales with edges, not nodes². This is the paper's most valuable transferable idea and is the basis of `build_edge_selection_qubo`. |
| Classical preprocessing → small quantum subproblem → classical decode | **Adopted** | Matches our required hybrid architecture. |
| Segment count tied to the available qubit budget | **Adopted** | Our candidate reduction targets a fixed variable budget for the same reason. |
| Metric projection before distance math | **Adopted** | We hold WGS84 canonically and project to EPSG:32644 for metric work. |
| Explicit refusal to claim quantum advantage | **Adopted** | Our benchmark harness computes no "winner" verdict. |
| Continuous 2D free space with obstacle polygons | **Not applicable** | Trucks travel a constrained road network. There are no obstacles to avoid — the analogous quantities are road accessibility and surface risk, which are edge attributes, not geometric exclusions. |
| Grid discretisation of navigable space | **Not applicable** | We have a real road graph; discretising the plane would discard it. |
| Safety-buffer scaling factors (sₓ, s_y) | **Not applicable** | No physical clearance constraint for road vehicles. |
| **Purely linear cost Hamiltonian** | **Deliberately rejected** | See below. |

### The critique that changed our design

QUAV's cost Hamiltonian, **H_C = Σᵢ C(eᵢ) Zᵢ**, contains only single-qubit Z terms. Such a
Hamiltonian is **separable**: its ground state factorises, each qubit's optimal value can
be determined independently by inspecting the sign of C(eᵢ), and no entanglement is
required to find it. QAOA on a separable Hamiltonian cannot outperform reading off n
signs.

The paper does describe applying "CNOT — Rz(2γ) — CNOT" sequences between consecutive
qubits to preserve path continuity, which would introduce ZZ coupling — but the stated
Hamiltonian does not contain the corresponding quadratic terms, so the formulation as
written and the circuit as described are not consistent.

**Our response:** the VahaanBandhu edge-selection QUBO adds squared flow-conservation
residuals at every node, which produce genuine ZᵢZⱼ couplings. We verify by test
(`test_has_genuine_quadratic_coupling`, `test_circuit_contains_entangling_gates`) that
the resulting circuit actually entangles — otherwise running QAOA would be decorative.

---

## 2. Reference repositories reviewed

Both repositories named in the Phase-A brief were reviewed for architecture and
formulation. **No code was copied.**

### `armulrich/Qpath_optimizer`
<https://github.com/armulrich/Qpath_optimizer>

### `anityu45/quantum-route-optimiser`
<https://github.com/anityu45/quantum-route-optimiser>

**Status note (honest):** these repositories were reviewed only at the level of their
general approach as described in the Phase-A brief and the broader QAOA-for-routing
literature. A line-by-line audit of their current contents was **not** performed in
Phase-A, and no claim is made here about their specific implementation details. The
architectural decisions in this project are traceable to the QUAV paper and to the
standard QUBO/QAOA formulations cited below, not to these repositories.

---

## 3. Formulation and algorithm references

- **Lucas, A.** (2014). *Ising formulations of many NP problems.* Frontiers in Physics 2:5.
  — The canonical source for the permutation-encoded TSP QUBO used in
  `build_tsp_qubo`, and for the penalty-weight requirement that a constraint violation
  must never be cheaper than compliance.

- **Farhi, E., Goldstone, J., Gutmann, S.** (2014). *A Quantum Approximate Optimization
  Algorithm.* arXiv:1411.4028.
  — The alternating-operator ansatz implemented in `routing/quantum/qaoa.py`.

- **Glover, F., Kochenberger, G., Du, Y.** (2019). *A Tutorial on Formulating and Using
  QUBO Models.* arXiv:1811.11538.
  — Penalty-method construction and the QUBO ↔ Ising transformation
  (x = (1 − z)/2) verified exactly in `test_ising_energies_match_qubo_energies`.

- **Hart, P. E., Nilsson, N. J., Raphael, B.** (1968). *A Formal Basis for the Heuristic
  Determination of Minimum Cost Paths.* IEEE Trans. SSC 4(2).
  — A*; the admissibility requirement that made haversine (never a scaled variant) the
  correct heuristic over road distance.

- **Yen, J. Y.** (1971). *Finding the K Shortest Loopless Paths in a Network.*
  Management Science 17(11).
  — k-shortest-paths candidate generation (`nx.shortest_simple_paths`).

- **Dantzig, G. B., Ramser, J. H.** (1959). *The Truck Dispatching Problem.*
  Management Science 6(1).
  — Origin of the VRP family.

- **Toth, P., Vigo, D.** (2014). *Vehicle Routing: Problems, Methods, and Applications.*
  2nd ed., SIAM.
  — CVRP / VRPTW / pickup-and-delivery formulations underlying `problem_type`.

---

## 4. Software

| Tool | Version | Use |
|---|---|---|
| Qiskit | 1.3.1 | Circuit construction, transpilation |
| Qiskit Aer | 0.15.1 | Statevector simulation |
| qiskit-ibm-runtime | 0.34.0 | IBM Quantum hardware access (`SamplerV2`) |
| qiskit-optimization | 0.6.1 | Reference QUBO utilities |
| Google OR-Tools | 9.11.4210 | CVRP / VRPTW solving |
| NetworkX | 3.4.2 | Road graph, Dijkstra, A*, k-shortest paths |
| SciPy | 1.18.1 | COBYLA classical optimizer in the QAOA loop |
| GeoPandas / Shapely / pyproj | 1.0.1 / 2.0.6 / 3.7.0 | Geospatial handling and projection |
| OSMnx | 2.0.1 | OSM road-network ingestion (integration path; unused in `v0.1`) |
| Pandera | 0.22.1 | Dataset schema validation |

## 5. Hardware

IBM Quantum Platform, `ibm_cloud` channel. Backends observed operational during Phase-A:
`ibm_fez` (156 qubits), `ibm_marrakesh` (156), `ibm_kingston` (156).

Execution status and job identifiers for the actual hardware run are recorded in
`Res/quantum/experiment_h_ibm_hardware.json` and in
[QUANTUM_ROUTE_OPTIMIZATION.md](QUANTUM_ROUTE_OPTIMIZATION.md).

## 6. Data sources

See [DATA_SOURCES.md](DATA_SOURCES.md) for full provenance, licensing posture and the
record of sources that were **not** acquired.
