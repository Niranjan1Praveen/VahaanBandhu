# Legacy Migration Map

Every piece of the legacy application, classified. This is what makes the revamp
auditable rather than a rewrite that quietly dropped things.

**Classification:** `RETAIN` (unchanged) · `REFACTOR` (kept, reworked) ·
`REPLACE` (superseded) · `DEPRECATE` (still present, not in the active path) ·
`REMOVE LATER` (dead, deletion deferred)

---

## Frontend

| Path | Class | Disposition |
|---|---|---|
| `src/components/ui/*` (26 shadcn primitives) | **RETAIN** | Untouched. The new pages build on them. |
| `src/app/globals.css` | **RETAIN** | Design tokens are the product's visual identity. Not edited. |
| `src/sections/{Hero,Features,Footer,Navbar,Introduction}.js` | **RETAIN** | Landing page still renders these. |
| `src/assets/data/products.js` | **RETAIN** | ~40 Hindi SKUs; dealer seed material. |
| `src/hooks/use-mobile.js`, `src/lib/utils.js` | **RETAIN** | Used by the new shell. |
| `src/app/layout.js` | **REFACTOR** | `SessionProvider` added; `lang="en"` → `lang="hi"`. Fonts and metadata unchanged. |
| `src/sections/SignupOptions.js` | **REFACTOR** | Superseded in the flow by `/app/role`; the component still renders on the landing page. Its hard redirect to `127.0.0.1:5000` is no longer reachable. |
| `src/components/dashboard/{AppSidebar,AppNavbar,ERPDashboard}.js` | **DEPRECATE** | Dealer-only and Kinde-coupled. Replaced by `components/app/Shell.jsx`. Left in place for reference. |
| `src/app/(dashboard)/input-dealer/*` | **DEPRECATE** | Superseded by `/app/dealer`. Still routable. |
| `src/app/farmer/vehicle-request/page.js` | **REPLACE** | Superseded by `/app/farmer`. The crop/mandi/quantity idea survives; the Flask redirect does not. |
| `src/app/api/auth/[kindeAuth]/route.js` | **DEPRECATE** | Kinde catch-all. Not in any active path. |
| `src/app/api/auth/creation/route.js` | **DEPRECATE** | Post-login Prisma upsert + hardcoded redirect. Replaced by `POST /api/v1/me/role`. |
| `src/app/api/voice-response/route.js` | **REPLACE** | Replaced by `POST /api/v1/farmers/requests`. |
| `src/app/utils/db.js` | **REPLACE** | Prisma client → Mongo repositories. |
| `src/lib/supabaseClient.js` | **REMOVE LATER** | Instantiated but imported nowhere, even before Phase-B. |
| `src/assets/data/{faqs,integrations}.js` | **REMOVE LATER** | Imported nowhere. |
| `src/generated/prisma/**` | **REMOVE LATER** | Committed build output, including ~45 orphaned `.tmp` DLL binaries. Deleting is noisy; deferred deliberately. |

### New

`src/lib/api.js` · `src/lib/i18n.js` · `src/components/providers/SessionProvider.jsx` ·
`src/components/app/Shell.jsx` · `src/components/map/RouteMap.jsx` ·
`src/app/signin/` · `src/app/app/{page,role,farmer,trucker,dealer,map}/`

---

## Backend

| Path | Class | Disposition |
|---|---|---|
| `server/TruckRouteNavigator/app.py` | **REPLACE** | ~570 lines: nearest-truck haversine, TomTom call, quantum delay model, Folium HTML render. Split into `RoutingService`, the trucker matching endpoints and `RouteMap`. **Still runnable**; not in the active path. |
| `server/TruckRouteNavigator/mandi.py` | **DEPRECATE** | Standalone Folium map on port 5002. Superseded by `GET /api/v1/mandis` + client map. |
| `server/TruckRouteNavigator/Qdelay.py` | **DEPRECATE** | 5-qubit Ry/Rx delay model on `BasicSimulator`. Superseded by `routing/quantum/`. |
| `server/TruckRouteNavigator/static/js/{track_driver,route_to_mandi}.js` | **REMOVE LATER** | Call `POST /get-route` and `GET /update-trucks` — endpoints that never existed. |
| `server/TruckRouteNavigator/.env` | **UNTRACKED** | Removed from git tracking. Local file preserved. **Rotation is manual** — see `SECURITY_ACTION_REQUIRED.md`. |
| `gps_simulation.cpython-312.pyc` | **REMOVE LATER** | Compiled artifact with no source. |

### New

`server/app/` — `main.py`, `core/{config,security,logging}.py`,
`db/{mongodb,redis_cache,seed}.py`, `schemas/{common,routing}.py`,
`repositories/{user_repo,transport_repo}.py`,
`services/{routing_service,quantity_service}.py`,
`api/routes/{health,me,farmers,truckers,dealers,routing,live_routing,locations}.py`

---

## Database

| Legacy (Prisma/Postgres) | New (MongoDB) | Note |
|---|---|---|
| `User` | `users` | **Role enum extended.** Legacy had only `DRIVER` and `INPUTDEALER` — no farmer, despite the landing page advertising three user types. Now `FARMER` / `TRUCKER` / `INPUT_DEALER`, with role-specific profile data embedded. |
| `MandiLatLong` | `mandis` + `locations` | Split: `locations` is the geospatial master, `mandis` carries market attributes. Both gain a `geo` GeoJSON field and a 2dsphere index. |
| `Truck` | `vehicles` | Gains `owner_user_id`, `capacity_kg`, `available`, `geo`. |
| `VoiceResponse` | `transport_requests` | Substantially extended: normalized quantity, conversion confidence, clarification prompt, status + history, language, input mode. |
| — | `dealer_requirements` | New. No legacy equivalent. |
| — | `route_results` | New. Immutable optimization records with version provenance. |
| — | `crops` | New. Crop ontology from Phase-A. |
| — | `truck_availability` | New. TTL-expiring ephemeral state. |
| `prisma/schema.prisma` | **DEPRECATE** | Retained as the migration reference. |

---

## Active vs legacy, after Phase-B

```
ACTIVE                              LEGACY (present, not serving)
------                              ----------------------------
FastAPI  (server/app)               Flask   (server/TruckRouteNavigator)
MongoDB                             Supabase / Postgres / Prisma
Clerk architecture + dev auth       Kinde
Redis                               —
VB-QER                              inline optimization in app.py
Leaflet + TomTom behind an adapter  Folium server-rendered HTML
```

**No Next.js route calls Flask.** **No new feature touches Supabase.** Both were
verified by grepping the active source tree.

---

## Deferred deletions, and why

Nothing was deleted in this run. Everything above marked `REMOVE LATER` is dead,
but removing it would have produced a large diff competing for review attention
with the migration itself, and the legacy Flask app remains a useful reference
while the FastAPI replacement is still young.

Suggested order once the new stack is trusted:

1. `src/generated/prisma/**` and the `.tmp` DLL binaries (largest, zero risk)
2. `static/js/*` dead scripts and the orphaned `.pyc`
3. `supabaseClient.js`, `faqs.js`, `integrations.js`
4. The Kinde route handlers
5. `server/TruckRouteNavigator/` in full, once nothing references it
