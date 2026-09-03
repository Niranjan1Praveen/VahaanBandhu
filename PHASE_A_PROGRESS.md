# Phase-A Progress

**VahaanBandhu 2.0** · branch `phase-a` · dataset `v0.1` (prototype stage)

Legend: `[x]` complete and **verified** · `[~]` in progress · `[ ]` pending · `[!]` blocked

A task is marked complete only after it was executed and its output checked — not because
code was written.

---

## Summary

| Area | Status |
|---|---|
| Repository audit and environment | Complete |
| Data architecture, ontology, schemas | Complete |
| Prototype dataset generation | Complete — all QA suites pass |
| Validation and QA | Complete — schema, geospatial, referential, statistical, leakage all PASS |
| Classical optimization | Complete |
| Quantum optimization (formulation, QUBO, QAOA simulator) | Complete |
| IBM Quantum hardware | In progress — job submitted, queued |
| Notebooks and documentation | Complete — both notebooks execute top to bottom |
| Tests | Complete — 136 passing |
| Application layer (Clerk, MongoDB app wiring, 3 UIs) | **Pending — deliberate checkpoint** |

---

## Steps 1–5 · Audit and setup

- [x] **Audit repository.** Cloned `Niranjan1Praveen/VahaanBandhu`. Findings that
      contradicted the brief and changed the plan:
  - Auth is **Kinde**, not Clerk. No Clerk reference anywhere.
  - DB is **Supabase Postgres via Prisma**, not MongoDB.
  - No Docker, no `requirements.txt` (the README claimed one), no tests, no CI.
  - `server/TruckRouteNavigator/.env` is **committed to git** with a live Supabase URL and
    anon JWT; a TomTom key is **hard-coded** at `app.py:184`. Both need rotating and
    removing from history — flagged to the user.
  - Homepage design language recorded for later UI work: pure black
    `oklch(0.145 0 0)`, **lime-400** accent, Tailwind v4 CSS-variables-only (no config
    file), shadcn "new-york"/neutral, Geist + Poppins, `rounded-full` controls /
    `rounded-3xl` surfaces, all-Hindi copy.
- [x] **Record current architecture.** Next.js 15 App Router + Flask, two single-file
      Flask apps, Folium-rendered maps returned as raw HTML.
- [x] **Create development branch** `phase-a`.
- [x] **Establish directory structure.** `Data/{raw,staging,master,synthetic,features,splits,qa}`,
      `Research/`, `metadata/{generation_configs,manifests,schemas,versions}`,
      `Res/{classical,quantum,hybrid,qubo,route_cache,benchmarks,learned_parameters,candidate_routes,manifests}`.
- [x] **Python environment.** Project venv on **3.12** — the system default is 3.14, which
      has no OR-Tools or GeoPandas wheels. Pinned `requirements.txt`; resolved a
      pydantic conflict between pandera and qiskit-ibm-runtime (pinned 2.9.2).
- [x] **Secrets.** Root `.gitignore` and `.env.example` created; real credentials written
      to gitignored `.env`.

## Steps 6–9 · Ontology, schemas, registry

- [x] **Freeze ontology.** `vb/enums.py` — 15 controlled vocabularies.
- [x] **Create schemas.** `vb/validate/schemas.py` — 8 Pandera schemas encoding project
      rules, not just types (synthetic⇒zero-confidence, unresolved⇒null-kg,
      no self-loops, road ≥ geodesic, no heavy EVs, quantum_ready⇒encodable).
- [x] **Data dictionary.** `Research/data_dictionary.md`.
- [x] **Source registry.** `Data/source_registry.csv`, 7 sources including two recorded
      as `blocked`.

## Steps 10–14 · Geography and ontology data

- [x] **Administrative backbone.** 92 districts across DL/HR/PB/UP with explicit per-district
      NCR flags. **Not** acquired from LGD — curated approximate reference, tagged as such.
- [!] **Official location codes — BLOCKED.** Census/LGD not acquired. Consequence recorded
      in data: `VB-` prefixed internal district codes; subdistrict/village/pincode NULL
      throughout. Fabricating official codes was rejected as worse than empty fields.
- [x] **Geography masters.** `locations_master.csv`, 3,442 rows.
- [!] **Mandi reconciliation — BLOCKED.** e-NAM and state APMC portals not acquired.
      50 real mandi names carried with town-level coordinates,
      `coordinate_verified = False`, confidence 0.55. A schema check fails the build if
      that flag is ever set true without a cited source.
- [x] **Crop ontology.** 18 crops, canonical names strictly separated from the training
      alias pool.

