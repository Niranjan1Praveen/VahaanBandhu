# Route Optimization Data Specification

**VahaanBandhu 2.0 · Phase-A**

How the same canonical data feeds classical, quantum and hybrid solvers — and what makes
their results comparable.

---

## 1. The comparability contract

> **Two solver results are comparable if and only if they carry the same
> `instance_id` AND the same `cost_snapshot_id`.**

Everything in this document exists to make that statement enforceable rather than
aspirational.

`cost_snapshot_id` = `content_id("cost_snapshot", scenario_id, dataset_version, graph_version)`.
It identifies the exact cost matrix a result was computed against. Comparing an OR-Tools
run on baseline costs against a QAOA run on evening-peak costs, and presenting them as
equivalent, would be meaningless — so `benchmark_instance` **raises** rather than
comparing across snapshots.

### The single entry point

`routing.instances.load_instance(instance_id)` is the **only** sanctioned way to
materialise a problem. Nothing else in the codebase may construct a `RoutingInstance` or
build its own distance matrix. If a solver derived its own distances, the contract would
be silently void.

---

## 2. The canonical instance

```python
@dataclass
class RoutingInstance:
    instance_id: str
    problem_type: str              # TSP | CVRP | VRPTW | PDP | CIRCULAR_VRP
    depot_index: int               # always 0
    node_ids: list[str]            # location_ids; node 0 is the depot
    coords: np.ndarray             # (n, 2) WGS84 lat/lon
    distance_matrix: np.ndarray    # (n, n) km, DIRECTED
    time_matrix: np.ndarray        # (n, n) minutes, DIRECTED
    demands: np.ndarray            # (n,) kg; demands[depot] == 0
    vehicle_capacities: list[float]
    time_windows: list[tuple] | None   # minutes from midnight
    objective_weights: dict[str, float]
    cost_snapshot_id: str          # THE comparability key
    scenario_id: str
    dataset_version: str
    graph_version: str
```

`validate()` enforces: square matrices matching `n`, zero diagonal, zero depot demand,
and demand-vector length. Node ordering comes from `instance_requests.node_order`, so a
solution's stop indices mean the same thing to every solver.

**Matrices are asymmetric.** `D[i,j] != D[j,i]`. Any solver assuming symmetry — including
the usual 2-opt delta shortcut — is incorrect here, and `two_opt` re-evaluates full tours
for exactly this reason.

---

## 3. The objective

Weights are **stored in data**, carried on every instance in `objective_weights_json`, and
echoed by `routing.objective.DEFAULT_WEIGHTS`. A test asserts the two definitions have not
drifted apart, because if they do, offline benchmarks stop describing online behaviour.

```
score = 1.00 · distance_km
      + 0.35 · (travel_time_min + traffic_delay_min)
      + 0.010 · fuel_inr
      + 0.010 · toll_inr
      + 12.0 · road_risk_score
      + 0.85 · empty_km
      − 1.10 · circular_logistics_score      (negative: a return load helps)
      [+ 500 · (0.5 − accessibility) if accessibility < 0.5]
```

Two deliberate properties:

- **`circular_bonus` is negative.** A return load genuinely improves the objective, which
  is how a longer route can and does win.
- **Inaccessible routes are penalised, not filtered.** A route a truck cannot take is not
  a cheap route — but penalising rather than dropping keeps the reason in the log.

`ScoreBreakdown` returns per-term contributions, so a selection can be *explained* rather
than asserted. `explain_selection` additionally reports the margin over the runner-up and
flags `margin_is_decisive = False` below 2% — showing false confidence to a driver is
worse than showing none.

---

## 4. Classical consumption

| Solver | Consumes | Notes |
|---|---|---|
| Dijkstra / A* | road graph | A* heuristic is haversine — admissible because road ≥ geodesic |
| k-shortest paths | road graph | Generates distinct corridors for the selection layer |
| Brute-force TSP | `distance_matrix` | **Ground truth**, ≤9 nodes; refuses larger |
| Nearest neighbour + 2-opt | `distance_matrix` | Asymmetry-safe |
| Simulated annealing | `distance_matrix` | Seeded, reproducible |
| OR-Tools routing | full instance | CVRP/VRPTW with capacity and time dimensions |

**Integer scaling matters.** OR-Tools works in integers: distances are scaled km→metres
(×1000) and times minutes→seconds (×60) with `np.rint` before conversion. Truncating km
to int would produce tours that appear better than the true optimum.

Ground truth is the point of the exact solver. Without it, an optimality "gap" against a
heuristic implies a bound that was never computed — so `optimality_gap` is **NULL**
whenever no exact solver ran, rather than being estimated.

---

## 5. Quantum consumption

The quantum track consumes the **same** `RoutingInstance` and derives a QUBO from its
`distance_matrix`. No separate quantum dataset exists; quantum-specific artifacts
(variable maps, penalties, parameters) live in `Res/`, never in `Data/`.

### Two encodings

**Permutation TSP** (`build_tsp_qubo`) — n² variables. Standard, and included because it
is the benchmark standard, but it does not scale:

| Nodes | Qubits | Statevector amplitudes |
|---|---|---|
| 4 | 16 | 65,536 |
| 5 | 25 | 3.4 × 10⁷ |
| 7 | 49 | 5.6 × 10¹⁴ (≈8 exabytes) |

