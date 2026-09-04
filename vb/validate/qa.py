"""Geospatial, referential and statistical QA.

Writes machine-readable results to ``Data/qa/`` so the QA report is generated
from measurements rather than from claims.

An important limitation is recorded honestly rather than papered over: the routing research
has no district boundary polygons, so containment is checked against a circular
district envelope derived from the curated centroid and radius. That catches
gross misplacement but will not catch a point just over a real district border.
the application must swap in LGD/Census polygons.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from vb.config import QA
from vb.geo import haversine_km, in_coarse_bbox
from vb.reference import districts as dref


def geospatial_qa(locations: pd.DataFrame, edges: pd.DataFrame) -> dict:
    """Coordinate sanity, containment and duplicate detection."""
    res: dict[str, object] = {}
    n = len(locations)

    in_box = locations.apply(
        lambda r: in_coarse_bbox(r["latitude"], r["longitude"]), axis=1
    )
    res["n_locations"] = n
    res["n_outside_coarse_bbox"] = int((~in_box).sum())

    # Envelope containment: distance from the district centroid must not exceed
    # the district radius (with a 25% tolerance for the crude circular model).
    offenders, distances = [], []
    for _, r in locations.iterrows():
        d = dref.BY_NAME.get(r["district"])
        if d is None:
            offenders.append({"location_id": r["location_id"],
                              "reason": "unknown_district", "district": r["district"]})
            continue
        km = haversine_km(r["latitude"], r["longitude"], d.lat, d.lon)
        distances.append(km)
        if km > d.radius_km * 1.25:
            offenders.append({
                "location_id": r["location_id"], "district": r["district"],
                "reason": "outside_district_envelope",
                "km_from_centroid": round(km, 2), "envelope_km": d.radius_km,
            })
    res["n_outside_district_envelope"] = len(
        [o for o in offenders if o.get("reason") == "outside_district_envelope"]
    )
    res["envelope_distance_km_p50"] = round(float(np.median(distances)), 2) if distances else None
    res["envelope_distance_km_p99"] = round(float(np.percentile(distances, 99)), 2) if distances else None
    res["containment_method"] = "circular_district_envelope"
    res["containment_limitation"] = (
        "No boundary polygons available in the routing research. A point just across a real "
        "district border will not be detected. the application must use LGD polygons."
    )

    # Exact duplicate coordinates. Two distinct entities at identical 6-decimal
    # coordinates is ~0.1 m apart, which is a generator collision, not a fact.
    dupes = locations.duplicated(subset=["latitude", "longitude"], keep=False)
    res["n_duplicate_coordinates"] = int(dupes.sum())

    # NCR flag consistency: membership is per-district and must never be
    # inferred from the state.
    bad_ncr = 0
    for _, r in locations.iterrows():
        expected = dref.is_ncr(r["district"])
        if bool(r["in_ncr"]) != expected:
            bad_ncr += 1
    res["n_ncr_flag_mismatches"] = bad_ncr

    # Edge sanity against the geodesic lower bound.
    bad_edges = edges[edges["distance_km"] < edges["haversine_km"] * 0.98]
    res["n_edges"] = int(len(edges))
    res["n_edges_shorter_than_geodesic"] = int(len(bad_edges))
    res["n_self_loop_edges"] = int(
        (edges["origin_location_id"] == edges["destination_location_id"]).sum()
    )
    # Asymmetry is the point of a directed graph; confirm it actually exists.
    base = edges[edges["scenario_id"] == "SCN_BASELINE"]
    fwd = base.set_index(["origin_location_id", "destination_location_id"])["distance_km"]
    rev = base.set_index(["destination_location_id", "origin_location_id"])["distance_km"]
    common = fwd.index.intersection(rev.index)
    if len(common):
        diff = (fwd.loc[common].to_numpy() - rev.loc[common].to_numpy())
        res["n_bidirectional_pairs"] = int(len(common))
        res["mean_abs_direction_asymmetry_km"] = round(float(np.mean(np.abs(diff))), 4)

    res["passed"] = (
        res["n_outside_coarse_bbox"] == 0
        and res["n_edges_shorter_than_geodesic"] == 0
        and res["n_self_loop_edges"] == 0
        and res["n_ncr_flag_mismatches"] == 0
    )
    _write("geospatial_qa", res, offenders[:500])
    return res


def referential_qa(tables: dict[str, pd.DataFrame]) -> dict:
    """Foreign-key integrity across the relational model."""
    loc_ids = set(tables["locations_master"]["location_id"])
    res: dict[str, object] = {}

    def missing(child: str, col: str, parent_ids: set) -> int:
        if child not in tables or col not in tables[child]:
            return -1
        vals = tables[child][col].dropna()
        return int((~vals.isin(parent_ids)).sum())

    res["mandis.location_id_missing"] = missing("mandis", "location_id", loc_ids)
    res["shops.location_id_missing"] = missing("shops", "location_id", loc_ids)
    res["farmer_nodes.village_location_id_missing"] = missing(
        "farmer_nodes", "village_location_id", loc_ids)
    res["trucks.home_location_id_missing"] = missing("trucks", "home_location_id", loc_ids)
    res["route_edges.origin_missing"] = missing("route_edges", "origin_location_id", loc_ids)
    res["route_edges.destination_missing"] = missing(
        "route_edges", "destination_location_id", loc_ids)
    res["route_instances.depot_missing"] = missing(
        "route_instances", "depot_location_id", loc_ids)

    mandi_ids = set(tables["mandis"]["mandi_id"])
    res["requests.destination_mandi_missing"] = missing(
        "transport_requests", "destination_mandi_id", mandi_ids)
    res["farmer_nodes.market_preference_missing"] = missing(
        "farmer_nodes", "market_preference_mandi_id", mandi_ids)

    req_ids = set(tables["transport_requests"]["request_id"])
    inst_ids = set(tables["route_instances"]["instance_id"])
    res["instance_requests.request_missing"] = missing(
        "instance_requests", "request_id", req_ids)
    res["instance_requests.instance_missing"] = missing(
        "instance_requests", "instance_id", inst_ids)

    res["passed"] = all(v <= 0 for k, v in res.items() if k.endswith("missing"))
    _write("referential_qa", res, [])
    return res


def statistical_qa(tables: dict[str, pd.DataFrame]) -> dict:
    """Distribution summaries and impossible-value detection."""
    req = tables["transport_requests"]
    trk = tables["trucks"]
    edges = tables["route_edges"]
    res: dict[str, object] = {}

    res["requests_by_state"] = req["state_code"].value_counts().to_dict()
    res["requests_by_language"] = req["input_language"].value_counts().to_dict()
    res["requests_by_mode"] = req["input_mode"].value_counts().to_dict()
    res["requests_by_feasibility"] = req["feasibility_label"].value_counts().to_dict()
    res["requests_by_unit"] = req["quantity_unit"].value_counts().to_dict()
    res["conversion_confidence"] = req["conversion_confidence"].value_counts().to_dict()
    res["top_crops"] = req["crop_key"].value_counts().head(12).to_dict()

    qk = req["quantity_kg"].dropna()
    res["quantity_kg"] = {
        "n": int(len(qk)), "min": float(qk.min()), "p50": float(qk.median()),
        "p95": float(qk.quantile(0.95)), "max": float(qk.max()),
        "n_non_positive": int((qk <= 0).sum()),
    }
    res["trucks_by_class"] = trk["vehicle_class"].value_counts().to_dict()
    res["trucks_by_fuel"] = trk["fuel_type"].value_counts().to_dict()
    res["capacity_kg"] = {
        "min": float(trk["capacity_kg"].min()), "p50": float(trk["capacity_kg"].median()),
        "max": float(trk["capacity_kg"].max()),
    }
    res["shops_by_category"] = tables["shops"]["shop_category"].value_counts().to_dict()
    res["farm_size_ha"] = {
        "p50": float(tables["farmer_nodes"]["farm_size_ha"].median()),
        "p95": float(tables["farmer_nodes"]["farm_size_ha"].quantile(0.95)),
        "max": float(tables["farmer_nodes"]["farm_size_ha"].max()),
    }
    base = edges[edges["scenario_id"] == "SCN_BASELINE"]
    res["edge_distance_km"] = {
        "p50": float(base["distance_km"].median()),
        "p95": float(base["distance_km"].quantile(0.95)),
        "max": float(base["distance_km"].max()),
    }
    res["implied_speed_kmph"] = {
        "p50": float((base["distance_km"] / (base["traffic_time_min"] / 60)).median()),
    }

    # Impossible values. These should all be zero.
    res["violations"] = {
        "non_positive_quantity": int((qk <= 0).sum()),
        "negative_farm_size": int((tables["farmer_nodes"]["farm_size_ha"] <= 0).sum()),
        "zero_capacity_trucks": int((trk["capacity_kg"] <= 0).sum()),
        "implausible_speed_over_120kmph": int(
            ((base["distance_km"] / (base["traffic_time_min"] / 60)) > 120).sum()),
    }
    res["passed"] = all(v == 0 for v in res["violations"].values())
    _write("statistical_qa", res, [])
    return res


def _write(name: str, summary: dict, offenders: list) -> None:
    QA.mkdir(parents=True, exist_ok=True)
    payload = {"generated_at": datetime.now(timezone.utc).isoformat(), **summary}
    (QA / f"{name}.json").write_text(
        json.dumps(payload, indent=2, default=str, ensure_ascii=False), encoding="utf-8"
    )
    if offenders:
        pd.DataFrame(offenders).to_csv(QA / f"{name}_offenders.csv", index=False)