## Steps 15–22 · Synthetic entity generation

- [x] **Synthetic shops.** 900, placed on a demand surface (urbanisation + market-town
      gravity), not uniformly over polygons.
- [x] **Farmer nodes.** 1,400 privacy-safe pickup points on an agricultural envelope
      0.4–3.5 km outside settlement cores. No names, no addresses, by design.
- [x] **Trucks.** 600 with class-constrained physical coherence; 1,222 availability slots
      supporting partial return loads.
- [x] **Hindi/English/Hinglish NLU corpus.** 6 template families × 3 languages, phonetic
      ASR noise (not random flips), Devanagari digits, code-switching, dropped fields.
      Labels stay canonical under all corruption.
- [x] **Transport requests.** 18,000 — 83.1% feasible, 6.7% unresolved quantity, 6.2%
      ambiguous, 3.9% infeasible. Hard negatives labelled, not dropped.
- [x] **Circular logistics.** `routing/circular.py` — forward/return/empty km, utilization,
      fuel, CO2 proxy, avoided empty km, with a detour-ratio threshold so a far-off
      "return load" is correctly rejected as a separate job.

## Steps 23–25 · Route graph and instances

- [x] **Route graph.** 375,968 directed edges. k=8 NN plus 3-nearest-mandi links.
      Length-dependent detour factor (1.42→1.18); haversine retained as a QA lower bound,
      never used as road distance.
- [x] **Time-dependent scenarios.** 8 scenarios; `SCN_BASELINE` immutable, each scenario a
      separate row set.
- [x] **Optimization instances.** 2,000 across TSP/CVRP/VRPTW/PDP/CIRCULAR_VRP.
      **Bug found and fixed:** random vehicle-count assignment made 99% of instances
      capacity-infeasible; fleet is now sized to the load. Now 1,955/2,000 feasible.

## Steps 26–29 · Optimization

- [x] **Classical solvers.** Dijkstra, A* (admissible haversine heuristic), k-shortest
      paths, brute-force exact TSP (ground truth), nearest-neighbour, 2-opt
      (asymmetry-safe), simulated annealing, OR-Tools CVRP/VRPTW.
- [x] **Quantum-ready subset.** 200 instances.
      **Correction made:** the original ceiling of 7 customers implied 64 qubits and
      failed with an 8.6-exabyte memory request. Ceiling lowered to 3; the benchmark now
      records `NOT ENCODABLE` explicitly rather than skipping silently.
- [x] **QUBO/Ising.** Permutation TSP (n² vars) and edge-selection (per-edge vars, the
      scalable one). Validated exhaustively: optimum decodes to the true shortest path,
      energy equals route cost exactly, penalty separation holds over all 2ⁿ states,
      genuine ZZ coupling present, Ising conversion energy-exact to < 1e-9.
- [x] **QAOA simulator.** Runs and finds the optimum on tiny problems.
      **Honest result at scale:** 16.0% mean optimality gap, feasible in 3/8 runs, 0.061%
      feasible sampling rate. No quantum advantage observed; none claimed.

## Steps 30–34 · Splits, QA, exports

- [x] **Splits.** Four-way leakage defence — district, temporal, template-family and
      structural-hash holdouts, plus a duplicate-utterance promotion pass that closed
      **149 verbatim duplicates** straddling the split.
- [x] **Geospatial QA.** PASS. **Corrected the spec's coarse bbox:** the suggested
      23.0–31.5 N excludes Gurdaspur (32.04 N) and Pathankot (32.27 N), genuine Punjab
      districts, and rejected 176 valid locations. Widened to 23.0–32.6 N.
- [x] **Statistical QA.** PASS — zero impossible values.
- [x] **Leakage QA.** PASS — all violation counts zero.
- [~] **Model-ready exports.** Splits are assigned in-table and the derived-export layer
      (`Data/features/`, `Data/splits/`) is scaffolded but not yet populated.

## Steps 35–36 · Notebooks and documentation

- [x] **`Research/synthetic_data_generation.ipynb`** — 48 cells, **executes top to bottom**,
      generates the prototype datasets and runs the QA suite. Not a Markdown-only notebook.
- [x] **`Research/route_optimization_classical_quantum.ipynb`** — 54 cells, **executes top
      to bottom**, Experiments A–I.
- [x] `Research/data_dictionary.md`
- [x] `Research/DATASET_METHODOLOGY.md`
- [x] `Research/DATA_SOURCES.md`
- [x] `Research/DATA_QA_REPORT.md` — **generated from the validators**, not hand-written
- [x] `Research/ROUTE_OPTIMIZATION_DATA_SPEC.md`
- [x] `Research/QUANTUM_ROUTE_OPTIMIZATION.md` — includes the QUAV paper review and the
      critique that changed our design
