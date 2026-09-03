"""Location master generation.

``locations_master.csv`` is the single spatial spine of the platform. Mandis,
shops, farmer nodes, depots and villages all resolve to a ``location_id`` here,
so route edges and optimization instances only ever deal in one ID space.

Villages are synthetic. They are placed with a clustered sampler rather than a
uniform one, because real settlements follow corridors and market-town gravity;
a uniform carpet would make every routing problem artificially easy.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from vb.config import GenerationConfig
from vb.enums import GeocodePrecision, LocationType
from vb.geo import sample_clustered
from vb.ids import content_id, slug
from vb.reference import districts as dref

LOCATION_COLUMNS = [
    "location_id", "location_type", "name_en", "name_hi", "state", "state_code",
    "district", "district_code", "subdistrict", "subdistrict_code",
    "village_town", "village_town_code", "pincode", "latitude", "longitude",
    "geocode_precision", "source_id", "source_object_id", "is_synthetic",
    "confidence_score", "verified_at", "dataset_version", "in_ncr",
]

# Transliterated village-name stems, combined with a suffix to produce
# plausible-sounding but explicitly synthetic settlement names.
_STEMS_EN = [
    "Rampur", "Shahpur", "Sultanpur", "Bhagwanpur", "Nangla", "Chandpur",
    "Jamalpur", "Kheri", "Bhojpur", "Mubarikpur", "Dhanaura", "Salempur",
    "Gopalpur", "Alipur", "Bahadurpur", "Manakpur", "Rasulpur", "Todarpur",
    "Kishanpur", "Devipur", "Harjipur", "Nathupur", "Sikandarpur", "Barwala",
    "Ladwa", "Basantpur", "Umarpur", "Fatehpur", "Naurangpur", "Jhinjhana",
]
_STEMS_HI = [
    "रामपुर", "शाहपुर", "सुल्तानपुर", "भगवानपुर", "नंगला", "चांदपुर",
    "जमालपुर", "खेड़ी", "भोजपुर", "मुबारिकपुर", "धनौरा", "सलेमपुर",
    "गोपालपुर", "अलीपुर", "बहादुरपुर", "मानकपुर", "रसूलपुर", "तोदड़पुर",
    "किशनपुर", "देवीपुर", "हरजीपुर", "नत्थूपुर", "सिकंदरपुर", "बरवाला",
    "लाडवा", "बसंतपुर", "उमरपुर", "फतेहपुर", "नौरंगपुर", "झिंझाना",
]
_SUFFIX_EN = ["Kalan", "Khurd", "Khera", "Majra", "Nagar", ""]
_SUFFIX_HI = ["कलां", "खुर्द", "खेड़ा", "माजरा", "नगर", ""]


def _district_code(d: dref.District) -> str:
    """Internal district code. Deliberately prefixed VB- so it can never be
    mistaken for an official LGD or Census code."""
    return f"VB-{d.state_code}-{slug(d.district)[:12].upper()}"


def build_villages(cfg: GenerationConfig) -> pd.DataFrame:
    """Generate synthetic village nodes distributed across target districts.

    Village count per district is proportional to agricultural intensity, so
    grain-belt districts get denser coverage than urban ones.
    """
    rng = np.random.default_rng(cfg.seed)
    dists = dref.for_states(cfg.states)

    weights = np.array([max(d.agri_intensity, 0.02) for d in dists])
    weights = weights / weights.sum()
    counts = np.maximum(1, np.round(weights * cfg.sizes.n_villages).astype(int))

    rows: list[dict] = []
    for d, n in zip(dists, counts):
        lat, lon = sample_clustered(
            rng, d.lat, d.lon, d.radius_km, int(n),
            n_clusters=max(3, int(n / 40)), cluster_spread_km=max(2.0, d.radius_km / 6),
        )
        stem_idx = rng.integers(0, len(_STEMS_EN), n)
        suf_idx = rng.integers(0, len(_SUFFIX_EN), n)
        for i in range(int(n)):
            si, ui = int(stem_idx[i]), int(suf_idx[i])
            name_en = f"{_STEMS_EN[si]} {_SUFFIX_EN[ui]}".strip()
            name_hi = f"{_STEMS_HI[si]} {_SUFFIX_HI[ui]}".strip()
            # Disambiguate same-named villages within a district by index.
            name_en = f"{name_en} ({i + 1})" if n > len(_STEMS_EN) else name_en
            loc_id = content_id("location", "village", d.state_code, d.district, name_en, i)
            rows.append({
                "location_id": loc_id,
                "location_type": LocationType.VILLAGE.value,
                "name_en": name_en,
                "name_hi": name_hi,
                "state": d.state,
                "state_code": d.state_code,
                "district": d.district,
                "district_code": _district_code(d),
                "subdistrict": pd.NA,
                "subdistrict_code": pd.NA,
                "village_town": name_en,
                "village_town_code": pd.NA,
                "pincode": pd.NA,
                "latitude": round(float(lat[i]), 6),
                "longitude": round(float(lon[i]), 6),
                "geocode_precision": GeocodePrecision.SYNTHETIC_ENVELOPE.value,
                "source_id": "SRC_VB_SYNTHETIC",
                "source_object_id": pd.NA,
                "is_synthetic": True,
                "confidence_score": 0.0,  # synthetic: no real-world confidence
                "verified_at": pd.NA,
                "dataset_version": cfg.dataset_version,
                "in_ncr": d.in_ncr,
            })
    return pd.DataFrame(rows, columns=LOCATION_COLUMNS)


def build_depots(cfg: GenerationConfig) -> pd.DataFrame:
    """One depot / truck-parking hub per district town.

    Depots anchor VRP instances: every route instance needs a start and (for the
    circular-return formulation) an end node.
    """
    dists = dref.for_states(cfg.states)
    rows = []
    for d in dists:
        loc_id = content_id("location", "depot", d.state_code, d.district)
        rows.append({
            "location_id": loc_id,
            "location_type": LocationType.DEPOT.value,
            "name_en": f"{d.district} Transport Depot",
            "name_hi": f"{d.district} ट्रांसपोर्ट डिपो",
            "state": d.state,
            "state_code": d.state_code,
            "district": d.district,
            "district_code": _district_code(d),
            "subdistrict": pd.NA,
            "subdistrict_code": pd.NA,
            "village_town": d.district,
            "village_town_code": pd.NA,
            "pincode": pd.NA,
            "latitude": round(d.lat, 6),
            "longitude": round(d.lon, 6),
            "geocode_precision": GeocodePrecision.DISTRICT_CENTROID.value,
            "source_id": "SRC_VB_SYNTHETIC",
            "source_object_id": pd.NA,
            "is_synthetic": True,
            "confidence_score": 0.0,
            "verified_at": pd.NA,
            "dataset_version": cfg.dataset_version,
            "in_ncr": d.in_ncr,
        })
    return pd.DataFrame(rows, columns=LOCATION_COLUMNS)
