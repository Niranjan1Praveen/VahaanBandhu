# Phase-B Legacy Audit

**Branch:** `phase-b-app-revamp` · audited before any application code changed.

---

## 1. Current state

| Layer | Legacy | Target |
|---|---|---|
| Frontend | Next.js 15.3.2 (App Router, JS) | Next.js (retained, refactored) |
| Auth | **Kinde** | **Clerk** |
| Backend | **Flask**, 2 single-file apps | **FastAPI** |
| DB | **Supabase Postgres + Prisma** | **MongoDB** |
| Cache | none | **Redis** |
| Maps | Folium, server-rendered HTML | client-side map behind an adapter |
| Optimization | inline in `app.py` | **VB-QER** via `RoutingService` |
| Containers | none | Docker Compose |

**Scale:** 67 frontend source files, 3 Python backend files.

---

## 2. Frontend

**Routes:** `/` (landing), `/farmer/vehicle-request`, `/(dashboard)/input-dealer`,
`/(dashboard)/input-dealer/documentation`.

**Sections** (`src/sections/`): Navbar, Hero, Introduction, Features,
SignupOptions, Footer. All copy is Hindi/Devanagari.

**UI kit:** 26 shadcn primitives in `src/components/ui/`. `components.json` =
new-york / neutral / cssVariables / lucide.

### Design tokens — MUST be preserved

From `src/app/globals.css`. Note `:root` is the **dark** theme (inverted from
the shadcn default):

```
--radius: 0.625rem
--background: oklch(0.145 0 0)      --foreground: oklch(0.985 0 0)
--card: oklch(0.205 0 0)            --primary: oklch(0.922 0 0)
--muted-foreground: oklch(0.708 0 0)
--border: oklch(1 0 0 / 10%)        --input: oklch(1 0 0 / 15%)
```

Accent palette is Tailwind literals, not tokens: **`lime-400`** is the brand
accent (`bg-lime-400 text-neutral-950`), `neutral-900` for card surfaces,
`neutral-950/70` for the nav, `border-white/15` and `border-white/10` for edges.

Signature button variants (`ui/button.jsx:23-24`):
```
login:  border border-white h-12 px-6 font-medium rounded-full
signup: border bg-lime-400 text-neutral-950 border-lime-400 h-12 px-6 font-medium rounded-full
```

Conventions: sections `py-24 px-4`; pill nav
`border border-white/15 rounded-[27px] md:rounded-full bg-neutral-950/70 backdrop-blur`;
feature cards `bg-neutral-900 border border-white/10 p-6 rounded-3xl`; eyebrow tags
`border border-lime-400 text-lime-400 px-3 py-1 rounded-full uppercase`. Radii are
polarized: `rounded-full` controls, `rounded-3xl` surfaces.

Fonts: Geist, Geist Mono, Poppins (400/500/600/700). Metadata title `वाहनबन्धु`.

**Tailwind v4 with no config file** — all theming lives in `globals.css` under
`@theme inline`.

---

## 3. Backend (legacy Flask)

`server/TruckRouteNavigator/`, no `requirements.txt` despite the README claiming one.

| File | Route | Purpose |
|---|---|---|
| `app.py:179` | `GET /` | ~570 lines. Reads latest `VoiceResponse`, finds nearest truck by haversine, resolves mandi, calls TomTom routing + traffic, runs a quantum delay model, returns a **rendered Folium map as raw HTML**. Port 5000, `debug=True`. |
| `mandi.py:16` | `GET /mandi-map` | Standalone map of `MandiLatLong`. Port 5002. |
| `Qdelay.py` | — | `quantum_delay_prediction()` — 5-qubit Ry/Rx circuit, `BasicSimulator`. |

**Next.js API routes:** `voice-response` (POST, Prisma insert),
`auth/[kindeAuth]` (Kinde catch-all), `auth/creation` (post-login upsert then
redirect to a **hardcoded** `http://localhost:3000/input-dealer`).

**Dead code:** `static/js/track_driver.js` and `route_to_mandi.js` call
`POST /get-route` and `GET /update-trucks` — neither endpoint exists. No
`templates/` directory. `gps_simulation.cpython-312.pyc` with no source.
`app.py` also defines `quantum_route_evaluation()` and
`compare_haversine_vs_qvr()` that are **never called**.

