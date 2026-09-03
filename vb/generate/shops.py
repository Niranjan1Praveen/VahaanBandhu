"""Synthetic rural construction-material and input-dealer shop generation.

Shops are fully synthetic and flagged as such everywhere. There is no
authoritative registry of rural building-material dealers, so rather than
scattering points uniformly over district polygons -- which would put cement
dealers in the middle of fields -- placement is conditioned on a demand surface:

    demand ~ urbanisation + road access + market-town gravity

Concretely, each shop is anchored to an existing village or district town and
offset by a short distance, with anchor selection weighted by that demand
surface. The result is shops clustered along settled, accessible corridors,
which is what makes replenishment routing a non-trivial problem.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from vb.config import GenerationConfig
from vb.enums import GeocodePrecision, LocationType, ShopCategory, VehicleAccess
from vb.geo import haversine_km, km_to_deg_lat, km_to_deg_lon
from vb.generate.locations import LOCATION_COLUMNS, _district_code
from vb.ids import content_id
from vb.reference import districts as dref

# Category mix. Multi-category dealers dominate small rural markets; specialist
# tile/sanitary shops concentrate in more urbanised places.
CATEGORY_WEIGHTS = {
    ShopCategory.MULTI: 0.22,
    ShopCategory.CEMENT: 0.14,
    ShopCategory.HARDWARE: 0.14,
    ShopCategory.TMT: 0.10,
    ShopCategory.BRICK: 0.09,
    ShopCategory.PIPE: 0.07,
    ShopCategory.ELECTRICAL: 0.07,
    ShopCategory.PAINT: 0.06,
    ShopCategory.TILE: 0.05,
    ShopCategory.SANITARY: 0.04,
    ShopCategory.ROOFING: 0.02,
}

# Rough tonnes of stock a dealer of each category holds, and how long a truck
# spends being unloaded there.
CATEGORY_PROFILE = {
    ShopCategory.CEMENT: (60, 240, 45),
    ShopCategory.TMT: (80, 200, 60),
    ShopCategory.BRICK: (150, 500, 70),
    ShopCategory.HARDWARE: (15, 60, 25),
    ShopCategory.PIPE: (20, 70, 30),
    ShopCategory.ELECTRICAL: (8, 40, 20),
    ShopCategory.PAINT: (10, 45, 20),
    ShopCategory.TILE: (35, 110, 40),
    ShopCategory.SANITARY: (20, 70, 30),
    ShopCategory.ROOFING: (40, 130, 45),
    ShopCategory.MULTI: (55, 190, 50),
}

_NAME_EN = [
    "Shri Balaji", "Jai Bharat", "New Kisan", "Sharma", "Verma", "Singh",
    "Gupta", "Maa Durga", "Guru Nanak", "Krishna", "Bansal", "Yadav",
    "National", "Ganpati", "Hind", "Shanti", "Ambey", "Deep",
]
_NAME_HI = [
    "श्री बालाजी", "जय भारत", "न्यू किसान", "शर्मा", "वर्मा", "सिंह",
    "गुप्ता", "माँ दुर्गा", "गुरु नानक", "कृष्णा", "बंसल", "यादव",
    "नेशनल", "गणपति", "हिन्द", "शांति", "अंबे", "दीप",
]
_SUFFIX_EN = {
    ShopCategory.CEMENT: "Cement Store", ShopCategory.TMT: "Steel & TMT",
    ShopCategory.BRICK: "Bricks & Blocks", ShopCategory.HARDWARE: "Hardware",
    ShopCategory.PIPE: "Pipes & Fittings", ShopCategory.ELECTRICAL: "Electricals",
    ShopCategory.PAINT: "Paints", ShopCategory.TILE: "Tiles",
    ShopCategory.SANITARY: "Sanitaryware", ShopCategory.ROOFING: "Roofing",
    ShopCategory.MULTI: "Building Materials",
}
_SUFFIX_HI = {
    ShopCategory.CEMENT: "सीमेंट स्टोर", ShopCategory.TMT: "स्टील एंड टीएमटी",
    ShopCategory.BRICK: "ईंट भंडार", ShopCategory.HARDWARE: "हार्डवेयर",
    ShopCategory.PIPE: "पाइप एंड फिटिंग्स", ShopCategory.ELECTRICAL: "इलेक्ट्रिकल्स",
    ShopCategory.PAINT: "पेंट्स", ShopCategory.TILE: "टाइल्स",
    ShopCategory.SANITARY: "सैनिटरीवेयर", ShopCategory.ROOFING: "रूफिंग",
    ShopCategory.MULTI: "बिल्डिंग मटेरियल",
}


def _demand_surface(villages: pd.DataFrame) -> np.ndarray:
    """Per-village weight for anchoring a shop.

    Building-material demand tracks settlement activity and accessibility. We
    proxy that with the district's urbanisation level plus a mild boost for
    villages nearer their district town, since shops cluster on approach roads.
    """
    w = np.ones(len(villages), dtype=float)
    for i, (dist_name, lat, lon) in enumerate(
        zip(villages["district"], villages["latitude"], villages["longitude"])
    ):
        d = dref.BY_NAME.get(dist_name)
        if d is None:
            continue
        dist_km = haversine_km(lat, lon, d.lat, d.lon)
        gravity = 1.0 / (1.0 + dist_km / 12.0)
        w[i] = 0.25 + 1.6 * d.urbanisation + 1.1 * gravity
    return w / w.sum()


def build_shops(cfg: GenerationConfig, villages: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (shop_locations, shops)."""
    rng = np.random.default_rng(cfg.seed + 23)
    n = cfg.sizes.n_shops

    weights = _demand_surface(villages)
    anchor_idx = rng.choice(len(villages), size=n, replace=True, p=weights)

    cats = list(CATEGORY_WEIGHTS)
    cat_p = np.array([CATEGORY_WEIGHTS[c] for c in cats])
    cat_p = cat_p / cat_p.sum()
    cat_pick = rng.choice(len(cats), size=n, p=cat_p)

    loc_rows, shop_rows = [], []
    for i in range(n):
        v = villages.iloc[int(anchor_idx[i])]
        cat = cats[int(cat_pick[i])]
        d = dref.BY_NAME.get(v["district"])
        urb = d.urbanisation if d else 0.3

        # Shops sit on the settlement edge, near the approach road.
        offset_km = float(abs(rng.normal(0.6, 0.5))) + 0.05
        bearing = float(rng.uniform(0, 2 * np.pi))
        lat = float(v["latitude"]) + km_to_deg_lat(offset_km) * np.sin(bearing)
        lon = float(v["longitude"]) + km_to_deg_lon(offset_km, float(v["latitude"])) * np.cos(bearing)

        nm_i = int(rng.integers(0, len(_NAME_EN)))
        name_en = f"{_NAME_EN[nm_i]} {_SUFFIX_EN[cat]}"
        name_hi = f"{_NAME_HI[nm_i]} {_SUFFIX_HI[cat]}"

        loc_id = content_id("location", "shop", v["district"], cat.value, i)
        shop_id = content_id("shop", v["district"], cat.value, i)

        cap_lo, cap_hi, service = CATEGORY_PROFILE[cat]
        capacity = float(np.round(rng.uniform(cap_lo, cap_hi), 1))
        # Daily throughput is a small fraction of held stock, scaled by how
        # built-up the surrounding district is.
        daily_demand_kg = float(np.round(
            capacity * 1000 * rng.uniform(0.015, 0.06) * (0.5 + urb), 0
        ))

        # Bigger/urban shops can take bigger trucks; remote small ones cannot.
        access_score = 0.55 * urb + 0.45 * min(capacity / 300.0, 1.0)
        if access_score > 0.62:
            access = VehicleAccess.HEAVY
        elif access_score > 0.45:
            access = VehicleAccess.THREE_AXLE
        elif access_score > 0.28:
            access = VehicleAccess.TWO_AXLE
        else:
            access = VehicleAccess.LCV
        road_quality = float(np.round(np.clip(rng.normal(0.35 + 0.5 * urb, 0.14), 0.05, 0.98), 3))

        loc_rows.append({
            "location_id": loc_id,
            "location_type": LocationType.SHOP.value,
            "name_en": name_en,
            "name_hi": name_hi,
            "state": v["state"],
            "state_code": v["state_code"],
            "district": v["district"],
            "district_code": _district_code(d) if d else pd.NA,
            "subdistrict": pd.NA,
            "subdistrict_code": pd.NA,
            "village_town": v["village_town"],
            "village_town_code": pd.NA,
            "pincode": pd.NA,
            "latitude": round(lat, 6),
            "longitude": round(lon, 6),
            "geocode_precision": GeocodePrecision.SYNTHETIC_ENVELOPE.value,
            "source_id": "SRC_VB_SYNTHETIC",
            "source_object_id": pd.NA,
            "is_synthetic": True,
            "confidence_score": 0.0,
            "verified_at": pd.NA,
            "dataset_version": cfg.dataset_version,
            "in_ncr": bool(v["in_ncr"]),
        })
        shop_rows.append({
            "shop_id": shop_id,
            "location_id": loc_id,
            "shop_category": cat.value,
            "capacity_tonnes": capacity,
            "daily_demand_kg": daily_demand_kg,
            "loading_service_min": int(service + rng.integers(-8, 12)),
            "vehicle_access": access.value,
            "road_access_quality": road_quality,
            "anchor_village_location_id": v["location_id"],
            "is_synthetic": True,
            "generation_method": "demand_surface_anchored_v1",
            "source_id": "SRC_VB_SYNTHETIC",
            "seed": cfg.seed,
            "dataset_version": cfg.dataset_version,
        })

    return pd.DataFrame(loc_rows, columns=LOCATION_COLUMNS), pd.DataFrame(shop_rows)
