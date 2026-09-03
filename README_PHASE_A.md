# VahaanBandhu 2.0 — Phase-A

A rural circular-logistics data and optimization platform connecting **farmers**,
**truckers** and **rural construction-material dealers** across Delhi NCR, Haryana,
Punjab and Uttar Pradesh.

Phase-A delivers the **data and optimization foundation**: a reproducible synthetic
dataset, a validated route-optimization engine with classical and quantum tracks, and the
research documenting both.

---

## Quick start

```bash
# 1. Environment (Python 3.12 — OR-Tools and GeoPandas have no 3.13/3.14 wheels)
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt      # Windows
# .venv/bin/pip install -r requirements.txt        # macOS/Linux

# 2. Secrets
cp .env.example .env      # then fill in TOMTOM_API_KEYS, IBM_QUANTUM_TOKEN, MONGODB_URI
```

```bash
# 3. Generate the prototype dataset (~17 s)
python -m vb.pipeline --stage prototype --version v0.1
```

```bash
# 4. Validate everything
python -m vb.run_qa
```

```bash
# 5. Run the test suite
python -m pytest
```

```bash
# 6. Optional: MongoDB serving layer
docker compose up -d mongo
python -m vb.load_mongo --drop
```

---

## What Phase-A produced

| Dataset | Rows | Provenance |
|---|---|---|
| `locations_master.csv` | 3,442 | mixed |
| `mandis.csv` | 50 | real names, approximate coordinates |
| `crops.csv` | 18 | ontology |
| `shops.csv` | 900 | synthetic |
| `farmer_nodes.csv` | 1,400 | synthetic, privacy-safe |
| `trucks.csv` | 600 | synthetic |
| `transport_requests.csv` | 18,000 | synthetic, Hindi/English/Hinglish |
| `route_edges.csv` | 375,968 | synthetic, directed, 8 scenarios |
| `route_instances.csv` | 2,000 | synthetic, solver-agnostic |

All QA suites pass: schema, geospatial, referential, statistical, leakage. 136 tests pass.

---

## Layout

```
Data/            master (mixed) and synthetic datasets + source_registry.csv + qa/
Research/        two executable notebooks + six documents
Res/             reusable optimization artifacts (benchmarks, QUBOs, parameters, caches)
metadata/        generation configs, manifests, schemas, versions
vb/              data pipeline: ontology, generators, units, splits, validation
routing/         providers | classical | quantum | hybrid | evaluation | engine
tests/           136 tests
tools/           notebook and report builders, hardware experiment runner
docker/          API and web Dockerfiles
```

## Start here

- **[`Research/synthetic_data_generation.ipynb`](Research/synthetic_data_generation.ipynb)** —
  executes the whole data pipeline with commentary.
- **[`Research/route_optimization_classical_quantum.ipynb`](Research/route_optimization_classical_quantum.ipynb)** —
  Experiments A–I, classical through quantum.
- **[`PHASE_A_PROGRESS.md`](PHASE_A_PROGRESS.md)** — status, blockers, deviations.
- **[`Research/DATA_SOURCES.md`](Research/DATA_SOURCES.md)** — provenance and licensing,
  including what could **not** be acquired.

---

## Three rules the codebase enforces

**1. Synthetic is never presented as verified.** Every spatial row carries
`is_synthetic`, `geocode_precision`, `confidence_score` and `source_id`. The schema
*rejects* a synthetic row with non-zero real-world confidence. Mandi coordinates are
town-level approximations and carry `coordinate_verified = False` throughout.

**2. No fabricated quantities.** `bori` is a sack, not a unit of mass — its fill weight
depends on crop and packaging. Where it cannot be justified, `quantity_kg` is **NULL** and
the row is labelled `unresolved` (6.7% of the corpus). `fits_vehicle()` returns `None`,
not `False`, for such a load: an unknown load is not a load that fits.

**3. Comparability is enforced, not assumed.** Two solver results are comparable only if
they share an `instance_id` **and** a `cost_snapshot_id`. The benchmark harness raises
rather than comparing across cost snapshots.

---

## Quantum: what was and was not found

The primary research question is whether quantum or hybrid optimization can improve
route selection *after* classical preprocessing has reduced the search space.

**Phase-A answer: no improvement observed.** On 8 quantum-ready instances, QAOA at p=2
showed a 16.0% mean optimality gap and returned a feasible solution in 3 of 8 runs, with
a 0.061% feasible sampling rate. Classical baselines solved the same instances optimally
in under a millisecond.

What *was* established: a **correct** encode → solve → decode pipeline (the QUBO's
exhaustive optimum equals the true shortest path exactly, penalties strictly separate
feasible from infeasible, Ising conversion is energy-exact), and an honest benchmark
apparatus with decomposed runtimes and mandatory feasibility-rate reporting.

**No claim of quantum advantage is made** — no speedup, no better routes, nothing
exponential. See [`Research/QUANTUM_ROUTE_OPTIMIZATION.md`](Research/QUANTUM_ROUTE_OPTIMIZATION.md).

### Why quantum is offline-only

```
OFFLINE   instances -> classical baselines -> QUBO -> simulator -> hardware
          -> benchmarks, learned parameters, route priors
                                    |  artifacts only, never a live call
                                    v
LIVE      request -> TomTom candidates -> reduce -> fast classical scoring
          (+ optional stored prior) -> best route + explanation -> UI
```

Routing a live user request through a QPU would be worse on latency, reliability and
solution quality. **The live path is fully functional with no quantum backend**, and is
tested that way.

---

## Security notes

- `.env` is gitignored; `.env.example` documents every variable.
- **Pre-existing issues in the original repository, not introduced here:**
  `server/TruckRouteNavigator/.env` is committed to git with a live Supabase URL and anon
  JWT, and a TomTom key is hard-coded at `app.py:184`. **Both should be rotated and purged
  from git history.**
- No credentials appear in any Docker image; secrets are injected at runtime.

## Known limitations

1. No official administrative data (LGD/Census not acquired) — internal district codes,
   NULL subdistrict/village/pincode.
2. Mandi coordinates are town-level, unreconciled against e-NAM or state APMC portals.
3. Containment QA uses circular district envelopes, not boundary polygons.
4. Road costs come from an offline detour model, not measured routing.
5. Everything except mandi and district names is synthetic — **the data supports no
   distributional claim about real rural logistics.**

## Not yet built

The application layer is a deliberate checkpoint: `api/`, the Clerk migration (the repo
currently uses Kinde), MongoDB app wiring (currently Prisma/Supabase), and the three user
interfaces. The Docker `api` and `web` services will not build until `api/` exists.
