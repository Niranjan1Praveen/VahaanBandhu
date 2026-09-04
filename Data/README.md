# Data

Dataset version **`v0.1`** · prototype stage · geography **Delhi, Haryana,
Punjab, Uttar Pradesh**

> **Every entity row in this dataset is synthetic.** Villages, farmers, shops,
> trucks, transport requests and road edges were generated, not observed. The
> only real-world content is a curated set of district and mandi **names**, and
> even those carry **approximate, town-level coordinates** that are not sourced
> from an authoritative boundary file. Nothing here may be presented as
> official data.

Machine-readable provenance: [`source_registry.csv`](source_registry.csv).
Narrative versions: [`../research/docs/DATA_SOURCES.md`](../research/docs/DATA_SOURCES.md),
[`../research/docs/DATASET_METHODOLOGY.md`](../research/docs/DATASET_METHODOLOGY.md),
column-level definitions in [`../research/docs/data_dictionary.md`](../research/docs/data_dictionary.md).

---

## Layout

| Path | Contents |
|---|---|
| `master/` | Reference tables — crops, locations, mandis, scenarios |
| `synthetic/` | Generated entities and the routing instance corpus |
| `qa/` | Validation output: schema, geospatial, referential, statistical, leakage |
| `demo/` | Frozen TomTom route geometry used by the read-only public demo |
| `raw/`, `staging/`, `features/`, `splits/` | Pipeline stages; empty in the prototype (no external extract was pulled) |
| `source_registry.csv` | One row per data source: URL, licence, acquisition status, ML-use permission |

Everything under `master/` and `synthetic/` is written by
[`vb/pipeline.py`](../vb/pipeline.py) and is reproducible from the recorded
seed and generation config. Every generated row carries `is_synthetic=True`,
a `seed`, and a `dataset_version`.

---

## Tables

### `master/` — reference

| File | Rows | What it holds |
|---|---:|---|
| `crops.csv` | 18 | Crop identity, English/Hindi names and aliases, default unit, **default bag weight**, handling class, season, states |
| `locations_master.csv` | 3,442 | Villages, mandis, shop sites and depots: names (en/hi), admin hierarchy, lat/lon, `geocode_precision`, `confidence_score`, NCR flag |
| `mandis.csv` | 50 | APMC name, yard type, e-NAM flag, commodities, opening days, service window, queue time, market scale |
| `mandi_commodities.csv` | 383 | Which crops each mandi accepts |
| `scenarios.csv` | 8 | Named traffic/risk multipliers, one marked as the baseline |

### `synthetic/` — generated entities

| File | Rows | What it holds |
|---|---:|---|
| `farmer_nodes.csv` | 1,400 | Farm size, primary/secondary crop, preferred mandi, road access |
| `shops.csv` | 900 | Input-dealer sites: category, capacity, daily demand, loading time, vehicle access |
| `trucks.csv` | 600 | Vehicle class, capacity in kg **and bori**, body/fuel type, mileage, max route length, availability window |
| `truck_availability.csv` | 1,222 | Time-and-place availability with remaining capacity and return-home deadline |
| `transport_requests.csv` | 18,000 | The NLU + feasibility corpus (see below) |
| `route_edges.csv` | 375,968 | Road graph: distance, haversine, free-flow and traffic time, road-class mix, toll, fuel, accessibility, surface risk, per scenario |
| `route_instances.csv` | 2,000 | Optimization instances: problem type, size band, depot, customers, vehicles, constraint flags, objective weights, cost snapshot, split, `estimated_qubits_permutation` |
| `instance_requests.csv` | 37,101 | Instance-to-request membership with per-node demand |

`route_edges.csv` is ~65 MB. Costs in it come from an **offline detour model**,
deliberately — so that no unverified third-party derived data is redistributed
in the corpus.

---

## The request corpus

`transport_requests.csv` is the piece that carries most of the product logic.
Each row is a transport request with the raw utterance, the parsed fields with
per-field confidences, and the gold labels.

| Distribution | |
|---|---|
| Language | hinglish 9,837 · hi 5,003 · en 3,160 |
| Input mode | text 11,124 · voice 6,876 |
| State | UP 7,828 · PB 5,664 · HR 4,390 · DL 118 |
| Unit used | quintal 4,973 · bori 4,680 · tonne 4,225 · kg 4,122 |
| Feasibility | feasible 14,962 · unresolved quantity 1,208 · ambiguous 1,124 · infeasible 706 |

