# Data Dictionary

**VahaanBandhu 2.0 · Phase-A · dataset `v0.1` (prototype stage)**

Every table below is written by [`vb/pipeline.py`](../vb/pipeline.py) and validated by
[`vb/validate/schemas.py`](../vb/validate/schemas.py). Row counts are for the prototype
stage; see `metadata/manifests/v0.1_prototype.json` for exact counts, column lists and
file hashes of the current build.

## Relational model

```
locations_master (spatial spine, one ID space)
   |-- mandis            (location_id)        -- mandi_commodities -- crops
   |-- shops             (location_id)
   |-- farmer_nodes      (village_location_id)
   |-- trucks            (home_location_id)   -- truck_availability
   |-- route_edges       (origin_location_id, destination_location_id) -- scenarios
   |
transport_requests (requester_id -> farmer_nodes | shops)
   |-- instance_requests -- route_instances -- route_solutions
```

Two rules the model exists to enforce:

- **One ID space.** Villages, mandis, shops, depots and warehouses all resolve to a
  `location_id` in `locations_master`, so route edges and optimization instances never
  deal in mixed identifier types.
- **Junction tables, not delimited cells.** `mandi_commodities` and `instance_requests`
  are real tables so their foreign keys can actually be validated.

---

## `Data/master/locations_master.csv` — 3,442 rows · mixed provenance

The spatial spine. Contains real mandis and synthetic villages, depots and shops, each
flagged.

| Column | Type | Description |
|---|---|---|
| `location_id` | str `LOC_…` | **PK.** Content-derived, stable across regeneration. |
| `location_type` | enum | `village` \| `mandi` \| `shop` \| `depot` \| `parking` \| `hub` \| `warehouse` |
| `name_en` | str | English/transliterated name |
| `name_hi` | str | Devanagari name |
| `state` | str | Full state name |
| `state_code` | enum | `DL` \| `HR` \| `PB` \| `UP` |
| `district` | str | District name (real) |
| `district_code` | str `VB-…` | **Internal code.** `VB-` prefixed so it can never be mistaken for an official LGD/Census code. |
| `subdistrict`, `subdistrict_code` | str | **NULL throughout** — LGD not acquired |
| `village_town` | str | Settlement name |
| `village_town_code` | str | **NULL throughout** — LGD not acquired |
| `pincode` | str | **NULL throughout** — not acquired |
| `latitude` | float64 | WGS84 / EPSG:4326 decimal degrees |
| `longitude` | float64 | WGS84 / EPSG:4326 decimal degrees |
| `geocode_precision` | enum | `exact` \| `rooftop` \| `street` \| `settlement` \| `district_centroid` \| `synthetic_envelope` \| `unknown` |
| `source_id` | str | FK → `source_registry.csv` |
| `source_object_id` | str | Key within the source system, where one exists |
| `is_synthetic` | bool | Generated rather than observed |
| `confidence_score` | float 0–1 | Real-world confidence. **Schema-enforced to 0.0 when `is_synthetic`.** |
| `verified_at` | timestamp | Verification against a source. **NULL throughout Phase-A.** |
| `dataset_version` | str | Release version |
| `in_ncr` | bool | **Explicit NCR membership.** Never inferred from `state_code`. |

## `Data/master/mandis.csv` — 50 rows · mixed provenance

Real market names, approximate town-level coordinates.

| Column | Type | Description |
|---|---|---|
| `mandi_id` | str `MND_…` | **PK** |
| `location_id` | str | FK → `locations_master` |
| `apmc_name` | str | Market name (real) |
| `market_yard_type` | enum | `main` \| `sub-yard` \| `private` \| `other` |
| `enam_enabled` | bool | **Plausible assignment from the curated reference, NOT a verified e-NAM status.** |
| `commodities_supported` | int | Count; the relation itself lives in `mandi_commodities` |
| `opening_days` | str | Comma-separated day abbreviations |
| `service_start`, `service_end` | str `HH:MM` | Yard operating window |
| `avg_queue_min` | int | Mean gate queue, scaled by market size |
| `market_scale` | enum | `terminal` \| `large` \| `medium` \| `small` |
| `coordinate_verified` | bool | **`False` throughout.** Schema fails the build if ever `True` without a cited source. |
| `source_id` | str | `SRC_CURATED_REF` |
| `is_synthetic` | bool | `False` — the market is real, only its coordinate is approximate |

## `Data/master/mandi_commodities.csv` — ~383 rows

Junction: `mandi_id` × `crop_id` (+ `crop_key`, `dataset_version`).

## `Data/master/crops.csv` — 18 rows · verified ontology

