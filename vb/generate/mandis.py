"""Mandi master generation from the curated real-name reference.

Mandis are the one entity class here that is *not* synthetic: the names are
real markets. Their coordinates, however, are town-level approximations, so
every row is emitted with ``is_synthetic = False`` but
``geocode_precision = settlement`` and a deliberately modest confidence score.
That combination is the honest description: a real market, imprecisely located.

Mandi-to-commodity is emitted as a junction table rather than a delimited
string, so it can be joined and validated properly.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from vb.config import GenerationConfig
from vb.enums import GeocodePrecision, LocationType
from vb.generate.locations import LOCATION_COLUMNS, _district_code
from vb.ids import content_id
from vb.reference import crops as cref
from vb.reference import districts as dref
from vb.reference import mandis as mref

# Town-level coordinates on a real market: real object, coarse geocode.
MANDI_CONFIDENCE = 0.55


def build_mandis(cfg: GenerationConfig) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Return (mandi_locations, mandis, mandi_commodities)."""
    rng = np.random.default_rng(cfg.seed + 11)
    refs = mref.mandis_for_states(cfg.states)

    loc_rows, mandi_rows, commodity_rows = [], [], []
    for m in refs:
        d = dref.BY_NAME.get(m.district)
        loc_id = content_id("location", "mandi", m.key)
        mandi_id = content_id("mandi", m.key)

        loc_rows.append({
            "location_id": loc_id,
            "location_type": LocationType.MANDI.value,
            "name_en": m.name_en,
            "name_hi": m.name_hi,
            "state": dref.STATE_NAMES[m.state_code],
            "state_code": m.state_code,
            "district": m.district,
            "district_code": _district_code(d) if d else pd.NA,
            "subdistrict": pd.NA,
            "subdistrict_code": pd.NA,
            "village_town": m.district,
            "village_town_code": pd.NA,
            "pincode": pd.NA,
            "latitude": m.lat,
            "longitude": m.lon,
            "geocode_precision": GeocodePrecision.SETTLEMENT.value,
            "source_id": "SRC_CURATED_REF",
            "source_object_id": m.key,
            "is_synthetic": False,
            "confidence_score": MANDI_CONFIDENCE,
            "verified_at": pd.NA,  # no verification against an official source has occurred
            "dataset_version": cfg.dataset_version,
            "in_ncr": bool(d.in_ncr) if d else False,
        })

        breadth = mref.SCALE_COMMODITY_BREADTH[m.scale]
        eligible = cref.crops_for_state(m.state_code)
        chosen = eligible if len(eligible) <= breadth else [
            eligible[i] for i in rng.choice(len(eligible), breadth, replace=False)
        ]
        for c in chosen:
            commodity_rows.append({
                "mandi_id": mandi_id,
                "crop_id": content_id("crop", c.key),
                "crop_key": c.key,
                "dataset_version": cfg.dataset_version,
            })

        # Opening pattern: most yards close one day a week.
        closed_day = int(rng.integers(0, 7))
        opening_days = ",".join(
            day for i, day in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])
            if i != closed_day
        )
        queue = mref.SCALE_QUEUE_MIN[m.scale]

        mandi_rows.append({
            "mandi_id": mandi_id,
            "location_id": loc_id,
            "apmc_name": m.name_en,
            "market_yard_type": m.yard_type.value,
            "enam_enabled": m.enam_enabled,
            "commodities_supported": len(chosen),
            "opening_days": opening_days,
            "service_start": "06:00",
            "service_end": "18:00" if m.scale in ("terminal", "large") else "16:00",
            "avg_queue_min": int(queue + rng.integers(-8, 9)),
            "market_scale": m.scale,
            "coordinate_verified": mref.COORDINATE_VERIFIED,
            "source_id": "SRC_CURATED_REF",
            "is_synthetic": False,
            "dataset_version": cfg.dataset_version,
        })

    return (
        pd.DataFrame(loc_rows, columns=LOCATION_COLUMNS),
        pd.DataFrame(mandi_rows),
        pd.DataFrame(commodity_rows),
    )


def build_crops(cfg: GenerationConfig) -> pd.DataFrame:
    """Crop ontology table. Canonical names and aliases stay in separate
    columns so alias noise never contaminates a canonical field."""
    rows = []
    for c in cref.CROPS:
        rows.append({
            "crop_id": content_id("crop", c.key),
            "crop_key": c.key,
            "name_en": c.name_en,
            "name_hi": c.name_hi,
            "aliases_en": "|".join(c.aliases_en),
            "aliases_hi": "|".join(c.aliases_hi),
            "default_unit": c.default_unit.value,
            "default_bag_weight_kg": c.default_bag_weight_kg,
            "density_or_handling_class": c.handling_class,
            "season_kharif_rabi_zaid": c.season.value,
            "states": "|".join(c.states),
            "dataset_version": cfg.dataset_version,
        })
    return pd.DataFrame(rows)
