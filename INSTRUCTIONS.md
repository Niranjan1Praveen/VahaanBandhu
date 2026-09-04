# Running VahaanBandhu 2.0

Everything below runs **locally**. Nothing deploys, and no live quantum hardware
is required.

---

## 1. What you need

| Tool | Version used here | Notes |
|---|---|---|
| Docker Desktop | 29.7.2 | Must be **running** before you start |
| Python | 3.12 | A `.venv` already exists in the repo root |
| Node.js + npm | Next.js 15.3.2 | For the frontend |
| Git Bash / PowerShell | — | Either works |

Check Docker is actually up before anything else:

```bash
docker info
```

If that errors, open Docker Desktop and wait ~30–60 seconds for the engine.

---

## 2. Environment file

Copy the template and fill in what you have:

```bash
cp .env.example .env
```

**Nothing is required to start the app.** Every integration degrades gracefully:

| Variable | If missing |
|---|---|
| `TOMTOM_API_KEYS` | Map falls back to straight-line estimates, clearly labelled |
| `CLERK_SECRET_KEY` / `CLERK_PUBLISHABLE_KEY` | Development sign-in is used instead |
| `IBM_QUANTUM_TOKEN` | Irrelevant to the app — hardware is offline research only |
| `MONGODB_URI` / `REDIS_URL` | Defaults point at the Docker containers |

`.env` is gitignored. Keep it that way — see
[SECURITY_ACTION_REQUIRED.md](SECURITY_ACTION_REQUIRED.md).

---

## 3. Fastest path (recommended)

Three terminals. Data services in Docker, app processes on the host — this gives
the quickest edit-reload loop.

### Terminal 1 — data services

```bash
docker compose up -d mongo redis
```

Wait for both to report healthy:

```bash
docker compose ps
```

You want `Up (healthy)` for `vb-mongo` and `vb-redis`.

### Terminal 2 — load data, then start the API

One-time (or whenever you want a clean database):

```bash
PYTHONPATH=. MONGODB_URI=mongodb://localhost:27017 ./.venv/Scripts/python.exe -m server.app.db.seed --reset
```

This loads a subset of the Phase-A research datasets into MongoDB — about 1,320
locations, 50 mandis, 18 crops — plus three demo users. It reads `Data/` and
never writes to it.

Then:

```bash
PYTHONPATH=. MONGODB_URI=mongodb://localhost:27017 REDIS_URL=redis://localhost:6379/0 \
  ./.venv/Scripts/python.exe -m uvicorn server.app.main:app --host 127.0.0.1 --port 8000
```

Check it:

```bash
curl http://127.0.0.1:8000/api/v1/health
```

Interactive API docs: <http://127.0.0.1:8000/docs>

### Terminal 3 — frontend

```bash
cd client
npm install          # first time only
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000 npm run dev
```

Open <http://localhost:3000>.

---

## 4. Full Docker stack

```bash
docker compose up --build
```

Slower to iterate on, but closer to a deployed topology. Same URLs.

To stop, keeping your data:

```bash
docker compose down
```

To stop **and wipe** the database volumes:

```bash
docker compose down -v
```

---

## 5. Signing in

With no Clerk credentials configured, <http://localhost:3000/signin> offers three
seeded demo users:

| User | Role | Sees |
|---|---|---|
| `dev_farmer_01` — रमेश कुमार | Farmer | Transport requests, crop/mandi/quantity, route |
| `dev_trucker_01` — सुखबीर सिंह | Trucker | Vehicle, jobs, **return loads** |
| `dev_dealer_01` — श्री बालाजी | Input dealer | Material requirements, incoming deliveries |

A yellow **डेमो मोड** banner appears whenever development auth is in use. It is
refused outside development: `demo_auth_active` requires *both*
`DEV_AUTH_ENABLED=true` **and** a non-production `ENVIRONMENT`, so a single
misconfigured variable cannot expose it.

