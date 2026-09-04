# Supabase/Postgres/Prisma → MongoDB

**Status: complete for the active application.** No new feature touches Supabase.
The Prisma schema is retained as a migration reference, not as a runtime
dependency.

---

## 1. Why MongoDB, used as MongoDB

The temptation with a Postgres→Mongo move is to translate tables into
collections one-for-one and keep writing SQL-shaped queries. That would inherit
the relational structure without the relational guarantees — the worst of both.

The design decisions that actually differ:

| Decision | Where | Why |
|---|---|---|
| **Embed** role profile inside `users` | `users.profile` | Always read with the user, never queried independently, small and bounded. |
| **Reference** locations, mandis, vehicles | `location_id`, `mandi_id`, `vehicle_id` | Shared across many documents; embedding would duplicate and drift. |
| **GeoJSON + 2dsphere** | `locations`, `mandis`, `vehicles`, `transport_requests.origin`, `dealer_requirements.delivery_location` | `$near` is the return-load matching query. Postgres would have needed PostGIS. |
| **TTL index** | `truck_availability.expires_at` | Availability is ephemeral. Mongo expires it; no cleanup job. |
| **Immutable append** | `route_results` | An optimization result is a record of what the system decided, with the model version that decided it. Never updated in place. |
| **Embedded status history** | `transport_requests.status_history` | Read with the request, bounded by workflow length. A join table would be pure overhead. |

**Coordinate order.** GeoJSON is `[longitude, latitude]` — the reverse of how
every other part of this codebase writes coordinates. Getting it backwards puts
every Haryana point in the Indian Ocean, silently, with `$near` returning
nothing. `to_geojson(lat, lon)` in `server/app/db/mongodb.py` is the single place
that swaps them, and the ordering is commented at both the definition and each
call site.

---

## 2. Entity mapping

### `User` → `users`

| Prisma field | Mongo field | Conversion |
|---|---|---|
| `id` (String @id) | `clerk_user_id` | Now the Clerk subject; unique + sparse index |
| `email` | `email` | unique + sparse |
| `firstName`, `lastName` | `first_name`, `last_name` | direct |
| `profileImage` | `profile_image` | direct |
| `createdAt` | `created_at` | `DateTime` → BSON date |
| `role` (enum) | `role` (string) | **see below** |
| — | `profile` (embedded object) | new; role-specific fields |
| — | `onboarded_at` | new |

**The role enum changed, and this is the substantive difference.** Legacy Prisma:

```prisma
enum Role { DRIVER, INPUTDEALER }   // @default(DRIVER)
```

There was **no farmer role**, despite the landing page advertising three user
types and the whole product thesis starting with a farmer. New:

```
FARMER · TRUCKER · INPUT_DEALER
```

`DRIVER` → `TRUCKER`, `INPUTDEALER` → `INPUT_DEALER`, and `FARMER` is new. There
is also **no default**: `role` starts null and onboarding must set it, so a user
cannot silently end up in the wrong experience.

### `MandiLatLong` → `locations` + `mandis`

Split deliberately. `locations` is the geospatial master shared by villages,
depots, shops and mandis; `mandis` carries market-specific attributes.

| Prisma | Mongo | Conversion |
|---|---|---|
| `State` | `locations.state`, `state_code` | direct |
| `Mandi` | `locations.name_en` / `mandis.apmc_name` | direct |
| `Mandi_Hindi` | `locations.name_hi` | direct |
| `Latitude`, `Longitude` (Float?) | `latitude`, `longitude` + `geo` | nullable → required; a location without coordinates is not loaded |
| — | `mandis.coordinate_verified` | new; Phase-A honesty flag — real market name, approximate coordinate |
| — | `mandis.enam_enabled`, `market_yard_type`, `avg_queue_min` | from Phase-A masters |

### `Truck` → `vehicles`

| Prisma | Mongo | Conversion |
|---|---|---|
| `TruckNumberPlate` (@unique) | `vehicle_number` | no longer globally unique; scoped to owner |
| `TruckDriverName`, `_Hindi` | — | **dropped**; the driver is a `users` document now |
| `Latitude`, `Longitude` | `latitude`, `longitude` + `geo` | + 2dsphere |
| — | `owner_user_id`, `capacity_kg`, `vehicle_class`, `available` | new; capacity is what makes matching possible at all |

### `VoiceResponse` → `transport_requests`

The largest expansion. Legacy stored a raw utterance and three strings.

