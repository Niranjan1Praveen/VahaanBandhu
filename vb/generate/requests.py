"""Transport request generation.

Two request populations share one table:

* **farmer -> mandi**: a crop load moving from a farm pickup point to a market.
  Quantity is conditioned on farm size, crop yield and season, so a 0.5 ha
  holding does not offer 30 tonnes of wheat.
* **hub -> shop**: a building-material replenishment moving to a rural dealer.
  Quantity is conditioned on shop category and held stock.

The corpus deliberately includes requests that cannot be served. Infeasible and
ambiguous rows are *labelled*, not hidden: a matcher that has never seen an
over-capacity load or an unresolvable bori quantity will fail the first time a
real user produces one.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from vb.enums import InputLanguage, InputMode, RequesterType, Season, Unit
from vb.generate.nlu import TEMPLATE_FAMILIES, make_utterance
from vb.ids import content_id
from vb.reference import crops as cref
from vb.reference import mandis as mref
from vb.units import normalize

# Indicative marketable yield in tonnes per hectare. Used only to scale
# synthetic load sizes into a believable range -- not an agronomic claim.
YIELD_T_PER_HA = {
    "wheat": 4.4, "paddy": 4.0, "mustard": 1.6, "sugarcane": 72.0, "maize": 3.2,
    "bajra": 2.2, "gram": 1.4, "moong": 0.9, "cotton": 2.0, "potato": 24.0,
    "onion": 20.0, "tomato": 26.0, "cauliflower": 18.0, "barley": 3.4,
    "sunflower": 1.7, "guar": 1.1, "arhar": 1.2, "urad": 0.8,
}

SEASON_MONTHS = {
    Season.RABI: (3, 4, 5),
    Season.KHARIF: (9, 10, 11),
    Season.ZAID: (6, 7),
    Season.PERENNIAL: (1, 2, 3, 4, 10, 11, 12),
}

BASE_DATE = datetime(2026, 1, 1)

REQUEST_COLUMNS = [
    "request_id", "requester_type", "requester_id", "origin_location_id",
    "destination_mandi_id", "destination_shop_id", "crop_id", "crop_key",
    "quantity_value", "quantity_unit", "quantity_kg", "bag_weight_kg_used",
    "conversion_source", "conversion_confidence", "pickup_earliest",
    "pickup_latest", "delivery_latest", "priority", "input_language",
    "input_mode", "raw_utterance", "template_family", "parsed_crop_conf",
    "parsed_mandi_conf", "parsed_quantity_conf", "label_crop_key",
    "label_mandi_key", "label_quantity_value", "label_quantity_unit",
    "is_incomplete", "missing_field", "feasibility_label", "infeasible_reason",
    "district", "state_code", "request_date", "is_synthetic", "dataset_version",
]


def _pick_unit(rng: np.random.Generator, crop: cref.Crop) -> Unit:
    """Farmers state quantities in whatever unit suits the crop and the load."""
    if crop.default_unit is Unit.TONNE:
        return Unit(rng.choice([Unit.TONNE.value, Unit.QUINTAL.value], p=[0.7, 0.3]))
    if crop.handling_class == "perishable_crate":
        return Unit(rng.choice([Unit.KG.value, Unit.BORI.value, Unit.QUINTAL.value],
                               p=[0.5, 0.25, 0.25]))
    return Unit(rng.choice(
        [Unit.QUINTAL.value, Unit.BORI.value, Unit.KG.value, Unit.TONNE.value],
        p=[0.42, 0.34, 0.16, 0.08]))


def _to_unit_value(kg: float, unit: Unit, crop: cref.Crop, rng: np.random.Generator) -> float:
    """Express a target kg load in the unit the user would actually say."""
    if unit is Unit.KG:
        return float(np.round(kg, -1))
    if unit is Unit.QUINTAL:
        return float(np.round(kg / 100.0, 1))
    if unit is Unit.TONNE:
        return float(np.round(kg / 1000.0, 2))
    bw = crop.default_bag_weight_kg or 50.0
    return float(max(1, round(kg / bw)))


def build_transport_requests(
    cfg,
    farmer_nodes: pd.DataFrame,
    shops: pd.DataFrame,
    mandi_locations: pd.DataFrame,
    shop_locations: pd.DataFrame,
    trucks: pd.DataFrame,
) -> pd.DataFrame:
    rng = np.random.default_rng(cfg.seed + 71)
    n_total = cfg.sizes.n_requests
    n_shop = int(n_total * cfg.frac_shop_requests)
    n_farmer = n_total - n_shop

    families = list(TEMPLATE_FAMILIES)
    lang_choices = [InputLanguage.HI, InputLanguage.EN, InputLanguage.HINGLISH]
    max_truck_capacity = float(trucks["capacity_kg"].max())

    mandi_by_id = {
        content_id("mandi", k): k for k in mref.BY_KEY
    }
    mandi_loc_by_mandi_id = {
        content_id("mandi", row["source_object_id"]): row["location_id"]
        for _, row in mandi_locations.iterrows()
    }

    rows: list[dict] = []

    # --- farmer -> mandi -----------------------------------------------------
    f_idx = rng.integers(0, len(farmer_nodes), n_farmer)
    for i in range(n_farmer):
        fn = farmer_nodes.iloc[int(f_idx[i])]
        crop_key = fn["primary_crop_key"] if rng.random() < 0.75 else (
            fn["secondary_crop_key"] if pd.notna(fn["secondary_crop_key"]) else fn["primary_crop_key"]
        )
        crop = cref.BY_KEY[crop_key]

        # A farmer moves a share of one harvest, not the whole year's output.
        yield_t = YIELD_T_PER_HA.get(crop_key, 3.0)
        harvest_kg = float(fn["farm_size_ha"]) * yield_t * 1000.0
        target_kg = harvest_kg * float(rng.uniform(0.10, 0.55))
        target_kg = float(np.clip(target_kg, 80.0, 40000.0))

        unit = _pick_unit(rng, crop)
        value = _to_unit_value(target_kg, unit, crop, rng)

        mandi_id = fn["market_preference_mandi_id"]
        mandi_key = mandi_by_id.get(mandi_id)
        if mandi_key is None:
            continue
        mandi_ref = mref.BY_KEY[mandi_key]

        # Force a fraction of bori requests to be unresolvable, by generating
        # them for a crop the converter has no bag weight for.
        force_unresolved = unit is Unit.BORI and rng.random() < 0.06
        q = normalize(value, unit, None if force_unresolved else crop_key,
                      None if force_unresolved else crop.handling_class)

        month = int(rng.choice(SEASON_MONTHS[crop.season]))
        day = int(rng.integers(1, 28))
        req_date = BASE_DATE.replace(month=month, day=day)
        pickup_h = int(rng.integers(5, 15))
        pickup_earliest = req_date + timedelta(hours=pickup_h)
        pickup_latest = pickup_earliest + timedelta(hours=float(rng.uniform(2, 10)))
        delivery_latest = pickup_latest + timedelta(hours=float(rng.uniform(4, 30)))

        feasibility, reason = "feasible", None
        if q.kg is None:
            feasibility, reason = "unresolved_quantity", q.conversion_source
        elif q.kg > max_truck_capacity:
            feasibility, reason = "infeasible", "exceeds_max_fleet_capacity"
        elif q.kg <= 0:
            feasibility, reason = "infeasible", "non_positive_quantity"

        drop = None
        if rng.random() < cfg.frac_ambiguous:
            drop = str(rng.choice(["quantity", "mandi", "crop"], p=[0.4, 0.35, 0.25]))
            if feasibility == "feasible":
                feasibility, reason = "ambiguous", f"missing_{drop}"

        lang = lang_choices[int(rng.choice(3, p=list(cfg.lang_mix)))]
        is_voice = bool(rng.random() < cfg.frac_voice)
        family = families[int(rng.integers(0, len(families)))]
        utt = make_utterance(rng, crop, mandi_ref, value, unit, lang, family,
                             is_voice=is_voice, drop_field=drop)

        rows.append({
            "request_id": content_id("request", "farmer", fn["farmer_node_id"], i),
            "requester_type": RequesterType.FARMER.value,
            "requester_id": fn["farmer_node_id"],
            "origin_location_id": fn["village_location_id"],
            "destination_mandi_id": mandi_id,
            "destination_shop_id": pd.NA,
            "crop_id": content_id("crop", crop_key),
            "crop_key": crop_key,
            "quantity_value": value,
            "quantity_unit": unit.value,
            "quantity_kg": q.kg,
            "bag_weight_kg_used": q.bag_weight_kg_used,
            "conversion_source": q.conversion_source,
            "conversion_confidence": q.conversion_confidence.value,
            "pickup_earliest": pickup_earliest.isoformat(),
            "pickup_latest": pickup_latest.isoformat(),
            "delivery_latest": delivery_latest.isoformat(),
            "priority": str(rng.choice(["normal", "high", "low"], p=[0.7, 0.18, 0.12])),
            "input_mode": (InputMode.VOICE if is_voice else InputMode.TEXT).value,
            "feasibility_label": feasibility,
            "infeasible_reason": reason,
            "district": fn["district"],
            "state_code": fn["state_code"],
            "request_date": req_date.date().isoformat(),
            "is_synthetic": True,
            "dataset_version": cfg.dataset_version,
            **utt,
        })

    # --- hub -> shop replenishment ------------------------------------------
    s_idx = rng.integers(0, len(shops), n_shop)
    shop_loc_by_id = dict(zip(shop_locations["location_id"], shop_locations.index))
    # Replenishment originates at the nearest district depot-scale mandi town;
    # we reuse mandi locations as supply hubs for the prototype.
    hub_ids = mandi_locations["location_id"].to_numpy()

    for i in range(n_shop):
        sh = shops.iloc[int(s_idx[i])]
        loc_i = shop_loc_by_id.get(sh["location_id"])
        if loc_i is None:
            continue
        sl = shop_locations.loc[loc_i]

        # Replenish a few days of throughput at a time.
        days = float(rng.uniform(3, 21))
        target_kg = float(np.clip(sh["daily_demand_kg"] * days, 250, 30000))
        unit = Unit(rng.choice([Unit.TONNE.value, Unit.KG.value, Unit.BORI.value],
                               p=[0.5, 0.32, 0.18]))
        if unit is Unit.TONNE:
            value = float(np.round(target_kg / 1000.0, 2))
        elif unit is Unit.KG:
            value = float(np.round(target_kg, -1))
        else:
            value = float(max(1, round(target_kg / 50.0)))

        # Building material in bori has no crop, so bori here is genuinely
        # unresolvable -- exactly the case the converter must refuse to guess.
        q = normalize(value, unit, None, None)

        month = int(rng.integers(1, 13))
        day = int(rng.integers(1, 28))
        req_date = BASE_DATE.replace(month=month, day=day)
        pickup_earliest = req_date + timedelta(hours=float(rng.integers(6, 12)))
        pickup_latest = pickup_earliest + timedelta(hours=float(rng.uniform(3, 12)))
        delivery_latest = pickup_latest + timedelta(hours=float(rng.uniform(6, 48)))

        feasibility, reason = "feasible", None
        if q.kg is None:
            feasibility, reason = "unresolved_quantity", q.conversion_source
        elif q.kg > max_truck_capacity:
            feasibility, reason = "infeasible", "exceeds_max_fleet_capacity"

        rows.append({
            "request_id": content_id("request", "shop", sh["shop_id"], i),
            "requester_type": RequesterType.SHOP.value,
            "requester_id": sh["shop_id"],
            "origin_location_id": str(rng.choice(hub_ids)),
            "destination_mandi_id": pd.NA,
            "destination_shop_id": sh["shop_id"],
            "crop_id": pd.NA,
            "crop_key": pd.NA,
            "quantity_value": value,
            "quantity_unit": unit.value,
            "quantity_kg": q.kg,
            "bag_weight_kg_used": q.bag_weight_kg_used,
            "conversion_source": q.conversion_source,
            "conversion_confidence": q.conversion_confidence.value,
            "pickup_earliest": pickup_earliest.isoformat(),
            "pickup_latest": pickup_latest.isoformat(),
            "delivery_latest": delivery_latest.isoformat(),
            "priority": str(rng.choice(["normal", "high", "low"], p=[0.66, 0.22, 0.12])),
            "input_language": InputLanguage.HINGLISH.value,
            "input_mode": InputMode.TEXT.value,
            "raw_utterance": f"{sh['shop_category']} restock {value} {unit.value} for {sl['name_en']}",
            "template_family": "TF_SHOP_RESTOCK",
            "parsed_crop_conf": 0.0,
            "parsed_mandi_conf": 0.0,
            "parsed_quantity_conf": 0.95,
            "label_crop_key": None,
            "label_mandi_key": None,
            "label_quantity_value": value,
            "label_quantity_unit": unit.value,
            "is_incomplete": False,
            "missing_field": None,
            "feasibility_label": feasibility,
            "infeasible_reason": reason,
            "district": sl["district"],
            "state_code": sl["state_code"],
            "request_date": req_date.date().isoformat(),
            "is_synthetic": True,
            "dataset_version": cfg.dataset_version,
        })

    df = pd.DataFrame(rows)
    return df.reindex(columns=REQUEST_COLUMNS)
