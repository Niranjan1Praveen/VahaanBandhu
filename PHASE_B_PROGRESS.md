# Phase-B Progress

Branch `phase-b-app-revamp`. All work local; nothing pushed.

Status values: **COMPLETE** (runtime or test evidence) · **PARTIAL** ·
**BLOCKED** · **NOT REQUIRED**.

---

## 1. Summary

| Component | Status | Verification | Remaining |
|---|---|---|---|
| Legacy audit | COMPLETE | `PHASE_B_AUDIT.md`, `LEGACY_MIGRATION_MAP.md` | — |
| Security audit | COMPLETE | `.env` untracked; hardcoded key removed | **You must rotate 2 credentials** |
| Prisma removal | COMPLETE | 0 refs in `package-lock.json`; `next build` passes | — |
| Supabase removal | COMPLETE | 0 imports in active source | — |
| Kinde removal | COMPLETE | 0 imports in active source | — |
| Flask → FastAPI | COMPLETE | 32 endpoints serving; no Next route calls Flask | Legacy Flask retained for reference |
| Postgres → MongoDB | COMPLETE | 9 collections, 24 indexes, seeded in container | Real-data migration not run (no Supabase contact) |
| Redis | COMPLETE | Outage test: all endpoints 200 with Redis stopped | — |
| Docker (mongo/redis) | COMPLETE | `Up (healthy)` | — |
| Docker (api) | COMPLETE | `Up (healthy)`, container healthcheck passes | — |
| Docker (web) | COMPLETE | `Up`, serves `/`, `/signin`, `/demo`, `/app/farmer` | No healthcheck defined |
| VB-QER boundary | COMPLETE | Import audit + subprocess test | — |
| No live QPU | COMPLETE | qiskit absent from the API image | — |
| Clerk real login | PARTIAL | Implemented; **never exercised against a tenant** | Needs credentials |
| Show Demo | COMPLETE | 15 frontend tests + screenshots | — |
| Farmer / Trucker / Dealer | COMPLETE | Live API + screenshots at 4 widths | — |
| Map + TomTom | COMPLETE | 1,761 real geometry points; traffic overlay | — |
| Backend tests | COMPLETE | 55 passing | — |
| Frontend tests | COMPLETE | 25 passing | — |
| Phase-A regression | COMPLETE | 235 passing | — |
| Screenshots | COMPLETE | 28, zero console errors | — |
| Documentation | COMPLETE | 9 documents | — |
| Phase-A scaling study | PARTIAL | 208 rows, sizes 4–8 | Deferred; not a correctness failure |

---

## 2. Tests

| Suite | Count | Command |
|---|---|---|
| Phase-A research | **235** | `pytest tests/` |
| Phase-B backend | **55** | `pytest server/tests/` |
| Frontend (vitest) | **25** | `cd client; npm test` |
| **Total** | **315** | |

**Correction:** an earlier report said "235 tests = 187 Phase-A + 48 backend".
That was wrong. `pytest.ini` had `testpaths = tests`, so the default run only
ever collected Phase-A — 235 was Phase-A alone. `testpaths` now covers both.

Production build: `next build` succeeds, 15 routes.

---

## 3. Endpoints verified against the Docker stack

All against `http://localhost:8000` with the containerised API:

| Endpoint | Result |
|---|---|
| `GET /api/v1/health` | 200, `status: ok` |
| `GET /api/v1/health/live` · `/ready` | 200 |
| `GET /api/v1/crops` · `/mandis` | 200 |
| `GET /api/v1/routes/engine/info` | 200, `live_quantum_hardware_call: false` |
| `GET /api/v1/me` (farmer) | 200 |
| `GET /api/v1/farmers/requests` | 200 |
| `GET /api/v1/truckers/jobs` | 200 |
| `GET /api/v1/dealers/requirements` | 200 |
| `GET /api/v1/routes/live/traffic-config` | 200, traffic available |
| `POST /api/v1/routes/live` | 200, 1,761 geometry points from TomTom |
| farmer → trucker endpoint | **403** |
| no auth | **401** |
| `/docs` | 200 |

