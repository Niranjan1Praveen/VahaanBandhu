# Dataset Methodology

**VahaanBandhu 2.0 · Phase-A · dataset `v0.1`**

How the synthetic data is generated, and **why each choice was made**. Executable
companion: [`synthetic_data_generation.ipynb`](synthetic_data_generation.ipynb).

---

## 0. Three rules that govern everything

1. **Verified and synthetic data are never mixed silently.** Every spatial row carries
   `is_synthetic`, `geocode_precision`, `confidence_score`, `source_id`. The schema
   *structurally rejects* a synthetic row carrying a non-zero real-world confidence or a
   `verified_at` timestamp.

2. **No fabricated precision.** Where we do not know something to a given accuracy, we
   record the accuracy we actually have and flag it. Mandi coordinates are town-level and
   say so; LGD codes are absent rather than invented.

3. **No fabricated quantities.** `bori` is a sack, not a unit of mass. Where fill weight
   cannot be justified, `quantity_kg` is NULL and the row is labelled `unresolved`.

Every generator is a pure function of `(seed, GenerationConfig)`. Both are recorded in
`metadata/generation_configs/`, and every table's manifest carries the config hash, git
commit and file SHA-256.

---

## 1. Geographic backbone

### Districts

92 districts across Delhi (11), Haryana (22), Punjab (23) and Uttar Pradesh (36), in
[`vb/reference/districts.py`](../vb/reference/districts.py). Names are real; centroids,
radii, agricultural-intensity and urbanisation values are **approximate**, drawn from
general public knowledge rather than an authoritative boundary file. They are tagged
`geocode_precision = district_centroid` with `source_id = SRC_CURATED_REF`.

Fit for: laying out a geographically plausible network, coarse containment QA, relative
distances. **Not fit for:** publication as official coordinates, or any survey-accuracy claim.

### NCR: an explicit flag, never an inference

Each district carries `in_ncr` as a stored boolean. This is not pedantry —
inferring NCR from state is simply wrong:

- **Delhi:** all 11 districts are in NCR.
- **Haryana:** 14 of 22 are (Gurugram, Faridabad, Sonipat, Panipat, Rohtak, Jhajjar,
  Rewari, Palwal, Nuh, Bhiwani, Charkhi Dadri, Mahendragarh, Jind, Karnal). Hisar,
  Sirsa, Ambala, Amritsar-adjacent districts and others are not.
- **Uttar Pradesh:** 8 of 36 are (Gautam Buddha Nagar, Ghaziabad, Meerut, Baghpat,
  Hapur, Bulandshahr, Muzaffarnagar, Shamli).
- **Punjab:** none.

Rajasthan's NCR districts (Alwar, Bharatpur) are genuine NCR members but fall outside
the four target states and are intentionally absent. Tested in
`test_ncr_is_explicit_not_inferred_from_state`.

### Villages — why clustered, not uniform

Village count per district is proportional to agricultural intensity, so grain-belt
districts get denser coverage than urban ones.

Placement uses `sample_clustered`, not uniform sampling. This is a **substantive**
modelling choice, not aesthetics: real settlements follow road corridors and market-town
gravity. A uniform carpet of villages would make every routing problem artificially easy,
every nearest-neighbour heuristic look excellent, and every optimizer look better than it
is. The sampler draws cluster seeds area-uniformly (radius ∝ √u, so seeds do not pile at
the centre), scatters points around them with a Gaussian spread, then clamps back into
the district envelope so nothing escapes its district.

Village names combine transliterated stems (`Rampur`, `Kheri`, `Nangla`, …) with real
suffixes (`Kalan`, `Khurd`, `Majra`), in both scripts. They are plausible-sounding and
explicitly synthetic.

### Mandis — real names, honest coordinates

50 real markets across the four states, with aliases for NLU training
(`azadpur` / `ajadpur` / `आजादपुर`). Coordinates are pinned to the host town, not the
market yard gate.

Every mandi row therefore carries `coordinate_verified = False`,
`geocode_precision = settlement`, `confidence_score = 0.55`, `verified_at = NULL`. A
schema check fails the build if `coordinate_verified` is ever set true without a cited source.

The Phase-A rule *"never fabricate the latitude/longitude of an actual mandi"* is honoured
by refusing to **claim** precision we lack — not by omitting the markets, since routing
needs plausible destinations to exist.

Market scale (`terminal` / `large` / `medium` / `small`) drives gate queue time (28–95 min)
and commodity breadth (4–14 crops), so Azadpur behaves like a terminal market and a small
yard like a small yard.