With Clerk configured, the same page shows the Clerk flow instead.

---

## 6. Worth looking at

**The bori rule** — the farmer dashboard has a sugarcane request in **बोरी**.
It shows `quantity_kg = null` and asks how many kilograms are in one bori,
because bag weight varies by crop and packaging. It is never silently assumed to
be 50 kg. Enter a weight and the request moves from `DRAFT` to `REQUESTED`.

**Circular logistics** — the trucker dashboard leads with **खाली किलोमीटर बचे**
(empty km avoided). The seeded corridor runs Rohtak depot → Sonipat mandi, ~40 km
apart, with dealers positioned along the way home and one deliberately in the
wrong direction, so the difference between a real opportunity and a pointless
detour is visible.

**The map** (`/app/map`) — real TomTom road geometry (~1,761 points across the
trucker's four legs, following actual carriageways), a live TomTom traffic
overlay you can toggle, and role symbols: 🏠 depot, 🌾 farm, 🏛️ mandi, 🏪 dealer.
Solid lime is the outbound leg; dashed amber is the return load.

If TomTom is unavailable the map says **अनुमानित सीधी दूरी** rather than
presenting an estimate as a measured route.

---

## 7. Tests

```bash
# Phase-A research suite (no services needed)
PYTHONPATH=. ./.venv/Scripts/python.exe -m pytest tests/ -q

# Phase-B backend (needs mongo + redis running)
PYTHONPATH=. MONGODB_URI=mongodb://localhost:27017 REDIS_URL=redis://localhost:6379/0 \
  ./.venv/Scripts/python.exe -m pytest server/tests/ -q
```

Screenshots, captured from the actually-running app:

```bash
PYTHONPATH=. ./.venv/Scripts/python.exe tools/capture_screenshots.py
```

Output lands in `artifacts/screenshots/`, organised by checkpoint. Both servers
must be running.

---

## 8. Architecture, briefly

```
Next.js ──► FastAPI ──► MongoDB (application state)
                   └──► Redis   (cache; optional by design)
                   └──► VB-QER  (the one optimization interface)
                            └──► Phase-A datasets and artifacts
```

**Two rules that matter:**

1. **Application code calls `VBQEROptimizer().solve()` and nothing else.** Not
   Dijkstra, not OR-Tools, not QAOA. Those are components *inside* VB-QER.
2. **No live quantum hardware in the request path.** A queued or failed IBM job
   cannot make the app unavailable. This is enforced by a test that verifies the
   IBM runtime is absent from the API's import graph in a clean subprocess.

Redis is a performance component. If it goes down the app keeps working — every
cache operation degrades to a miss.

---

## 9. When something breaks

**`docker info` fails** — Docker Desktop is not running. Start it and wait.

**Port already in use** — find and stop the holder:

```bash
netstat -ano | grep ":8000" | grep LISTENING     # or :3000
taskkill //PID <pid> //F
```

**API returns 500 on every request** — check MongoDB:

```bash
docker compose ps
docker compose logs mongo --tail 30
```

**Frontend loads but every panel errors** — the API is not reachable. Confirm
`curl http://127.0.0.1:8000/api/v1/health` and that
`NEXT_PUBLIC_API_BASE_URL` matches where the API is actually listening.

**Map shows straight lines** — TomTom is not answering. Check which keys work:

```bash
curl -H 'x-dev-user: dev_trucker_01' http://127.0.0.1:8000/api/v1/routes/live/traffic-config
```

Of the three keys supplied, one is dead (401), one works, one is 403 for routing
but fine for traffic tiles. The provider rotates automatically.

**`redis:7-alpine` will not pull** — a Docker Desktop proxy issue on this
machine returns HTTP for an HTTPS request. `redis:7` pulls fine and is what the
compose file uses.

**Screenshots fail** — both servers must be running, and Playwright's browser
must be installed:

```bash
./.venv/Scripts/python.exe -m playwright install chromium
```
