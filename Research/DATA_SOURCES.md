# Data Sources

**VahaanBandhu 2.0 · Phase-A · dataset `v0.1`**

Machine-readable equivalent: [`Data/source_registry.csv`](../Data/source_registry.csv).

This document records what was used, what was **not** acquired, and what may legally
be done with each. An unacquired source appears here with status `blocked` rather than
being silently omitted.

---

## Summary

| `source_id` | Source | Status | Used for | ML training |
|---|---|---|---|---|
| `SRC_VB_SYNTHETIC` | VahaanBandhu generators | generated | villages, shops, farmer nodes, trucks, requests, edges | Yes |
| `SRC_CURATED_REF` | Curated district + mandi reference | curated_approximate | district names/centroids, mandi names/approx coords, NCR flags | Yes |
| `SRC_ENAM_DIRECTORY` | e-NAM mandi directory | **blocked** | — | Unknown |
| `SRC_CENSUS_LGD` | Census / LGD Location Code Directory | **blocked** | — | Unknown |
| `SRC_OSM` | OpenStreetMap | not_used_in_prototype | — | Yes, with ODbL obligations |
| `SRC_TOMTOM` | TomTom Routing / Traffic APIs | integration_ready | live routing only | **Unverified — do not persist** |
| `SRC_IBM_QUANTUM` | IBM Quantum Platform | integration_ready | offline benchmarking | n/a |

---

## `SRC_VB_SYNTHETIC` — VahaanBandhu synthetic generators

- **Organization:** VahaanBandhu (internal)
- **Coverage:** Delhi, Haryana, Punjab, Uttar Pradesh
- **Data produced:** village nodes, depots, shops, farmer logistics nodes, truck fleet,
  truck availability, transport requests, the Hindi/English/Hinglish utterance corpus,
  the directed route graph, and optimization instances.
- **Licence:** Project-internal. No third-party rights attach.
- **Caveats:** Every row carries `is_synthetic = True` and `confidence_score = 0.0`.
  These records describe **nothing about the real world**. They are fit for building and
  testing the pipeline; they are not evidence about rural logistics.
- **Reproducibility:** Fully determined by `(seed, GenerationConfig)`. Both are recorded
  in `metadata/generation_configs/` and in each table's manifest entry.

---

## `SRC_CURATED_REF` — Curated district and mandi reference

- **Organization:** VahaanBandhu compilation of public-domain facts
- **Modules:** [`vb/reference/districts.py`](../vb/reference/districts.py),
  [`vb/reference/mandis.py`](../vb/reference/mandis.py)
- **Coverage:** 92 districts and 50 mandis across DL / HR / PB / UP
- **Data used:** district names, approximate district centroids, district radius
  estimates, agricultural-intensity and urbanisation priors, NCR membership flags,
  mandi names and aliases, approximate mandi coordinates, yard type, e-NAM flag.

### The important caveat

**Names are real. Coordinates are approximate.**

District and mandi names are genuine and drawn from general public knowledge. Their
coordinates are town-level approximations, **not** sourced from an authoritative boundary
file or a survey. Accordingly:

- mandi rows carry `geocode_precision = settlement`, `confidence_score = 0.55`,
  `coordinate_verified = False`, and `verified_at = NULL`;
- district-derived depots carry `geocode_precision = district_centroid`;
- a schema check (`no_unsourced_verified_coordinate_claim`) **fails the build** if any
  mandi row ever asserts `coordinate_verified = True` without a cited source.

The Phase-A rule *"never fabricate the latitude/longitude of an actual mandi"* is
honoured by refusing to claim precision we do not have — not by omitting the markets,
since routing needs plausible destinations to exist.

### NCR membership

NCR is an **explicit per-district flag**, never inferred from state. Haryana and Uttar
Pradesh each contain both NCR and non-NCR districts; Delhi is entirely within NCR; no
Punjab district is. Rajasthan's NCR districts (Alwar, Bharatpur) are genuine NCR members
but fall outside the four target states and are intentionally absent.

---

## `SRC_ENAM_DIRECTORY` — e-NAM mandi directory — **BLOCKED**

- **URL:** https://enam.gov.in/
- **Organization:** Ministry of Agriculture & Farmers Welfare, Government of India
- **Status:** **Not acquired.** Phase-A proceeds on synthetic data by explicit project
  decision, so no scraping or bulk download was attempted and the terms were not reviewed.
- **Consequence:** The `enam_enabled` flag in `mandis.csv` is a **plausible assignment
  from the curated reference, not a verified e-NAM integration status.** It must not be
  presented to users as authoritative.

**Critical note for Phase-B:** e-NAM covers *integrated* markets only. It is **not** the
complete universe of physical mandis. Reconciliation must cross-check against the state
agricultural marketing board / APMC portals for Delhi, Haryana, Punjab and Uttar Pradesh,
and treat e-NAM as one input rather than as ground truth for coverage.