---

## 2. Crop ontology and quantity normalization

### Canonical names vs. training aliases

18 crops. Canonical `crop_key` is the NLU label and appears in no alias field. Aliases —
transliterations (`gehun`, `gehu`, `genhu`), regional names (`kanak` for wheat, `narma`
for cotton), Devanagari variants, and misspellings — exist **only** to train the parser.
Mixing them into a canonical field would corrupt every downstream join.

### The bori problem

kg, quintal and tonne are exact definitional conversions. **`bori` is not a unit of mass.**
It is a sack whose fill weight depends on crop, packaging and local mandi practice:

- wheat ≈ 50 kg/bori
- paddy ≈ 40 kg/bori
- cotton ≈ 40 kg/bori
- tomato crate ≈ 25 kg
- sugarcane: **no bag weight at all** — it moves loose

A global "1 bori = 50 kg" assumption overstates a 20-bori paddy load by 25%, which
propagates directly into capacity feasibility checks and truck assignment.

`vb.units.normalize` therefore resolves in tiers, and records which tier it used:

| Confidence | When | `quantity_kg` |
|---|---|---|
| `exact` | kg / quintal / tonne | value × factor |
| `crop_default` | bori with a known crop that is bagged | value × crop bag weight |
| `regional_default` | bori, crop unknown but family known | value × class default |
| **`unresolved`** | bori with no determinable bag weight, or value ≤ 0 | **NULL** |

`fits_vehicle()` returns `None` — not `False` — for an unresolved quantity. An unknown
load is not a load that fits and not one that doesn't; collapsing that to a boolean would
silently dispatch an unsized truck.

In `v0.1`, 1,208 of 18,000 requests (6.7%) are genuinely unresolved. That is the feature
working, not a defect.

---

## 3. Synthetic shops

No authoritative registry of rural building-material dealers exists, so shops are fully
synthetic.

**Not uniform over district polygons** — that would put cement dealers in the middle of
fields. Placement is conditioned on a demand surface:

```
weight(village) = 0.25 + 1.6·urbanisation + 1.1·(1 / (1 + km_to_district_town / 12))
```

Shops anchor to a village drawn from that distribution, then offset ~0.6 km (|N(0.6, 0.5)|)
in a random bearing — the settlement edge, where an approach road would be.

Category mix reflects rural reality: multi-category dealers dominate (22%), specialist
tile and sanitaryware shops are rare (5%, 4%) and concentrate in urbanised districts.
Capacity, daily throughput and unloading dwell time follow per-category profiles (a brick
yard holds 150–500 t and takes ~70 min to unload; an electrical shop holds 8–40 t and
takes ~20 min).

`vehicle_access` is derived from urbanisation and shop size, so remote small shops are
LCV-only. This creates genuine routing constraints — a 3-axle truck cannot serve every
shop, which is what makes the assignment problem non-trivial.

---

## 4. Farmer nodes — a privacy design decision

**A farmer node is a pickup point, not a person and not a home.**

Nodes are placed on an **agricultural envelope**: a ring 0.4–3.5 km *outside* the
settlement core, never at the centre where houses are. The table contains no names, no
phone numbers, no household identifiers, and none may be added.

This is a deliberate design constraint rather than an oversight — a synthetic dataset
that generates realistic-looking residential coordinates for farmers creates a re-identification
and misuse surface for no operational benefit. Logistics needs a pickup point; it does not
need a home address.

Conditioning: village selection weighted by district agricultural intensity; farm size
lognormal (heavily right-skewed, as in north India — most holdings small, a few large);
crop assignment restricted to crops actually marketed in that state; market preference
is the nearest mandi 80% of the time, with 20% choosing a farther yard, because farmers
do travel past the nearest market for better prices.

---

## 5. Fleet

Vehicle attributes are drawn from a table of **physically coherent classes** rather than
sampled independently. Independent sampling produces a 30-tonne electric pickup returning
14 km/l; class-constrained sampling cannot.

| Class | Capacity (kg) | km/l | Range (km) | Share |
|---|---|---|---|---|
| pickup | 700–1,500 | 11.0–15.5 | 60–180 | 20% |
| LCV | 1,500–4,000 | 8.0–12.0 | 100–300 | 30% |
| 2-axle | 6,000–11,000 | 4.5–6.5 | 150–450 | 26% |
| 3-axle | 12,000–18,000 | 3.4–4.8 | 200–700 | 16% |
| multi-axle | 20,000–32,000 | 2.6–3.8 | 300–1,000 | 8% |