**Duplication:** the two route-building blocks in `app.py` (truck→user,
user→mandi) are near-verbatim copies.

---

## 4. Database (legacy)

`client/prisma/schema.prisma` — Postgres, `DATABASE_URL` / `DIRECT_URL`.

| Model | Fields |
|---|---|
| `User` | id, email, firstName, lastName, profileImage, createdAt, `role Role @default(DRIVER)`; enum `Role { DRIVER, INPUTDEALER }` |
| `MandiLatLong` | State, Mandi, Mandi_Hindi, Latitude?, Longitude? |
| `Truck` | State, TruckDriverName, TruckDriverName_Hindi, TruckNumberPlate @unique, Latitude?, Longitude? |
| `VoiceResponse` | cuid id, crop, market, quantity, Latitude?, Longitude?, createdAt |

**The role enum has only two values** — there is no FARMER role, despite the
landing page advertising three user types. This is a real gap Phase-B closes.

Python side uses `supabase.create_client` directly against the same tables.
`src/lib/supabaseClient.js` is instantiated but **imported nowhere**;
`@supabase/auth-ui-react` is likewise unused.

**Committed build artifacts:** the generated Prisma client is in git, including
~45 orphaned `query_engine-windows.dll.node.tmpNNNNN` binaries.

---

## 5. Security findings

| Finding | Severity | Action |
|---|---|---|
| `server/TruckRouteNavigator/.env` committed with live Supabase URL + anon JWT | **High** | Untracked in this branch; **rotation + history purge is yours** |
| TomTom key hardcoded at `app.py:184` | **High** | Replaced with env lookup; **rotate the old key** |
| Hardcoded `http://127.0.0.1:5000` and `http://localhost:3000` in app code | Medium | Moved to env in the new app |
| `debug=True` on the Flask app | Medium | Legacy only; FastAPI does not enable it |

Full detail and required manual steps: [SECURITY_ACTION_REQUIRED.md](SECURITY_ACTION_REQUIRED.md).

---

## 6. Classification

### RETAIN
- All 26 shadcn `ui/` primitives.
- `globals.css` design tokens and the lime-400 identity.
- `sections/` landing components (Hero, Features, Footer, Navbar).
- `assets/data/products.js` (~40 Hindi SKUs) as dealer seed material.
- `hooks/use-mobile.js`, `lib/utils.js`.

### REFACTOR
- `sections/SignupOptions.js` — good design, but hard-redirects to
  `127.0.0.1:5000`; becomes role onboarding.
- `components/dashboard/*` (AppSidebar, AppNavbar, ERPDashboard) — reusable
  shell, currently dealer-only and Kinde-coupled.
- `farmer/vehicle-request/page.js` — the crop/mandi/quantity idea is right; the
  implementation redirects to Flask.

### REPLACE
- `server/TruckRouteNavigator/app.py` → FastAPI + `RoutingService` + VB-QER.
- Folium server-rendered HTML → client-side map behind an adapter.
- `app/utils/db.js` (Prisma) → Mongo repositories.
- `api/voice-response/route.js` → `POST /api/v1/farmers/requests`.

### DEPRECATE (keep for reference, not in the active path)
- `prisma/schema.prisma`, `lib/supabaseClient.js`, Kinde handlers,
  `mandi.py`, `Qdelay.py` (superseded by `routing/quantum/`).

### REMOVE LATER (not in this run)
- Committed Prisma client + `.tmp` binaries.
- `static/js/*` dead scripts.
- `assets/data/faqs.js`, `integrations.js` (imported nowhere).

---

## 7. Missing

No tests of any kind on the application side. No CI. No Docker. No
`requirements.txt` for the Flask app. No error boundaries, loading states or
empty states. No i18n structure despite being a Hindi-first product. No
server-side role authorization — the role is read from the client.

---

## 8. Phase-A boundary

Phase-A artifacts are **inputs** to Phase-B, never rewritten by it:

```
Data/  Research/  Res/  metadata/   →  read-only research source of truth
   ↓ (validated loader)
MongoDB                             →  application serving layer
```

The application depends on exactly one optimization interface,
`VBQEROptimizer().solve()`, and never on Dijkstra, A*, OR-Tools, 2-opt,
simulated annealing, a QUBO solver, QAOA, IBM Quantum or an individual
quantum artifact.