`MAX_SIMULATOR_QUBITS = 22`. Above it the benchmark records `NOT ENCODABLE` explicitly
rather than skipping, because "no quantum row" and "quantum was not encodable" are
different findings.

**Edge selection** (`build_edge_selection_qubo`) — one variable per candidate edge, with
squared flow-conservation residuals producing genuine ZZ couplings. Scales with edges,
not nodes². **This is the formulation the hybrid pipeline uses.**

### Penalty weights are derived, not guessed

Set strictly above the largest achievable cost saving, so a constraint violation can never
pay for itself. Verified exhaustively:
`max(feasible energy) < min(infeasible energy)` over all 2ⁿ states.

### Mandatory classical validation

Before **any** quantum execution:

1. Brute-force the QUBO and confirm the optimum decodes to a valid route.
2. Confirm the optimum's energy equals the true route cost exactly (no penalty residue).
3. Confirm penalty separation holds.
4. Confirm non-zero quadratic coupling exists — a separable Hamiltonian needs no quantum
   computation.
5. Confirm QUBO ↔ Ising conversion is energy-exact.

A QUBO that does not encode the routing problem will still produce a beautifully
converging QAOA run of the wrong problem.

### Reporting requirements

Every sampling-based result **must** carry `feasible_rate`. In `v0.1`, QAOA's mean feasible
sampling rate is 0.061% — about 6 shots in 10,000. Reporting the best sample without that
figure would badly misrepresent the method.

---

## 6. Hybrid consumption

```
road graph -> k-shortest paths -> Pareto filter -> QUBO -> solve -> decode -> validate
```

Pareto filtering discards only dominated candidates — worse on *every* criterion — which
can never win under any non-negative weighting, so nothing reachable is lost. Further
truncation to the variable budget is flagged as `truncation_may_discard_optimum`, because
it can.

---

## 7. Result schema

`route_solutions` rows carry:

**Identity and provenance:** `solution_id`, `instance_id`, `algorithm_family`,
`algorithm_name`, `cost_snapshot_id`, `scenario_id`, `dataset_version`, `graph_version`,
`seed`, `hyperparameters_json`, `created_at`.

**Solution:** `ordered_stops`, `total_distance_km`, `total_time_min`,
`empty_distance_km`, `total_cost_inr`, `objective_value`, `feasible`,
`constraint_violations`, `optimality_gap`.

**Decomposed runtime** — never a single total:
`classical_preprocess_ms`, `solver_runtime_ms`, `quantum_execution_ms`, `queue_wait_ms`,
`classical_postprocess_ms`, `wall_clock_ms`.

**Quantum-only, NULL for classical rows:** `quantum_backend`, `quantum_qubits`,
`quantum_depth`, `quantum_shots`, `quantum_optimizer`, `qubo_version`,
`encoding_version`, `feasible_rate`.

Quantum fields are NULL rather than zero-filled so that *not applicable* is
distinguishable from *measured zero*.

---

## 8. Rules the benchmark harness enforces

1. **Same instance, same cost snapshot.** Enforced by exception.
2. **Runtime is decomposed.** "QAOA took 900 ms" is not comparable to "OR-Tools took
   40 ms" if the former excludes the surrounding circuit construction, or if it ran on a
   classical simulator.
3. **Optimality gap requires ground truth.** NULL otherwise.
4. **Feasibility rate for every stochastic method.**
5. **No automatic winner.** `summarise()` reports per-algorithm statistics and computes no
   verdict. Auto-declaring a paradigm winner across simulator and hardware rows is exactly
   the comparison this project must not make.

---

## 9. Artifact reuse and invalidation

Artifacts in `Res/` declare a volatility class, and `ArtifactStore.save` **refuses** to
write an artifact that does not name its cost snapshot — a result comparable to nothing
is not worth storing.

| Class | TTL | Examples |
|---|---|---|
| `DYNAMIC` | 15 min | Traffic-adjusted routes, TomTom responses |
| `SEMI_STATIC` | 30 days | Road topology, geodesic distances |
| `STATIC` | never | QUBO matrices, benchmarks, QAOA parameters for a fixed cost matrix |

Expired dynamic entries are deleted on read rather than returned — stale traffic data is
worse than none, because it looks authoritative.

**In production**, a stored quantum-derived prior may adjust only the circular-logistics
term, bounded to ±0.25. A stale artifact can shade a decision; it can never override live
cost data. The live path is fully functional with no artifacts and no quantum backend.

---

## 10. Traceability

The full chain Phase-A must support:

```
raw utterance ("गेहूं आजादपुर 20 बोरी")
  -> parsed slots + per-slot confidence
  -> canonical IDs (crop_key=wheat, mandi_key=azadpur)
  -> quantity normalization (20 bori -> 1000 kg, crop_default)   [or unresolved]
  -> transport_request (REQ_...)
  -> origin/destination location_ids (LOC_...)
  -> truck_availability match (capacity, radius, time)
  -> route_edges under a scenario_id
  -> route_instance (INS_...) pinned to a cost_snapshot_id (CST_...)
  -> classical | quantum | hybrid solver
  -> route_solution carrying that same cost_snapshot_id
  -> selected route + explanation
  -> UI
```

Every arrow is a stored foreign key, and every step is queryable after the fact.
