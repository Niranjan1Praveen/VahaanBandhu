# Data QA Report

**VahaanBandhu · the routing research · dataset `v0.1` (prototype stage)**

Generated: `2026-09-03T05:06:46.944570+00:00`

This report is **generated from the validators**, not written by hand, so it
cannot drift from what was actually measured. Regenerate with
`python tools/build_qa_report.py`. Raw outputs are in `Data/qa/`.

## Overall result: PASS

| Suite | Result |
|---|---|
| Schema validation | **PASS** |
| Geospatial QA | **PASS** |
| Referential integrity | **PASS** |
| Statistical QA | **PASS** |
| Leakage QA | **PASS** |

## 1. Schema validation

Schemas encode project rules, not just types: a synthetic row may not carry a
non-zero real-world confidence; an unresolved quantity may not have a kilogram
value; a directed edge may not be a self-loop or shorter than the geodesic.

| Table | Result | Failure cases |
|---|---|---|
| `locations_master` | **PASS** | 0 |
| `mandis` | **PASS** | 0 |
| `shops` | **PASS** | 0 |
| `farmer_nodes` | **PASS** | 0 |
| `trucks` | **PASS** | 0 |
| `transport_requests` | **PASS** | 0 |
| `route_edges` | **PASS** | 0 |
| `route_instances` | **PASS** | 0 |

## 2. Geospatial QA

| Check | Value | Requirement |
|---|---|---|
| Locations checked | 3,442 | — |
| Outside coarse project bbox | 0 | 0 |
| Outside district envelope | 7 | flagged |
| Duplicate coordinates | 80 | flagged |
| NCR flag mismatches | 0 | 0 |
| Route edges | 375,968 | — |
| Edges shorter than geodesic | 0 | 0 |
| Self-loop edges | 0 | 0 |
| Bidirectional pairs | 40,258 | — |
| Mean directional asymmetry (km) | 0.9696 | > 0 |
| Envelope distance p50 (km) | 16.89 | — |
| Envelope distance p99 (km) | 33.25 | — |

### Coarse bounding box — a correction to the spec

The the routing research brief suggested a coarse rejection box of 23.0–31.5 N. **That upper
bound is too tight.** It excludes Gurdaspur (~32.04 N) and Pathankot (~32.27 N),
which are genuine Punjab districts, and rejected 176 valid locations plus 68
farmer nodes on the first validation run. The box was widened to 23.0–32.6 N.

### Known limitation: containment method

Method: `circular_district_envelope`

> No boundary polygons available in the routing research. A point just across a real district border will not be detected. the application must use LGD polygons.

## 3. Referential integrity

| Foreign key | Dangling references |
|---|---|
| `mandis` → `location_id_missing` | 0 |
| `shops` → `location_id_missing` | 0 |
| `farmer_nodes` → `village_location_id_missing` | 0 |
| `trucks` → `home_location_id_missing` | 0 |
| `route_edges` → `origin_missing` | 0 |
| `route_edges` → `destination_missing` | 0 |
| `route_instances` → `depot_missing` | 0 |
| `requests` → `destination_mandi_missing` | 0 |
| `farmer_nodes` → `market_preference_missing` | 0 |
| `instance_requests` → `request_missing` | 0 |
| `instance_requests` → `instance_missing` | 0 |

## 4. Statistical QA

### Impossible-value checks (all must be zero)

| Check | Count |
|---|---|
| `non_positive_quantity` | 0 |
| `negative_farm_size` | 0 |
| `zero_capacity_trucks` | 0 |
| `implausible_speed_over_120kmph` | 0 |

### Distributions

**Requests by state**

| Value | Count |
|---|---|
| `UP` | 7,828 |
| `PB` | 5,664 |
| `HR` | 4,390 |
| `DL` | 118 |

**Requests by language**

| Value | Count |
|---|---|
| `hinglish` | 9,837 |
| `hi` | 5,003 |
| `en` | 3,160 |

**Requests by input mode**

| Value | Count |
|---|---|
| `text` | 11,124 |
| `voice` | 6,876 |

**Requests by feasibility**

| Value | Count |
|---|---|
| `feasible` | 14,962 |
| `unresolved_quantity` | 1,208 |
| `ambiguous` | 1,124 |
| `infeasible` | 706 |