| Column | Type | Description |
|---|---|---|
| `crop_id` | str `CRP_…` | **PK** |
| `crop_key` | str | Canonical snake_case key used as the NLU label |
| `name_en`, `name_hi` | str | Canonical display names |
| `aliases_en`, `aliases_hi` | str `\|`-joined | **Training aliases only.** Includes transliterations, regional names, misspellings and ASR corruptions. Must never be written into a canonical field. |
| `default_unit` | enum | `kg` \| `bori` \| `quintal` \| `tonne` |
| `default_bag_weight_kg` | float \| NULL | Crop-typical bori weight. **NULL where the crop is not bagged** (e.g. sugarcane), which forces an unresolved conversion. |
| `density_or_handling_class` | str | `granular_bagged`, `pulse_bagged`, `oilseed_bagged`, `perishable_bagged`, `perishable_crate`, `fibre_baled`, `bulk_loose` |
| `season_kharif_rabi_zaid` | enum | `kharif` \| `rabi` \| `zaid` \| `perennial` |
| `states` | str | `\|`-joined state codes where commonly marketed |

## `Data/master/scenarios.csv` — 8 rows

Time-dependent cost scenarios. `SCN_BASELINE` is the free-flow reference and is
**never overwritten**; every other scenario is a separate set of edge rows.

| `scenario_id` | traffic ×| risk × | Meaning |
|---|---|---|---|
| `SCN_BASELINE` | 1.00 | 1.00 | Free-flow reference |
| `SCN_MORNING_PEAK` | 1.45 | 1.10 | Weekday 07:00–10:00 |
| `SCN_MIDDAY` | 1.12 | 1.00 | Weekday 11:00–16:00 |
| `SCN_EVENING_PEAK` | 1.52 | 1.14 | Weekday 17:00–20:00 |
| `SCN_NIGHT` | 0.88 | 1.25 | 22:00–05:00; faster but riskier |
| `SCN_WEEKEND` | 1.05 | 1.00 | Saturday/Sunday |
| `SCN_HARVEST_PEAK` | 1.38 | 1.08 | Rabi/Kharif arrival surge |
| `SCN_MONSOON_RAIN` | 1.34 | 1.60 | Active rain |

---

## `Data/synthetic/shops.csv` — 900 rows · fully synthetic

| Column | Type | Description |
|---|---|---|
| `shop_id` | str `SHP_…` | **PK** |
| `location_id` | str | FK → `locations_master` |
| `shop_category` | enum | `cement` \| `tmt` \| `hardware` \| `brick` \| `pipe` \| `electrical` \| `paint` \| `tile` \| `sanitary` \| `roofing` \| `multi` |
| `capacity_tonnes` | float | Stock held, by category profile |
| `daily_demand_kg` | float | Throughput; scales with district urbanisation |
| `loading_service_min` | int | Truck unloading dwell time |
| `vehicle_access` | enum | `LCV` \| `2-axle` \| `3-axle` \| `heavy` — largest vehicle that can reach it |
| `road_access_quality` | float 0–1 | Approach-road quality prior |
| `anchor_village_location_id` | str | Settlement the shop was placed against |
| `generation_method` | str | `demand_surface_anchored_v1` |
| `is_synthetic` | bool | Always `True` |

## `Data/synthetic/farmer_nodes.csv` — 1,400 rows · fully synthetic

**Privacy design:** a farmer node is a *pickup point*, not a person and not a home. Nodes
sit on an agricultural envelope 0.4–3.5 km outside the settlement core. There are no
names, phone numbers or household identifiers, and none may be added.

| Column | Type | Description |
|---|---|---|
| `farmer_node_id` | str `FRM_…` | **PK** |
| `village_location_id` | str | FK → `locations_master` |
| `latitude`, `longitude` | float64 | WGS84; agricultural envelope, never a residence |
| `farm_size_ha` | float | Lognormal, right-skewed as in north India |
| `primary_crop_id` / `_key` | str | FK → `crops` |
| `secondary_crop_id` / `_key` | str \| NULL | Optional second crop |
| `market_preference_mandi_id` | str | FK → `mandis`; nearest 80% of the time |
| `road_access_km` | float | Distance to a usable road |
| `generation_method` | str | `agri_envelope_ring_v1` |

## `Data/synthetic/trucks.csv` — 600 rows · fully synthetic

