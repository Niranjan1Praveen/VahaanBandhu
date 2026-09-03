"""Load canonical optimization instances from the Phase-A datasets.

This is the single entry point every solver uses. If a solver builds its own
distance matrix anywhere else, classical/quantum comparison stops being valid,
so nothing else in the codebase should construct a ``RoutingInstance``.
"""

from __future__ import annotations

import json
from functools import lru_cache

import numpy as np
import pandas as pd

from routing.models import RoutingInstance
from vb import config as C


@lru_cache(maxsize=1)
def _load_tables() -> dict[str, pd.DataFrame]:
    return {
        "instances": pd.read_csv(C.SYNTHETIC / "route_instances.csv"),
        "instance_requests": pd.read_csv(C.SYNTHETIC / "instance_requests.csv"),
        "requests": pd.read_csv(C.SYNTHETIC / "transport_requests.csv", low_memory=False),
        "locations": pd.read_csv(C.MASTER / "locations_master.csv"),
        "edges": pd.read_csv(C.SYNTHETIC / "route_edges.csv"),
        "trucks": pd.read_csv(C.SYNTHETIC / "trucks.csv"),
    }


def list_instances(
    *, quantum_ready: bool | None = None, problem_type: str | None = None,
    split: str | None = None, limit: int | None = None,
) -> pd.DataFrame:
    df = _load_tables()["instances"]
    if quantum_ready is not None:
        df = df[df["quantum_ready"] == quantum_ready]
    if problem_type:
        df = df[df["problem_type"] == problem_type]
    if split:
        df = df[df["split"] == split]
    return df.head(limit) if limit else df


def load_instance(instance_id: str, provider=None) -> RoutingInstance:
    """Materialise one instance into matrices.

    Node 0 is always the depot. Service nodes are the request origins, in the
    order recorded in the junction table, so a solution's stop indices mean the
    same thing to every solver.
    """
    t = _load_tables()
    inst = t["instances"].set_index("instance_id").loc[instance_id]
    members = t["instance_requests"]
    members = members[members["instance_id"] == instance_id].sort_values("node_order")

    reqs = t["requests"].set_index("request_id")
    loc = t["locations"].set_index("location_id")

    node_location_ids = [inst["depot_location_id"]]
    demands = [0.0]
    for _, m in members.iterrows():
        r = reqs.loc[m["request_id"]]
        node_location_ids.append(r["origin_location_id"])
        demands.append(float(m["demand_kg"]))

    coords = np.array([
        [float(loc.loc[lid, "latitude"]), float(loc.loc[lid, "longitude"])]
        for lid in node_location_ids
    ])

    if provider is None:
        from routing.providers.offline import OfflineGraphProvider
        provider = OfflineGraphProvider(t["edges"], t["locations"],
                                        scenario_id=inst["scenario_id"])

    # Pull every cost component from one pass, so toll/fuel/risk always describe
    # the same path as the distance they accompany.
    if hasattr(provider, "get_cost_matrices"):
        cm = provider.get_cost_matrices(
            origin_ids=node_location_ids, destination_ids=node_location_ids)
        dist, dur = cm["distance_km"], cm["time_min"]
        toll, fuel, risk = cm["toll_inr"], cm["fuel_inr"], cm["risk"]
    else:
        dist, dur = provider.get_matrix(
            None, None, origin_ids=node_location_ids,
            destination_ids=node_location_ids)
        toll = fuel = risk = None

    truck_ids = str(inst["truck_ids"]).split("|")
    trucks = t["trucks"].set_index("truck_id")
    capacities = [
        float(trucks.loc[tid, "capacity_kg"]) for tid in truck_ids if tid in trucks.index
    ] or [float(inst["capacity_constraint"])]

    time_windows = None
    if bool(inst["time_window_constraint"]):
        # Depot is open all day; each service node inherits its request's window,
        # expressed in minutes from midnight on the request date.
        tw: list[tuple[float, float]] = [(0.0, 24 * 60.0)]
        for _, m in members.iterrows():
            r = reqs.loc[m["request_id"]]
            start = pd.Timestamp(r["pickup_earliest"])
            end = pd.Timestamp(r["pickup_latest"])
            tw.append((start.hour * 60 + start.minute,
                       max(end.hour * 60 + end.minute, start.hour * 60 + start.minute + 30)))
        time_windows = tw

    ri = RoutingInstance(
        instance_id=instance_id,
        problem_type=str(inst["problem_type"]),
        depot_index=0,
        node_ids=node_location_ids,
        coords=coords,
        distance_matrix=dist,
        time_matrix=dur,
        demands=np.array(demands, dtype=float),
        vehicle_capacities=capacities,
        time_windows=time_windows,
        objective_weights=json.loads(inst["objective_weights_json"]),
        cost_snapshot_id=str(inst["cost_snapshot_id"]),
        scenario_id=str(inst["scenario_id"]),
        dataset_version=str(inst["dataset_version"]),
        graph_version=str(inst["graph_version"]),
        toll_matrix=toll,
        fuel_matrix=fuel,
        risk_matrix=risk,
    )
    ri.validate()
    return ri