**Quantity unit as stated**

| Value | Count |
|---|---|
| `quintal` | 4,973 |
| `bori` | 4,680 |
| `tonne` | 4,225 |
| `kg` | 4,122 |

**Quantity conversion confidence**

| Value | Count |
|---|---|
| `exact` | 13,320 |
| `crop_default` | 3,472 |
| `unresolved` | 1,208 |

**Trucks by class**

| Value | Count |
|---|---|
| `LCV` | 179 |
| `2axle` | 161 |
| `3axle` | 112 |
| `pickup` | 107 |
| `multi_axle` | 41 |

**Trucks by fuel**

| Value | Count |
|---|---|
| `diesel` | 489 |
| `cng` | 91 |
| `ev` | 20 |

**Shops by category**

| Value | Count |
|---|---|
| `multi` | 216 |
| `cement` | 124 |
| `hardware` | 124 |
| `brick` | 92 |
| `tmt` | 90 |
| `paint` | 66 |
| `electrical` | 59 |
| `pipe` | 55 |
| `tile` | 38 |
| `sanitary` | 25 |
| `roofing` | 11 |

### Numeric ranges

| Metric | min | p50 | p95 | max |
|---|---|---|---|---|
| Request quantity (kg) | 80 | 3,380 | 3e+04 | 4e+04 |
| Truck capacity (kg) | 710 | 6,500 | — | 3.198e+04 |
| Farm size (ha) | — | 1.48 | 5.331 | 25.23 |
| Baseline edge distance (km) | — | 10.12 | 116.4 | 221 |

Median implied speed across baseline edges: **46 km/h** — plausible for mixed rural/highway truck movement.

## 5. Leakage QA

Random row splitting is wrong for this dataset in four independent ways. Each
violation count below must be zero.

| Check | Value |
|---|---|
| `request_id_overlap` | 0 |
| `holdout_families_leaked_into_train` | none |
| `holdout_districts_leaked_into_train` | none |
| `holdout_districts_in_train_instances` | none |
| `instance_hash_overlap` | 0 |
| `duplicate_utterances_across_split` | 0 |
| `passed` | **PASS** |

### Note on the duplicate-utterance promotion

The district and time holdouts can pull one instance of a repeated utterance into
test while an identical sentence stays in train. Before the final promotion pass
was added, **149 verbatim duplicates straddled the split**. Any utterance
appearing in test is now promoted to test everywhere.

## 6. the routing research acceptance criteria

| Criterion | Status |
|---|---|
| All master locations have stable unique IDs | **PASS** |
| Verified entities carry provenance (`source_id`, `geocode_precision`) | **PASS** |
| Mandi coordinates carry precision and confidence information | **PASS** |
| No synthetic entity is marked official or verified | **PASS** |
| Coordinates pass containment checks or are flagged | **PASS** |
| No feasible request has quantity <= 0 | **PASS** |
| Over-capacity loads are labelled infeasible, not dropped | **PASS** |
| Route solutions reference their exact cost snapshot | **PASS** |
| Classical/quantum comparisons use identical instance IDs | **PASS** |
| Train/test leakage checks pass | **PASS** |
| Schema validation passes | **PASS** |
| Foreign key checks pass | **PASS** |
| Random seeds reproduce generated datasets | **PASS** |
| Source hashes stored | **PASS** |
| Generation configuration stored | **PASS** |

## 7. Known limitations

These are real, and none is worked around silently:

1. **Containment uses circular district envelopes, not boundary polygons.** A point
   just across a real district border will not be detected. the application must use LGD
   polygons.
2. **No official administrative codes.** LGD/Census was not acquired, so district
   codes are internal `VB-` prefixed and subdistrict/village/pincode are NULL.
3. **Mandi coordinates are town-level**, `coordinate_verified = False` throughout,
   unreconciled against e-NAM or state APMC portals.
4. **Road costs come from an offline detour model**, not measured routing.
5. **Statistical distributions cannot be validated against real-world data**, since
   no real operational dataset was acquired. The checks above verify internal
   consistency and physical plausibility only — they do **not** establish realism.
6. **Test split is 37.5%**, higher than a conventional 20%, because the geographic,
   temporal, template and duplicate holdouts overlap. This trades training volume
   for trustworthy generalisation measurement.