| Column | Type | Description |
|---|---|---|
| `truck_id` | str `TRK_…` | **PK** |
| `home_location_id` | str | FK → depot in `locations_master` |
| `driver_name_en` / `_hi` | str | Synthetic display name |
| `vehicle_class` | enum | `pickup` \| `LCV` \| `2axle` \| `3axle` \| `multi_axle` |
| `capacity_kg` | float | Constrained by class |
| `capacity_bori` | int | Convenience figure at a nominal 50 kg/bori. **Not an authoritative conversion** — see `vb.units`. |
| `body_type` | enum | `open` \| `closed` \| `refrigerated` \| `tipper`; restricted per class |
| `fuel_type` | enum | `diesel` \| `cng` \| `ev` \| `other`; EV/CNG only at the light end |
| `avg_kmpl` | float | Constrained by class — schema rejects heavy trucks with light-vehicle economy |
| `max_route_km` | float | Operating range; capped at 160 km for EVs |
| `available_from`, `available_to` | str `HH:MM` | Daily window |

## `Data/synthetic/truck_availability.csv` — ~1,222 rows

`availability_id` (PK), `truck_id`, `location_id`, `available_time`,
`remaining_capacity_kg`, `preferred_radius_km`, `return_home_by`. A truck may appear
multiple times with different remaining capacity — this is what lets the matcher find
**partial** return loads.

## `Data/synthetic/transport_requests.csv` — 18,000 rows · fully synthetic

Carries both the logistics request and its natural-language surface form.

### Request fields

| Column | Type | Description |
|---|---|---|
| `request_id` | str `REQ_…` | **PK** |
| `requester_type` | enum | `farmer` \| `shop` |
| `requester_id` | str | FK → `farmer_nodes` or `shops` |
| `origin_location_id` | str | FK → `locations_master` |
| `destination_mandi_id` | str \| NULL | Set for farmer requests |
| `destination_shop_id` | str \| NULL | Set for shop replenishment |
| `crop_id` / `crop_key` | str \| NULL | NULL for building-material requests |
| `pickup_earliest`, `pickup_latest`, `delivery_latest` | ISO ts | Time windows |
| `priority` | enum | `low` \| `normal` \| `high` |
| `district`, `state_code`, `request_date` | — | Used for geographic and temporal splits |

### Quantity fields — the important ones

| Column | Type | Description |
|---|---|---|
| `quantity_value` | float | **As stated by the user.** Never overwritten. |
| `quantity_unit` | enum | `kg` \| `bori` \| `quintal` \| `tonne` — as stated |
| `quantity_kg` | float \| **NULL** | Derived. **NULL when the conversion cannot be justified.** |
| `bag_weight_kg_used` | float \| NULL | Which bori weight was applied, if any |
| `conversion_source` | str | e.g. `definitional`, `crop_default:wheat`, `no_bag_weight_available` |
| `conversion_confidence` | enum | `exact` \| `crop_default` \| `regional_default` \| **`unresolved`** |

**The rule:** `conversion_confidence = unresolved` ⟺ `quantity_kg IS NULL`. Enforced by
schema in both directions. A `bori` quantity with no determinable bag weight is never
silently filled with 50 kg, and never becomes `0`.

### NLU fields

| Column | Type | Description |
|---|---|---|
| `input_language` | enum | `hi` \| `en` \| `hinglish` |
| `input_mode` | enum | `voice` \| `text` (voice carries more noise) |
| `raw_utterance` | str | Surface form, possibly corrupted or incomplete |
| `template_family` | str `TF_…` | Sentence shape. **Splits hold out whole families.** |
| `label_crop_key` | str \| NULL | **Canonical label** — never an alias |
| `label_mandi_key` | str \| NULL | **Canonical label** — never an alias |
| `label_quantity_value` / `_unit` | — | Canonical labels |
| `parsed_crop_conf`, `parsed_mandi_conf`, `parsed_quantity_conf` | float 0–1 | Per-slot confidence; `0.0` when the field was dropped |
| `is_incomplete`, `missing_field` | bool, str | Deliberately incomplete inputs |

### Feasibility

| Column | Values |
|---|---|
| `feasibility_label` | `feasible` \| `ambiguous` \| `infeasible` \| `unresolved_quantity` |
| `infeasible_reason` | `exceeds_max_fleet_capacity`, `non_positive_quantity`, `missing_<field>`, or the conversion source |

Hard negatives are **labelled, not dropped**. A matcher that has never seen an
over-capacity load or an unresolvable quantity will fail the first time a user produces one.

### Split

`split` (`train` \| `validation` \| `test`) and `split_reason`
(`random_bucket`, `holdout_template_family`, `holdout_time`, `holdout_district`,
`duplicate_of_test_utterance`).

## `Data/synthetic/route_edges.csv` — 375,968 rows · fully synthetic

**Directed.** A→B and B→A are separate rows with separate IDs.

