"""Data source registry.

Every dataset must be traceable to a row here. Sources that were *not*
successfully acquired are recorded too, with status ``blocked`` -- an
unacquired source is a finding, not an omission to be quietly dropped.
"""

from __future__ import annotations

from datetime import date

import pandas as pd

from vb.config import SOURCE_REGISTRY

REGISTRY_COLUMNS = [
    "source_id", "source_name", "source_url", "organization", "retrieved_at",
    "status", "license_or_terms", "geography", "fields_used", "raw_file_hash",
    "ml_training_permitted", "notes",
]

SOURCES = [
    {
        "source_id": "SRC_VB_SYNTHETIC",
        "source_name": "VahaanBandhu synthetic generators",
        "source_url": "internal://vb.generate",
        "organization": "VahaanBandhu",
        "retrieved_at": "",
        "status": "generated",
        "license_or_terms": "Project-internal. Freely usable within the project.",
        "geography": "DL, HR, PB, UP",
        "fields_used": "all synthetic entity fields",
        "raw_file_hash": "",
        "ml_training_permitted": "yes",
        "notes": (
            "Villages, shops, farmer nodes, trucks, requests and route edges. "
            "Fully synthetic; every row carries is_synthetic=True. Reproducible "
            "from the recorded seed and generation config."
        ),
    },
    {
        "source_id": "SRC_CURATED_REF",
        "source_name": "Curated district and mandi reference",
        "source_url": "internal://vb.reference",
        "organization": "VahaanBandhu",
        "retrieved_at": "",
        "status": "curated_approximate",
        "license_or_terms": "Project-internal compilation of public-domain facts.",
        "geography": "DL, HR, PB, UP",
        "fields_used": "district names, mandi names, approximate centroids, NCR membership",
        "raw_file_hash": "",
        "ml_training_permitted": "yes",
        "notes": (
            "District and mandi NAMES are real. COORDINATES ARE APPROXIMATE, "
            "town-level, and not sourced from an authoritative boundary file. "
            "Emitted with geocode_precision=settlement|district_centroid and a "
            "reduced confidence score; coordinate_verified=False throughout. "
            "Must not be presented as official. Phase-B replaces this."
        ),
    },
    {
        "source_id": "SRC_ENAM_DIRECTORY",
        "source_name": "e-NAM mandi directory",
        "source_url": "https://enam.gov.in/web/dhanyawad/mandis",
        "organization": "Ministry of Agriculture & Farmers Welfare, GoI",
        "retrieved_at": "",
        "status": "blocked",
        "license_or_terms": "Terms not reviewed; acquisition not attempted in Phase-A.",
        "geography": "India",
        "fields_used": "",
        "raw_file_hash": "",
        "ml_training_permitted": "unknown",
        "notes": (
            "NOT ACQUIRED. Phase-A proceeds on synthetic data by explicit "
            "decision. Critically, e-NAM covers integrated markets only and is "
            "NOT the complete universe of physical mandis -- Phase-B must "
            "cross-check against state APMC/marketing board portals for DL, HR, "
            "PB and UP rather than treating e-NAM as authoritative coverage."
        ),
    },
    {
        "source_id": "SRC_CENSUS_LGD",
        "source_name": "Census of India / LGD Location Code Directory",
        "source_url": "https://lgdirectory.gov.in/",
        "organization": "Ministry of Panchayati Raj / Office of the Registrar General",
        "retrieved_at": "",
        "status": "blocked",
        "license_or_terms": "Terms not reviewed; acquisition not attempted in Phase-A.",
        "geography": "India",
        "fields_used": "",
        "raw_file_hash": "",
        "ml_training_permitted": "unknown",
        "notes": (
            "NOT ACQUIRED. This is why locations_master carries internal "
            "VB-prefixed district codes and NULL subdistrict/village/pincode "
            "codes: fabricating official location codes would be worse than "
            "leaving them empty. Phase-B must populate these from LGD."
        ),
    },
    {
        "source_id": "SRC_OSM",
        "source_name": "OpenStreetMap",
        "source_url": "https://www.openstreetmap.org/",
        "organization": "OpenStreetMap contributors",
        "retrieved_at": "",
        "status": "not_used_in_prototype",
        "license_or_terms": "ODbL 1.0. Share-alike; attribution required for derived data.",
        "geography": "Global",
        "fields_used": "",
        "raw_file_hash": "",
        "ml_training_permitted": "yes, with ODbL obligations on derived databases",
        "notes": (
            "Integration path is built (osmnx is a dependency) but no extract "
            "was pulled for the prototype. Note the ODbL share-alike obligation "
            "before mixing OSM geometry into a redistributed dataset. "
            "Nominatim must not be used for bulk geocoding per its usage policy."
        ),
    },
    {
        "source_id": "SRC_TOMTOM",
        "source_name": "TomTom Routing, Matrix and Traffic Flow APIs",
        "source_url": "https://developer.tomtom.com/",
        "organization": "TomTom",
        "retrieved_at": "",
        "status": "integration_ready",
        "license_or_terms": (
            "Freemium developer terms. STORAGE AND REDISTRIBUTION OF RESPONSES "
            "IS RESTRICTED -- verify before persisting any response as training data."
        ),
        "geography": "Global",
        "fields_used": "route geometry, distance, travel time, traffic delay (live only)",
        "raw_file_hash": "",
        "ml_training_permitted": "UNVERIFIED - do not persist as training data without checking terms",
        "notes": (
            "Provider abstraction and an on-disk cache exist. The cache is a "
            "short-TTL operational cache, NOT a training corpus. route_edges "
            "ships with offline detour-model costs precisely so the dataset "
            "carries no unverified third-party derived data."
        ),
    },
    {
        "source_id": "SRC_IBM_QUANTUM",
        "source_name": "IBM Quantum Platform",
        "source_url": "https://quantum.ibm.com/",
        "organization": "IBM",
        "retrieved_at": "",
        "status": "integration_ready",
        "license_or_terms": "IBM Quantum Platform terms of use.",
        "geography": "n/a",
        "fields_used": "backend metadata, measurement counts",
        "raw_file_hash": "",
        "ml_training_permitted": "n/a",
        "notes": (
            "Used only in the offline research/benchmark stage, never in the "
            "live request path. Simulator results are produced locally; hardware "
            "execution status is recorded per experiment."
        ),
    },
]


def write_source_registry(cfg) -> pd.DataFrame:
    rows = []
    for s in SOURCES:
        r = dict(s)
        if r["status"] in ("generated", "curated_approximate"):
            r["retrieved_at"] = date.today().isoformat()
        rows.append(r)
    df = pd.DataFrame(rows, columns=REGISTRY_COLUMNS)
    SOURCE_REGISTRY.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(SOURCE_REGISTRY, index=False, encoding="utf-8")
    return df