Frontend: `/`, `/signin`, `/demo`, `/app/farmer` all 200.

---

## 4. Redis outage test

With `docker compose stop redis`:

```
health              -> ok   (redis.connected=false, required=false)
/farmers/requests   -> 200
/mandis             -> 200
/routes/live        -> 200
```

Reconnected cleanly on `docker compose start redis`. Redis is a cache, never a
source of truth.

---

## 5. Real bugs found and fixed

Worth listing, because several were silent:

1. **TomTom provider read `os.environ` directly**, but the app loads `.env`
   through pydantic-settings, which does not populate `os.environ`. The provider
   saw zero keys and every route degraded to a straight line.
2. **`RouteCandidate.to_dict()` added a derived `n_geometry_points`** that the
   cache stored and replayed into the constructor. The first call worked; every
   cached call raised `TypeError` and fell back.
3. **Key rotation covered 403/429 but not 401.** Key #1 is dead (401); without
   401 in rotation it failed every request while a working key sat unused.
4. **Provider label was last-writer-wins** across legs. Now reports
   `tomtom` / `mixed` / `offline_estimate` honestly.
5. **The API image had no pandas**, so in Docker `RoutingService` silently
   degraded to estimates and the seeder could not read the master CSVs.
6. **Degenerate seed geometry**: the trucker's home was effectively at the
   mandi, making every `empty_km_avoided` legitimately 0. The formula was right;
   the scenario was not.
7. **Navbar used `<Link>` without importing it** after the Kinde swap — caught
   by ESLint during `next build`.
8. **The `useRouter` test mock returned a fresh object per call**, so effects
   depending on `router` re-fired every render and a dashboard looped. Next's
   real `useRouter` is stable; the mock was wrong, not the component.
9. **The corridor generator produced only within-leg permutations** (Phase-A),
   a subset of 2-opt's neighbourhood, so the QUBO optimum equalled the incumbent
   on 10/10 instances and quantum could not contribute by construction.

---

## 6. Known limitations

- **Clerk is unexercised.** The integration is implemented; no tenant was
  available. Token verification, refresh and webhooks are untested.
- **The web container has no healthcheck.** It reports `Up`, not `Up (healthy)`.
- **No real Supabase data was migrated.** No Supabase project was contacted,
  per the local-only constraint. Tooling and mapping are documented.
- **Voice input is not implemented.** The API accepts `input_mode` and
  `raw_utterance`; no speech recognition exists. Not faked.
- **Real-time GPS tracking is not implemented.**
- **Legacy Flask, Prisma schema and the old dealer dashboard remain in the tree**
  as reference. None is in an active path.
- **VB-QER live-mode latency is unprofiled.** The ensemble took ~4 s on Phase-A
  benchmarks; the live path currently uses shortest-path members, not the full
  ensemble.

---

## 7. Deferred Phase-A research

The circular option-size scaling study completed sizes 4–8 (208 rows) and died
around size 10 when the host processes were lost with Docker Desktop. **Not a
correctness failure** — no exception, no bad data. Deferred deliberately;
Phase-B was the priority and the study is an independent research track.

---

## 8. Commits

```
phase-b: audit, security, FastAPI foundation + REAL IBM hardware results
phase-b: FastAPI + MongoDB + Redis running with seed data
phase-b: map with real TomTom geometry, live traffic, role symbols
Phase-A: all three IBM QPUs returned real measurements
phase-b: backend tests, INSTRUCTIONS.md
phase-b: remove Prisma/Supabase/Kinde runtime deps; two-path auth entry
phase-b: frontend test suite, demo-auth guards, corrected test counts
phase-b: full Docker stack verified end to end
```

Nothing pushed. No history rewritten. No remotes touched.