| Prisma | Mongo | Conversion |
|---|---|---|
| `id` (cuid) | `request_id` (`REQ_…`) | prefixed id |
| `crop` (String) | `crop_key` + `crop_label` | canonical key separated from display text |
| `market` (String) | `mandi_id` + `mandi_label` | resolved to an id where possible |
| `quantity` (String) | `quantity_value` + `quantity_unit` + `quantity_kg` | **see below** |
| `Latitude`, `Longitude` | `origin.{latitude,longitude,geo}` | + 2dsphere |
| — | `conversion_confidence`, `conversion_source`, `bag_weight_kg_used` | new |
| — | `needs_clarification`, `clarification_prompt` | new |
| — | `status`, `status_history` | new; validated transitions |
| — | `language`, `input_mode`, `raw_utterance` | new |

**Quantity is the important one.** Legacy stored `quantity` as a free string —
`"20 बोरी"` — with no normalization at all. The new model preserves the user's
own words *and* the normalization, and `quantity_kg` is **null** when the
conversion cannot be justified. A bori is not assumed to be 50 kg.

### New collections, no legacy equivalent

`dealer_requirements` · `route_results` · `crops` · `truck_availability`

---

## 3. Indexes

24 across 9 collections, created idempotently by `ensure_indexes()` at startup.

| Collection | Index | Purpose |
|---|---|---|
| `users` | `clerk_user_id` unique sparse | identity lookup on every authenticated request |
| `users` | `email` unique sparse | uniqueness without blocking null emails |
| `locations` | `geo` 2dsphere | "mandis near me" |
| `locations` | `name_en` + `name_hi` text | bilingual search |
| `locations` | `location_type` + `district` | filtered listings |
| `mandis` | `geo` 2dsphere | return-load candidate search |
| `vehicles` | `district` + `capacity_kg` | matching by region and size |
| `transport_requests` | `requester_user_id` + `created_at` desc | "my requests" |
| `transport_requests` | `origin.geo` 2dsphere | pickup proximity |
| `dealer_requirements` | `delivery_location.geo` 2dsphere | **the circular-logistics query** |
| `route_results` | `vbqer_version` + `cost_snapshot_id` | version-aware retrieval |
| `truck_availability` | `expires_at` TTL 0 | self-expiring availability |

`sparse` on the unique indexes matters: without it, two users with no email
would collide on a null value.

---

## 4. Loading Phase-A data

```
Data/master/*.csv   (research source of truth, read-only)
        ↓  server/app/db/seed.py
MongoDB             (serving layer, rebuildable)
```

One-way by design. The compose file mounts `./Data` and `./Res` **read-only**,
so the application cannot modify research artifacts even by accident.

Loaded subset: 1,320 locations (all mandis and depots, plus a village and shop
sample), 50 mandis, 18 crops. The full Phase-A graph is 376k route edges —
loading it into the application database would serve no purpose, since routing
reads it through `OfflineGraphProvider` or TomTom.

```bash
python -m server.app.db.seed --reset
```

---

## 5. Migrating real legacy data

**No Supabase project was contacted during this run**, per the local-only
constraint. The tooling is prepared, not executed.

The path when you want it:

```
Supabase export (CSV or pg_dump)
        ↓
map columns per the tables above
        ↓
validate: coordinates in-region, roles mapped, quantities parsed
        ↓
insert with the same `to_geojson()` helper
```

Two things that will need decisions on real data:

1. **`VoiceResponse.quantity` is a free string.** Parsing `"20 बोरी"` into
   value + unit will partially fail. Failures must land in `needs_clarification`,
   not in a guessed kilogram figure.
2. **Legacy users have no farmer role.** Every existing `DRIVER` maps to
   `TRUCKER`, but there is no way to know which of them were actually farmers
   using the wrong account type. They will need to re-onboard.

---

## 6. What still references the legacy stack

| Item | Status |
|---|---|
| `client/prisma/schema.prisma` | Retained as reference. Not read at runtime. |
| `package.json` `postinstall: prisma generate` | Still runs. Kept so the legacy path stays runnable; the Docker web image copies the schema before install for this reason. |
| `client/src/generated/prisma/**` | Committed build output. `REMOVE LATER`. |
| `client/src/lib/supabaseClient.js` | Instantiated, imported nowhere — true before Phase-B too. |
| `server/TruckRouteNavigator/*.py` | Uses `supabase.create_client`. Legacy Flask, not in the active path. |

**Verified:** no file under `server/app/` or `client/src/app/app/` imports
Prisma, Supabase or `@supabase/*`.