| Column | Type | Description |
|---|---|---|
| `edge_id` | str `EDG_…` | Content hash of (origin, destination, scenario) |
| `origin_location_id`, `destination_location_id` | str | FK → `locations_master` |
| `distance_km` | float | **Road distance estimate** via a length-dependent detour factor |
| `haversine_km` | float | Great-circle distance, retained as a QA lower bound and feature — **never used as road distance** |
| `freeflow_time_min`, `traffic_time_min` | float | Uncongested and scenario-adjusted |
| `road_class_mix` | enum | `highway_dominant` \| `mixed` \| `rural_dominant` |
| `toll_cost_inr`, `fuel_cost_inr` | float | Derived from highway share and distance |
| `truck_accessible` | bool | Passable by a loaded truck |
| `surface_risk_score` | float | Road-condition risk, scaled per scenario |
| `source` | str | `offline_detour_model_v1` — **not** a routing-API response |
| `snapshot_time` | ts | Cost snapshot timestamp |
| `scenario_id` | str | FK → `scenarios` |

## `Data/synthetic/route_instances.csv` — 2,000 rows

The canonical optimization problem statement. **Every solver consumes this.**

| Column | Type | Description |
|---|---|---|
| `instance_id` | str `INS_…` | **PK** |
| `instance_hash` | str | **Permutation-invariant** structural fingerprint. Splits key on this so the same problem cannot land on both sides. |
| `problem_type` | enum | `TSP` \| `CVRP` \| `VRPTW` \| `PDP` \| `CIRCULAR_VRP` |
| `size_band` | enum | `quantum` (3–7) \| `small` (8–14) \| `medium` (15–30) \| `large` (31–60) |
| `depot_location_id` | str | FK → depot |
| `n_customers`, `n_vehicles` | int | Problem size |
| `truck_ids` | str `\|`-joined | Assigned fleet |
| `capacity_constraint` | float | Smallest assigned vehicle capacity |
| `fleet_capacity_kg`, `total_demand_kg`, `capacity_feasible` | — | Feasibility guard |
| `time_window_constraint`, `pickup_delivery_constraint`, `circular_return_constraint` | bool | Active constraints |
| `objective_weights_json` | str | **Weights stored in data, never hard-coded in a solver** |
| `cost_snapshot_id` | str `CST_…` | **The load-bearing field.** Two results are comparable only if they carry the same value. |
| `scenario_id`, `graph_version`, `dataset_version` | str | Provenance |
| `quantum_ready` | bool | Encodable within the qubit budget (≤3 customers, 1 vehicle) |
| `estimated_qubits_permutation` | int | `(n_customers + 1)²` |
| `split`, `split_reason` | str | Leakage-safe assignment |

## `Data/synthetic/instance_requests.csv` — ~37,101 rows

Junction: `instance_id`, `request_id`, `node_order`, `demand_kg`. `node_order` fixes the
node indexing so a solution's stop indices mean the same thing to every solver.

## `route_solutions` (schema defined; populated by benchmark runs)

Written to `Res/benchmarks/`. Columns: `solution_id`, `instance_id`, `algorithm_family`
(`classical` \| `quantum` \| `hybrid`), `algorithm_name`, `hyperparameters_json`,
`ordered_stops`, `total_distance_km`, `total_time_min`, `empty_distance_km`,
`total_cost_inr`, `objective_value`, `feasible`, `constraint_violations`,
**decomposed runtime** (`classical_preprocess_ms`, `solver_runtime_ms`,
`quantum_execution_ms`, `queue_wait_ms`, `classical_postprocess_ms`, `wall_clock_ms`),
`optimality_gap`, `feasible_rate`, `shots`, `quantum_qubits`, `quantum_depth`,
`quantum_backend`, `qubo_version`, `encoding_version`, `seed`, `cost_snapshot_id`.

Quantum-only fields are **NULL for classical rows**, not zero-filled, so "not applicable"
is distinguishable from "measured zero".

## `Data/source_registry.csv` — 7 rows

`source_id`, `source_name`, `source_url`, `organization`, `retrieved_at`, `status`,
`license_or_terms`, `geography`, `fields_used`, `raw_file_hash`,
`ml_training_permitted`, `notes`. See [DATA_SOURCES.md](DATA_SOURCES.md).

---

## Conventions

- **CRS:** WGS84 / EPSG:4326 decimal degrees in all canonical tables. EPSG:32644 (UTM 44N)
  is used only inside derived metric computation and never replaces the canonical values.
- **IDs:** `PREFIX_<12 hex>`, derived from record content so regeneration is join-stable.
- **Encoding:** UTF-8 throughout; Devanagari is stored natively.
- **Nulls:** A NULL means *unknown*, never zero. This is load-bearing for `quantity_kg`
  and for the LGD code columns.