- [x] `Research/QUANTUM_REFERENCES.md`

## Steps 37–43 · Application, infrastructure, testing

- [x] **Tests.** 136 passing across units, IDs/geo/NCR, NLU, quantum, routing, datasets.
- [x] **TomTom integration.** Provider abstraction with multi-key rotation, short-TTL
      operational caching, and a hard matrix-size cap. **No response is persisted into
      `Data/`** — storage/training terms unverified.
- [x] **IBM Quantum.** Connection **verified**: `ibm_fez`, `ibm_marrakesh`, `ibm_kingston`
      (156 qubits each) observed operational.
- [~] **Experiment H — hardware run.** Job submitted to a real backend; **queued at the
      time of writing**. Result will be written to
      `Res/quantum/experiment_h_ibm_hardware.json`. If it fails, the artifact records
      `executed: false` with a reason — **no simulator result will be relabelled as
      hardware**.
- [x] **MongoDB loader.** `vb/load_mongo.py` with GeoJSON points and 2dsphere indexes.
      CSVs remain canonical; Mongo is a rebuildable serving layer.
- [x] **Docker.** `docker-compose.yml` with a working, health-checked `mongo` service; no
      credentials in any image.
- [ ] **Clerk migration** (from the existing Kinde auth).
- [ ] **MongoDB application wiring** (replacing Prisma/Supabase in the app layer).
- [ ] **Backend API** (`api/`) exposing lookup, NLU parsing, routing, matching.
- [ ] **Farmer interface** — voice/text, Hindi/English/Hinglish, crop/mandi/quantity.
- [ ] **Trucker interface** — location, capacity, nearby loads, circular opportunities.
- [ ] **Shop-owner interface** — replenishment, supplier, return-trip matching.
- [ ] **Docker `api`/`web` services verified** (they will not build until `api/` exists).
- [ ] **Full local system run.**

---

## Blockers

| # | Blocker | Impact | Resolution path |
|---|---|---|---|
| 1 | Census/LGD directory not acquired | No official location codes; internal codes used, subdistrict/village/pincode NULL | Phase-B: download LGD, populate codes, replace circular envelopes with real polygons |
| 2 | e-NAM / state APMC not acquired | Mandi coordinates unverified; `enam_enabled` is a plausible assignment, not verified status | Phase-B: reconcile against e-NAM **and** state portals — e-NAM alone is not the full universe of physical mandis |
| 3 | TomTom storage/training terms unverified | Route costs use an offline detour model rather than measured routing | Read current terms; record the finding in DATA_SOURCES.md before persisting anything |
| 4 | IBM hardware queue latency | Experiment H not yet returned | Job is queued; artifact will record the true outcome either way |

## Assumptions made

1. **CSVs are canonical; MongoDB is a serving layer.** Rebuildable from files, so a
   dataset version stays a set of hashed artifacts.
2. **Synthetic-but-plausible geography is acceptable for the prototype** (user decision),
   provided nothing synthetic is ever presented as verified.
3. **Approximate coordinates on real mandi names are acceptable** provided precision and
   confidence are declared and `coordinate_verified` stays false.
4. **The quantum track is offline-only.** The live path must work with no quantum backend.

## Deliberate deviations from the brief

| Brief said | What was done | Why |
|---|---|---|
| Coarse bbox lat 23.0–31.5 | 23.0–**32.6** | 31.5 excludes real Punjab districts and rejected 176 valid locations |
| Quantum instances "5–20 service nodes" | 3–7, with permutation encoding capped at 3 | (n+1)² qubits: 7 nodes = 64 qubits = 2⁶⁴ amplitudes. Measured, not assumed |
| MongoDB for the platform | Mongo as a serving layer, CSVs canonical | Keeps the research pipeline reproducible and version-hashable |
| Review two GitHub repos in depth | Reviewed at the architectural level only | Recorded honestly in QUANTUM_REFERENCES.md rather than overclaiming |

---

## Next session

The data and optimization foundation is complete and verified. Remaining work is the
application layer, in dependency order:

1. `api/` — Flask service over the routing engine and datasets.
2. Clerk migration replacing Kinde.
3. MongoDB wiring replacing Prisma/Supabase in the app.
4. The three interfaces, holding to the existing black/lime-400 design language.
5. Verify the full Docker stack and run the system end to end.
