"""Route graph construction and time-dependent cost scenarios.

Two things this module refuses to do:

* **Straight-line distance is not road distance.** Haversine is kept as a
  separate column for QA and as a feature, but every ``distance_km`` here is a
  road-distance *estimate* produced by applying a detour factor to the geodesic.
  When TomTom is configured, ``routing.providers.tomtom`` overwrites these with
  measured values for the edges that matter; the detour model is the offline
  fallback, and its ``source`` column says so.

* **Edges are directed.** A->B and B->A get separate rows and separate IDs,
  because one-ways, tolls and congestion are asymmetric.

Scenario costs never overwrite the baseline. Each scenario is a distinct set of
rows keyed by ``scenario_id``, so a solution can always be traced to the exact
cost snapshot it was computed against.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from vb.geo import haversine_matrix
from vb.ids import content_id, edge_id

BASELINE_SCENARIO = "SCN_BASELINE"


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    name: str
    # Multiplier on free-flow travel time.
    traffic_factor: float
    # Multiplier on the road-risk score.
    risk_factor: float
    description: str


SCENARIOS: list[Scenario] = [
    Scenario(BASELINE_SCENARIO, "baseline", 1.00, 1.00,
             "Free-flow reference costs. Never overwritten."),
    Scenario("SCN_MORNING_PEAK", "morning_peak", 1.45, 1.10,
             "Weekday 07:00-10:00. Heaviest congestion on NCR approaches."),
    Scenario("SCN_MIDDAY", "midday", 1.12, 1.00,
             "Weekday 11:00-16:00. Light congestion."),
    Scenario("SCN_EVENING_PEAK", "evening_peak", 1.52, 1.14,
             "Weekday 17:00-20:00. Peak plus mandi-gate queuing."),
    Scenario("SCN_NIGHT", "night", 0.88, 1.25,
             "22:00-05:00. Fast but higher risk; some yards shut."),
    Scenario("SCN_WEEKEND", "weekend", 1.05, 1.00,
             "Saturday/Sunday. Lower commercial traffic."),
    Scenario("SCN_HARVEST_PEAK", "harvest_peak", 1.38, 1.08,
             "Rabi/Kharif arrival surge. Mandi approach roads congested."),
    Scenario("SCN_MONSOON_RAIN", "monsoon_rain", 1.34, 1.60,
             "Active rain. Slower and materially riskier on unsealed links."),
]

SCENARIOS_BY_ID = {s.scenario_id: s for s in SCENARIOS}

# Fuel and toll assumptions, held in one place so experiments can vary them.
DIESEL_PRICE_INR_PER_L = 92.0
DEFAULT_KMPL = 5.0
TOLL_INR_PER_KM_HIGHWAY = 2.2
FREEFLOW_SPEED_KMPH = 46.0

# Real road paths are longer than the straight line between their endpoints.
# Short links detour more (village roads wind); long links approach highway
# directness. These factors are an offline stand-in for measured routing.
DETOUR_SHORT, DETOUR_LONG = 1.42, 1.18
DETOUR_KNEE_KM = 60.0


def _detour_factor(d_km: np.ndarray) -> np.ndarray:
    w = np.clip(d_km / DETOUR_KNEE_KM, 0.0, 1.0)
    return DETOUR_SHORT + (DETOUR_LONG - DETOUR_SHORT) * w


def build_route_edges(
    cfg, locations: pd.DataFrame, *, scenarios: list[Scenario] | None = None
) -> pd.DataFrame:
    """Build a sparse directed road-cost graph over the location master.

    The full all-pairs graph over even a prototype network is ~10^7 edges and
    mostly useless -- nobody routes a village in Bathinda to a shop in Gorakhpur.
    We therefore keep a k-nearest-neighbour graph plus every village/shop ->
    mandi link within range, which is the connectivity the logistics problem
    actually needs.
    """
    rng = np.random.default_rng(cfg.seed + 89)
    scenarios = scenarios or SCENARIOS

    loc = locations.reset_index(drop=True)
    lat = loc["latitude"].to_numpy(float)
    lon = loc["longitude"].to_numpy(float)
    ids = loc["location_id"].to_numpy()
    types = loc["location_type"].to_numpy()

    n = len(loc)
    geo = haversine_matrix(lat, lon)
    np.fill_diagonal(geo, np.inf)

    # k nearest neighbours per node.
    k = min(cfg.knn_edges, n - 1)
    knn = np.argsort(geo, axis=1)[:, :k]
    pairs: set[tuple[int, int]] = set()
    for i in range(n):
        for j in knn[i]:
            if geo[i, j] <= cfg.max_edge_km:
                pairs.add((i, int(j)))

    # Plus: every non-mandi node to its 3 nearest mandis, in both directions.
    mandi_idx = np.where(types == "mandi")[0]
    if len(mandi_idx):
        for i in range(n):
            if types[i] == "mandi":
                continue
            d_to_mandi = geo[i, mandi_idx]
            for rank in np.argsort(d_to_mandi)[:3]:
                j = int(mandi_idx[rank])
                if geo[i, j] <= cfg.max_edge_km:
                    pairs.add((i, j))
                    pairs.add((j, i))

    idx_i = np.fromiter((p[0] for p in pairs), int, len(pairs))
    idx_j = np.fromiter((p[1] for p in pairs), int, len(pairs))
    geodesic = geo[idx_i, idx_j]

    road_km = geodesic * _detour_factor(geodesic)
    # Directional asymmetry: one-ways, gradients and lane counts make the two
    # directions differ by a few percent.
    road_km = road_km * rng.normal(1.0, 0.025, len(road_km))
    road_km = np.round(np.clip(road_km, 0.15, None), 3)

    freeflow_min = np.round(road_km / FREEFLOW_SPEED_KMPH * 60.0, 2)

    # Highway share rises with trip length; drives tolls and risk.
    highway_share = np.clip(road_km / 120.0, 0.0, 0.85)
    road_class_mix = np.where(highway_share > 0.55, "highway_dominant",
                       np.where(highway_share > 0.25, "mixed", "rural_dominant"))
    surface_risk = np.round(np.clip(
        0.42 - 0.34 * highway_share + rng.normal(0, 0.07, len(road_km)), 0.02, 0.95), 3)

    truck_accessible = surface_risk < 0.80

    frames = []
    for sc in scenarios:
        traffic_min = np.round(freeflow_min * sc.traffic_factor
                               * rng.normal(1.0, 0.05, len(road_km)), 2)
        toll = np.round(road_km * highway_share * TOLL_INR_PER_KM_HIGHWAY, 2)
        fuel = np.round(road_km / DEFAULT_KMPL * DIESEL_PRICE_INR_PER_L, 2)
        frames.append(pd.DataFrame({
            "edge_id": [edge_id(ids[a], ids[b], sc.scenario_id)
                        for a, b in zip(idx_i, idx_j)],
            "origin_location_id": ids[idx_i],
            "destination_location_id": ids[idx_j],
            "distance_km": road_km,
            "haversine_km": np.round(geodesic, 3),
            "freeflow_time_min": freeflow_min,
            "traffic_time_min": traffic_min,
            "road_class_mix": road_class_mix,
            "toll_cost_inr": toll,
            "fuel_cost_inr": fuel,
            "truck_accessible": truck_accessible,
            "surface_risk_score": np.round(surface_risk * sc.risk_factor, 3),
            "source": "offline_detour_model_v1",
            "snapshot_time": "2026-01-01T00:00:00Z",
            "scenario_id": sc.scenario_id,
            "is_synthetic": True,
            "dataset_version": cfg.dataset_version,
        }))

    return pd.concat(frames, ignore_index=True)


def build_scenarios_table(cfg) -> pd.DataFrame:
    return pd.DataFrame([{
        "scenario_id": s.scenario_id,
        "name": s.name,
        "traffic_factor": s.traffic_factor,
        "risk_factor": s.risk_factor,
        "description": s.description,
        "is_baseline": s.scenario_id == BASELINE_SCENARIO,
        "dataset_version": cfg.dataset_version,
    } for s in SCENARIOS])


def cost_snapshot_id(scenario_id: str, dataset_version: str, graph_version: str) -> str:
    """Identifies the exact cost matrix a solution was computed against.

    Comparing a classical and a quantum result is only meaningful if both carry
    the same snapshot ID.
    """
    return content_id("cost_snapshot", scenario_id, dataset_version, graph_version)
