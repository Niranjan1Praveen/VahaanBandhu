# Phase-B Architecture

---

## 1. The stack

```
                        Browser (mobile-first)
                              │
                    Next.js 15 · App Router
                     Clerk  │  dev auth (local only)
                              │  Bearer / x-dev-user
                              ▼
                    FastAPI  ·  /api/v1
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
     MongoDB               Redis                 VB-QER
  application state    cache (optional)     the one optimizer
        │                                          │
        │                                          ▼
        │                              Phase-A datasets + artifacts
        │                                    (read-only)
        └──────────────────────┬───────────────────┘
                               ▼
                    External services, behind adapters
                    TomTom routing · TomTom traffic · OSM tiles
```

---

## 2. The two rules that shape everything

### One optimization interface

Application code calls **`VBQEROptimizer().solve()` and nothing else**. Not
Dijkstra, not A*, not OR-Tools, not 2-opt, not simulated annealing, not a QUBO
solver, not QAOA. Those are components *inside* VB-QER, and VB-QER decides
internally which of them contribute to a given instance.

```
FastAPI route handler
      ↓
RoutingService                  server/app/services/routing_service.py
      ↓
VBQEROptimizer.solve()          routing/ensemble/inference.py
      ↓  (internal, not the application's concern)
classical members · circular QUBO · quantum artifacts · incumbent guard
```

This is what lets Phase-A research keep moving without touching a line of
application code.

### No live quantum hardware in the request path

A queued or failed IBM job can never make the application unavailable. This is
not a convention — it is enforced by a test that imports the API in a **clean
subprocess** and asserts no IBM module appears in `sys.modules`:

```
server/tests/test_api.py::TestProductionSafety::test_no_live_quantum_hardware_in_request_path
tests/test_ensemble.py::TestProductionSafety::test_no_live_quantum_hardware_import
```

Real QPU work is offline research that produces versioned artifacts. Those
artifacts feed the ensemble only after passing held-out validation — and as of
this writing, **none has**, so `quantum_artifact_used` is `false` on every live
decision. That is reported, not hidden.

---

## 3. Backend layout

```
server/app/
  main.py                  app factory, middleware, lifespan
  core/
    config.py              pydantic-settings; no secret has a real default
    security.py            Clerk verification, dev auth, require_role()
    logging.py             structured JSON, redaction at the formatter
  db/
    mongodb.py             connection, collections, index definitions
    redis_cache.py         optional cache, version-aware keys
    seed.py                Phase-A loader + dev seed
  schemas/
    common.py              enums, GeoPoint, Quantity, status machine
    routing.py             RoutingRequest / RouteSolution — the frozen boundary
  repositories/            data access; no HTTP concerns
  services/
    routing_service.py     the VB-QER boundary
    quantity_service.py    the bori rule at the API edge
  api/routes/              thin handlers; validation and orchestration only
```

Layering is enforced by direction: routes → services → repositories → db. A
route handler never touches a collection directly, and a repository never
imports FastAPI.

---

## 4. The frozen Phase-A/Phase-B boundary

`RoutingRequest` and `RouteSolution` are versioned application types that expose
**no** VB-QER internals — no QUBO matrices, no bitstrings, no QAOA parameters,
no artifact payloads.

What *is* exposed is provenance the application legitimately needs:

```python
class OptimizationMetadata:
    vbqer_version, dataset_version, graph_version, cost_snapshot_id,
    artifact_version, profile, problem_type, final_route_source,
    quantum_component_invoked, quantum_artifact_used, quantum_artifact_source,
    quantum_hardware_called_live,   # always False
    computed_at, cached, compute_ms
```

Enough to reason about staleness and to trace a decision after the fact. Not
enough to leak research internals into a farmer's phone.

---

## 5. Data architecture

**Two stores, one direction.**

```
Data/ Research/ Res/ metadata/     research source of truth, read-only
        ↓  validated loader (seed.py)
MongoDB                            serving layer, rebuildable at any time
```

The compose file mounts the research directories **read-only** so the
application cannot modify them even by accident.

MongoDB is used as a document store, not as Postgres with JSON syntax — embed
where read together, reference where shared, GeoJSON + 2dsphere for spatial,
TTL for ephemeral, immutable append for optimization records. Detail in
[MIGRATION_SUPABASE_TO_MONGODB.md](MIGRATION_SUPABASE_TO_MONGODB.md).

**Redis is optional by design.** Every cache operation degrades to a miss when
Redis is unavailable. A Redis outage slows the application; it does not break it.

**Cache keys are version-aware:**

```
route:v1:{vbqer_version}:{sha256(origin, destination, stops, capacity,
                                 vbqer_version, graph_version,
                                 cost_snapshot_id, profile)}
```

Bumping the optimizer version makes every previously cached result unreachable
*by construction*. There is no invalidation step to forget.

---

## 6. Authorization

**The role lives in the database and nowhere else.** It is not in the token
payload, not in a header, not in the request body. `get_identity()` loads the
user document and reads `role` from it; `require_role()` compares against that.

The legacy app trusted a client-supplied role. That is the specific hole this
closes, and it is the reason a farmer hitting `/api/v1/truckers/jobs` gets 403
rather than a trucker's job list.

---

## 7. External services, behind adapters

| Service | Adapter | Degradation |
|---|---|---|
| TomTom routing | `routing/providers/tomtom.py` | Straight-line estimate, **labelled as an estimate** |
| TomTom traffic tiles | `GET /routes/live/traffic-config` | Overlay simply not offered |
| OSM base tiles | `RouteMap.jsx` `BASE_TILES` | Route geometry still renders on the dark ground |
| Clerk | `core/security.py` | Development auth (local only) |
| IBM Quantum | not in the request path at all | irrelevant to availability |

Two properties worth stating. First, the traffic key is **probed before it is
handed to the client**, so the frontend is never given a dead key. Second, a
synthetic route is **never** presented as a live one — the map shows
`असली सड़क मार्ग · TomTom` or `अनुमानित सीधी दूरी`, and the API reports
`provider: tomtom | mixed | offline_estimate` honestly across legs.

---

## 8. Frontend

The design language is inherited, not reinvented: pure-black ground
(`oklch(0.145 0 0)`), `lime-400` accent, `rounded-full` controls,
`rounded-3xl` surfaces, Geist + Poppins, Hindi-first.

**Mobile-first is structural, not responsive afterthought.** Navigation is a
bottom bar with 60px targets below `md` and a top bar above it. Quantity units
are chip rows rather than selects. Forms fit above the fold at 390px.

Three genuinely distinct experiences sharing primitives:

| Role | Leads with | Does not show |
|---|---|---|
| Farmer | Create request; crop / mandi / quantity | Vehicle detail, return loads |
| Trucker | **Empty km avoided** — the number that decides a job | Crop ontology, dealer stock |
| Dealer | Incoming deliveries above the requirement list | Route detail, optimization internals |

The map is one component; only the geometry each role cares about differs.

---

## 9. Testing

| Suite | Count | Needs |
|---|---|---|
| Phase-A research | 187 | nothing |
| Phase-B backend | 48 | MongoDB + Redis |
| **Total** | **235** | |

Backend tests run against **real** MongoDB and Redis. Index behaviour,
geospatial queries, status transitions and cache versioning are exactly what a
mock would fake away.

Screenshots come from the actually-running application via Playwright, with
console errors and failed requests collected per page. Nothing is constructed.