Body types are restricted per class (no refrigerated multi-axle tipper). EV and CNG appear
only at the light end, matching the current Indian fleet; EV range is additionally capped
at 160 km. Two schema checks enforce the invariants:
`heavy_trucks_have_plausible_economy` and `no_heavy_evs`.

`capacity_bori` is emitted as a driver-facing convenience at a nominal 50 kg — and
documented as **not** an authoritative conversion, precisely because §2 explains why no
such global constant exists.

**Availability slots** allow a truck to appear several times with different remaining
capacity. This is what lets the matcher find *partial* return loads rather than only
whole-truck ones.

---

## 6. Requests and the NLU corpus

### Two populations

**Farmer → mandi.** Quantity is conditioned on farm size, indicative crop yield and
season: a 0.5 ha holding cannot offer 30 tonnes of wheat. Target load = harvest ×
U(0.10, 0.55), clipped to [80 kg, 40 t]. Request dates fall in the crop's actual season
months (rabi → Mar–May, kharif → Sep–Nov, zaid → Jun–Jul).

**Hub → shop.** Quantity is conditioned on shop category and held stock: 3–21 days of
throughput. These are frequently stated in `bori` with no crop, which is a genuinely
unresolvable conversion — exactly the case the converter must refuse to guess.

### Utterance generation

Six template families × 3 languages × multiple surface realisations.

**Labels stay canonical.** However corrupted the surface form, the label is always the
crop key, mandi key, numeric value and unit enum. This is the property that makes the
corpus trainable, and it is tested directly.

**Noise is modelled, not sprinkled.** ASR substitutions follow phonetic neighbours —
स↔श, ज़↔ज, ड़↔ड, b↔v, aa↔a, kh↔k, ph↔f — because that is the error distribution a voice
interface actually produces. Random character flips would train the parser on noise it
will never encounter. Voice input carries a 30% corruption probability; typed input 12%.

Numbers render as a person would state them: digits (`20`), English words (`twenty`),
Hindi words (`बीस`), or Devanagari digits (`२०`).

Real generated examples:

```
'गाड़ी भेजो बरेली राया ०.५१ टन'              -> mustard, bareilly, 0.51, tonne
'mujhe हिसार ke liye 2.4 quintals chickpea bhejna hai' -> gram, hisar, 2.4, quintal
'गोभी, bareli मंडी, 1325 बोरी'                -> cauliflower, bareilly, 1325, bori
'165 bags of pyaz to पलवल'                    -> onion, palwal, 165, bori
'cotten रोहतक 29.1 quintals'                  -> cotton, rohtak, 29.1, quintal
'barnala के लिए कपाश'                         -> cotton, barnala, NULL, NULL
```

Note the mid-sentence script switching, the ASR corruptions (`cotten`, `कपाश`,
`शीतापुर`), and the final incomplete example.

### Hard negatives are labelled, not dropped

| Label | Share | Meaning |
|---|---|---|
| `feasible` | 83.1% | Servable |
| `unresolved_quantity` | 6.7% | Conversion refused |
| `ambiguous` | 6.2% | A field is missing |
| `infeasible` | 3.9% | Exceeds maximum fleet capacity |

A matcher that has never seen an over-capacity load or an unresolvable quantity will fail
the first time a real user produces one. These rows stay in the corpus and out of the
routing instances.

---

## 7. Route graph

### Directed, always

A→B and B→A are separate rows with separate IDs, and their distances differ by ~2.5%
(one-ways, gradients, lane counts). Tested: a perfectly symmetric graph fails
`test_edges_are_directed`.

### Road distance ≠ straight-line distance

`distance_km` applies a **length-dependent detour factor** to the geodesic: 1.42 for short
links (village roads wind) decaying to 1.18 for long ones (highways are direct).
`haversine_km` is retained separately as a QA lower bound and a feature — **never** as the
production road distance. A schema check enforces `distance_km ≥ haversine_km × 0.98`.

This offline model exists because TomTom's terms on persisting responses as derived
training data are unverified (see [DATA_SOURCES.md](DATA_SOURCES.md)). When routing is
configured, the provider overwrites these values for the edges that matter, and the
`source` column says which model produced each row.

### Sparsification

An all-pairs graph over 3,442 locations is ~11.8M edges and mostly meaningless — nobody
routes a Bathinda village to a Gorakhpur shop. We keep a k=8 nearest-neighbour graph plus
every non-mandi node to its 3 nearest mandis in both directions: 46,996 directed edges per
scenario, which is the connectivity the logistics problem actually needs.

