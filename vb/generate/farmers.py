"""Farmer logistics-node generation.

PRIVACY DESIGN
--------------
A farmer node is a *pickup point*, not a person and not a home. Nodes are
deliberately snapped to the agricultural envelope around a village -- an
offset ring outside the settlement core -- so that no row in this dataset
resembles a residential address. There are no names, no phone numbers and no
household identifiers here, and none should ever be added.

Node density per village is conditioned on the district's agricultural
intensity and farm-size distribution, so grain-belt districts produce more,
larger pickup points than peri-urban ones.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from vb.config import GenerationConfig
from vb.geo import km_to_deg_lat, km_to_deg_lon
from vb.ids import content_id
from vb.reference import crops as cref
from vb.reference import districts as dref
from vb.reference import mandis as mref

# Farm-size distribution (hectares) is heavily right-skewed in north India:
# most holdings are small, a few are large. Lognormal captures that shape.
FARM_SIZE_LOGNORM = (0.15, 0.75)  # (mu, sigma) of underlying normal


def build_farmer_nodes(
    cfg: GenerationConfig, villages: pd.DataFrame, mandi_locations: pd.DataFrame
) -> pd.DataFrame:
    rng = np.random.default_rng(cfg.seed + 37)
    n = cfg.sizes.n_farmer_nodes

    # Weight village selection by agricultural intensity: farm nodes belong in
    # farming districts, not in central Delhi.
    w = np.array([
        max(dref.BY_NAME[d].agri_intensity, 0.01) if d in dref.BY_NAME else 0.01
        for d in villages["district"]
    ])
    w = w / w.sum()
    anchor_idx = rng.choice(len(villages), size=n, replace=True, p=w)

    mandi_lat = mandi_locations["latitude"].to_numpy(float)
    mandi_lon = mandi_locations["longitude"].to_numpy(float)
    mandi_ids = mandi_locations["source_object_id"].to_numpy()

    rows = []
    for i in range(n):
        v = villages.iloc[int(anchor_idx[i])]
        d = dref.BY_NAME.get(v["district"])
        state_code = v["state_code"]

        # Agricultural envelope: a ring 0.4-3.5 km outside the settlement core.
        # Never the settlement centre, which is where houses are.
        r_km = float(rng.uniform(0.4, 3.5))
        bearing = float(rng.uniform(0, 2 * np.pi))
        lat = float(v["latitude"]) + km_to_deg_lat(r_km) * np.sin(bearing)
        lon = float(v["longitude"]) + km_to_deg_lon(r_km, float(v["latitude"])) * np.cos(bearing)

        farm_size = float(np.round(
            np.clip(rng.lognormal(*FARM_SIZE_LOGNORM) * (0.6 + (d.agri_intensity if d else 0.5)),
                    0.2, 40.0), 2))

        eligible = cref.crops_for_state(state_code) or cref.CROPS
        primary = eligible[int(rng.integers(0, len(eligible)))]
        secondary_pool = [c for c in eligible if c.key != primary.key]
        secondary = (
            secondary_pool[int(rng.integers(0, len(secondary_pool)))]
            if secondary_pool and rng.random() < 0.7 else None
        )

        # Market preference: nearest mandi most of the time, but farmers do
        # travel past the nearest yard for better prices, so 20% pick another.
        dl = (mandi_lat - lat) ** 2 + (mandi_lon - lon) ** 2
        if rng.random() < 0.80:
            pick = int(np.argmin(dl))
        else:
            pick = int(np.argsort(dl)[min(int(rng.integers(1, 4)), len(dl) - 1)])
        pref_key = mandi_ids[pick]

        rows.append({
            "farmer_node_id": content_id("farmer_node", v["location_id"], i),
            "village_location_id": v["location_id"],
            "district": v["district"],
            "state_code": state_code,
            "latitude": round(lat, 6),
            "longitude": round(lon, 6),
            "farm_size_ha": farm_size,
            "primary_crop_id": content_id("crop", primary.key),
            "primary_crop_key": primary.key,
            "secondary_crop_id": content_id("crop", secondary.key) if secondary else pd.NA,
            "secondary_crop_key": secondary.key if secondary else pd.NA,
            "market_preference_mandi_id": content_id("mandi", pref_key),
            "road_access_km": round(float(abs(rng.normal(0.8, 0.6))) + 0.05, 3),
            "is_synthetic": True,
            "generation_method": "agri_envelope_ring_v1",
            "seed": cfg.seed,
            "dataset_version": cfg.dataset_version,
        })
    return pd.DataFrame(rows)