---

## `SRC_CENSUS_LGD` — Census / LGD Location Code Directory — **BLOCKED**

- **URL:** https://lgdirectory.gov.in/
- **Organization:** Ministry of Panchayati Raj / Office of the Registrar General
- **Status:** **Not acquired.**
- **Consequence, visible in the data:** `locations_master.csv` carries internal
  district codes prefixed `VB-` (so they can never be mistaken for official LGD or
  Census codes), and `subdistrict_code`, `village_town_code` and `pincode` are **NULL
  throughout**.

Leaving these fields empty is deliberate. Fabricating official government location codes
would be materially worse than an empty column: it would be undetectable downstream and
would corrupt any future reconciliation.

**Phase-B must** populate state / district / subdistrict / village codes from LGD, and
replace the circular district envelopes used in geospatial QA with real boundary polygons.

---

## `SRC_OSM` — OpenStreetMap

- **URL:** https://www.openstreetmap.org/
- **Licence:** **ODbL 1.0** — attribution required, and **share-alike obligations attach
  to derived databases.**
- **Status:** Integration path exists (`osmnx` is a pinned dependency) but **no extract
  was pulled for the prototype**, so no OSM data is present in `v0.1`.

### Obligations to respect before use

1. **ODbL share-alike is contagious.** Mixing OSM geometry into a redistributed database
   can obligate publishing that database under ODbL. Decide the licensing posture *before*
   ingesting, not after.
2. **Nominatim must not be used for bulk geocoding.** Its usage policy prohibits heavy
   automated use. Use a self-hosted instance or a Geofabrik extract instead.
3. Attribution is required in any product surface displaying derived data.

---

## `SRC_TOMTOM` — TomTom Routing, Matrix and Traffic Flow APIs

- **URL:** https://developer.tomtom.com/
- **Status:** Integration ready. `TomTomRoutingProvider` implements routing, alternative
  routes, matrices and traffic flow, with multi-key rotation on quota exhaustion.
- **Used for:** live route candidates and traffic only.

### Licensing posture — the reason `route_edges` is not built from TomTom

**Storage and redistribution rights for TomTom responses are UNVERIFIED.** Freemium
developer terms commonly restrict persisting responses, and restrict their use as
derived training data.

Because of that uncertainty, Phase-A deliberately does **not** persist any TomTom
response into `Data/`. `route_edges.csv` is generated from an offline detour model
(`source = offline_detour_model_v1`), so the dataset carries no third-party derived data
of unverified provenance.

TomTom responses go only into `Res/route_cache/`, which is:
- a **short-TTL operational cache** (15 minutes for traffic-derived data),
- explicitly **not** a training corpus,
- excluded from version control via `.gitignore`.

**Before any TomTom-derived data is persisted for ML training, the current terms must be
read and the finding recorded here.**

### Credentials

Three freemium keys are configured via `TOMTOM_API_KEYS` (comma-separated) and rotated on
HTTP 403/429. Never hard-coded — note that the pre-existing `server/TruckRouteNavigator/app.py`
contains a hard-coded key that should be rotated and removed from git history.

---

## `SRC_IBM_QUANTUM` — IBM Quantum Platform

- **URL:** https://quantum.ibm.com/
- **Status:** Integration ready and **verified connected** during Phase-A.
- **Used for:** offline research and benchmarking **only**. Never in the live request path.
- **Credentials:** `IBM_QUANTUM_TOKEN` and `IBM_QUANTUM_CHANNEL` from the environment.
- **Data recorded:** backend name, job id, transpiled depth and qubit count, shot counts,
  measurement histograms, decoded routes, feasibility rates.

Measurement results are our own experimental output. Backend availability and queue depth
are observed operational facts, recorded with timestamps.

---

## Provenance fields carried on every record

| Field | Meaning |
|---|---|
| `source_id` | FK into `source_registry.csv` |
| `source_object_id` | Identifier within the source system, where one exists |
| `is_synthetic` | Whether the entity was generated rather than observed |
| `confidence_score` | Real-world confidence, `0.0` for synthetic by schema rule |
| `geocode_precision` | How tightly the coordinate is pinned (`exact` … `synthetic_envelope`) |
| `verified_at` | Timestamp of verification against a source; NULL if never verified |
| `coordinate_verified` | Mandi-specific; `False` throughout Phase-A |
| `generation_method` | Named, versioned generator that produced a synthetic row |
| `seed` | Random seed |
| `dataset_version` | Release version |

Each table's manifest (`metadata/manifests/`) additionally records row and column counts,
the SHA-256 of the written file, the generation config hash, and the git commit.