### Scenarios never overwrite the baseline

8 scenarios × 46,996 edges = 375,968 rows. `SCN_BASELINE` is the free-flow reference and
is immutable; each scenario is a separate row set keyed by `scenario_id`, so a solution
can always be traced to the exact cost snapshot it was computed against.

---

## 8. Optimization instances

An **instance** is the solver-agnostic problem statement, pinned to one
`cost_snapshot_id`. This is the contract that makes classical/quantum comparison honest:
every solver consumes the same instance and the same matrices, and nothing re-derives its
own distances.

Instances are district-local, because a real truck serves one neighbourhood — and because
that makes the held-out-district split meaningful.

**Fleet sizing was a real bug worth recording.** Drawing `n_vehicles` at random produced
instances whose demand exceeded fleet capacity in 99% of cases, making every benchmark
trivially infeasible. Vehicles are now assigned largest-first until the load fits, plus one
spare so the solver faces a genuine assignment choice. Result: 1,955 of 2,000 instances are
capacity-feasible; the remainder are single-vehicle quantum-band instances and are labelled,
not hidden.

**Size bands** and the qubit reality:

| Band | Customers | Note |
|---|---|---|
| `quantum` | 3–7 | Deliberately tiny — see below |
| `small` | 8–14 | |
| `medium` | 15–30 | |
| `large` | 31–60 | |

`quantum_ready` requires ≤3 customers and a single vehicle, because a permutation QUBO
needs (n+1)² qubits: 3 customers → 16 qubits (fine), 6 → 49 qubits → 2⁴⁹ statevector
amplitudes (impossible). We discovered this empirically when a benchmark run demanded
8.6 exabytes. A schema check now prevents an unencodable instance being flagged ready.

---

## 9. Leakage-safe splits

Random row splitting is wrong here in **four** independent ways:

| Leak | Why it matters | Defence |
|---|---|---|
| **Geographic** | Neighbouring villages share corridors and mandi catchments | Karnal, Bulandshahr and Bathinda held out entirely |
| **Temporal** | Requests carry seasonal structure | Cutoff 2026-11-20 |
| **Template** | A test sentence paraphrasing a training one measures memorisation | `TF_TERSE` held out entirely |
| **Structural** | Two instances with the same hash are the same problem | Split keyed on permutation-invariant `instance_hash` |

Precedence: district > time > template > random bucket, because the district holdout is
the strongest generalisation guarantee.

**A fifth subtlety.** Because the district and time rules can pull one instance of a
repeated utterance into test, an identical sentence could remain in train. A final pass
promotes any utterance appearing in test anywhere to test everywhere
(`split_reason = duplicate_of_test_utterance`). Without it, 149 verbatim duplicates
straddled the split.

Hash bucketing uses SHA-256, not Python's `hash()`, which is salted per process and would
produce different splits on every run.

Current split: 54.2% train / 8.4% validation / 37.5% test. The test share is high because
the holdouts are strict and deliberately overlapping; this trades training volume for
trustworthy generalisation measurement.

---

## 10. Reproducibility

Every release records: generation seed, config hash, git commit, timestamp, row and column
counts, per-file SHA-256, schema version, and dataset version. Manifests live in
`metadata/manifests/`; configs in `metadata/generation_configs/`.

`write_table` **refuses** to overwrite an existing (version, table) pair without an
explicit `overwrite=True`, so a published version is never silently replaced.

IDs are content-derived, not row-ordinal, so regenerating a dataset keeps it
join-compatible with cached solver results.

Stage sizes are configurable (`prototype` / `pilot` / `training`). Phase-A deliberately
proves the pipeline at prototype scale before generating anything larger.

---

## 11. Honest limitations

1. **No official administrative data.** LGD/Census not acquired; district codes are
   internal `VB-` prefixed and subdistrict/village/pincode codes are NULL.
2. **Mandi coordinates are town-level**, unreconciled against e-NAM or state APMC portals.
3. **Containment QA uses circular envelopes, not polygons** — a point just across a real
   district border will not be caught.
4. **Road costs are an offline model**, not measured routing.
5. **Agricultural priors are estimates.** Yield, agricultural intensity and urbanisation
   figures are plausible, not sourced.
6. **Everything except mandi and district names is synthetic.** No distributional claim
   about real rural logistics is supported by this data. It is fit for building and testing
   the pipeline; it is not evidence about the world.