Quantities: min 80 kg, median 3,380 kg, p95 30,000 kg, max 40,000 kg; no
non-positive values.

### The bori rule

A *bori* (sack) has **no universal weight** — it varies by crop and packaging.
The corpus encodes this rather than papering over it. Every converted quantity
records a `conversion_source` and `conversion_confidence`:

| Conversion confidence | Rows | Meaning |
|---|---:|---|
| `exact` | 13,320 | The unit was already a mass unit, or the bag weight was stated |
| `crop_default` | 3,472 | Resolved using the crop's default bag weight from `crops.csv` |
| `unresolved` | 1,208 | **Not guessed.** `quantity_kg` is null and the request asks for clarification |

Assuming 50 kg for a 20-bori paddy load overstates it by 25%, and that error
would propagate straight into vehicle capacity and dispatch the wrong truck.
Those 1,208 rows exist so that both the model and the product are trained to
ask instead of assume.

---

## Quality assurance

All checks in [`qa/qa_summary.json`](qa/qa_summary.json) pass
(`all_passed: true`). Highlights, with their real limits stated:

**Schema** — all 8 tables validate, 0 failures.

**Referential integrity** — 0 dangling foreign keys across all 11 checked
relationships.

**Geospatial** — 3,442 locations, 0 outside the coarse bounding box; 7 outside
their district envelope (p50 distance 16.9 km, p99 33.3 km); 80 duplicate
coordinate pairs; 0 NCR flag mismatches. 375,968 edges with 0 self-loops and 0
edges shorter than the geodesic; 40,258 bidirectional pairs with mean direction
asymmetry 0.97 km.
*Limitation:* containment uses a **circular district envelope**, not boundary
polygons — a point just across a real district border will not be detected. No
LGD polygons were available at this stage.

**Statistical plausibility** — median implied speed 46.0 km/h; 0 speeds above
120 km/h; 0 zero-capacity trucks; 0 negative farm sizes. Edge distance p50 10.1
km, p95 116.4 km, max 221.0 km.

**Leakage** — 0 request-ID overlap, 0 instance-hash overlap, 0 duplicate
utterances across splits, and no held-out template family or district appearing
in training.

Full narrative: [`../research/docs/DATA_QA_REPORT.md`](../research/docs/DATA_QA_REPORT.md).

---

## Sources, licences and what was *not* acquired

The registry records failures as explicitly as successes.

| Source | Status | Notes |
|---|---|---|
| VahaanBandhu synthetic generators | generated | All entity rows. Reproducible from seed. Project-internal licence. |
| Curated district / mandi reference | curated, approximate | Names are real; **coordinates are approximate** and `coordinate_verified=False` throughout. |
| **e-NAM mandi directory** | **not acquired** | Terms not reviewed. Also note e-NAM covers *integrated* markets only and is **not** the full universe of physical mandis — state APMC portals must be cross-checked before treating it as coverage. |
| **Census / LGD Location Code Directory** | **not acquired** | This is why `locations_master` carries internal `VB`-prefixed district codes and null subdistrict/village/pincode codes. Fabricating official location codes would be worse than leaving them empty. |
| **OpenStreetMap** | not used | Integration path exists (`osmnx` is a dependency) but no extract was pulled. **ODbL 1.0 share-alike** applies to derived databases; Nominatim must not be used for bulk geocoding. |
| **TomTom** (routing, matrix, traffic flow) | integration ready | **Storage and redistribution of responses is restricted.** The on-disk cache is a short-TTL *operational* cache, not a training corpus. Verify terms before persisting any response as training data. |
| **IBM Quantum Platform** | integration ready | Offline research and benchmarking only; never in the live request path. |

### `demo/demo_routes.json`

Frozen real TomTom route geometry for one representative journey per role,
captured once and committed so the public demo renders true road paths rather
than straight lines. It is a fixed snapshot, not a live feed, and is used for
display only — not as training data.

---

## Reproducing

```bash
python -m vb.pipeline
```

```bash
pytest tests/test_datasets.py tests/test_ids_geo.py tests/test_units.py
```

---

## Using this responsibly

- Do **not** publish these coordinates as authoritative locations.
- Do **not** treat model results on this corpus as evidence about real Indian
  road logistics — they characterise the algorithms, not the world.
- Do check `source_registry.csv` before redistributing anything derived from a
  third-party source; the ODbL and TomTom rows carry real obligations.
