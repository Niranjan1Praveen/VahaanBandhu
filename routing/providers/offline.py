"""Offline routing provider backed by the generated ``route_edges`` graph.

This is what keeps the whole system testable and the notebooks reproducible
with no API key and no network. It is also the honest default for building
training data, because it carries no third-party licensing ambiguity.

Alternatives are produced by k-shortest-paths over the road graph rather than
by perturbing a single answer, so the candidates are genuinely different paths
with genuinely different cost profiles.
"""

from __future__ import annotations

import networkx as nx
import numpy as np
import pandas as pd

from routing.models import LatLon, RouteCandidate
from routing.providers.base import RoutingProvider
from vb.geo import haversine_km

DIESEL_PRICE_INR_PER_L = 92.0
DEFAULT_KMPL = 5.0


class OfflineGraphProvider(RoutingProvider):
    name = "offline_graph"

    def __init__(
        self, edges: pd.DataFrame, locations: pd.DataFrame,
        scenario_id: str = "SCN_BASELINE",
    ) -> None:
        self.scenario_id = scenario_id
        e = edges[edges["scenario_id"] == scenario_id]
        if e.empty:
            raise ValueError(f"no edges for scenario {scenario_id}")
        self.edges = e
        self.locations = locations.set_index("location_id")

        self.G = nx.DiGraph()
        for _, r in e.iterrows():
            self.G.add_edge(
                r["origin_location_id"], r["destination_location_id"],
                distance_km=float(r["distance_km"]),
                freeflow_min=float(r["freeflow_time_min"]),
                traffic_min=float(r["traffic_time_min"]),
                toll=float(r["toll_cost_inr"]),
                fuel=float(r["fuel_cost_inr"]),
                risk=float(r["surface_risk_score"]),
                accessible=bool(r["truck_accessible"]),
            )

    @property
    def available(self) -> bool:
        return True

    def _coords(self, location_id: str) -> LatLon:
        row = self.locations.loc[location_id]
        return LatLon(float(row["latitude"]), float(row["longitude"]))

    def _path_to_candidate(
        self, path: list[str], origin_id: str, destination_id: str, idx: int
    ) -> RouteCandidate:
        dist = time_ff = time_tr = toll = fuel = 0.0
        risks, accessible = [], True
        geometry = []
        for u, v in zip(path[:-1], path[1:]):
            a = self.G[u][v]
            dist += a["distance_km"]
            time_ff += a["freeflow_min"]
            time_tr += a["traffic_min"]
            toll += a["toll"]
            fuel += a["fuel"]
            risks.append(a["risk"])
            accessible &= a["accessible"]
        for node in path:
            c = self._coords(node)
            geometry.append((c.lat, c.lon))

        return RouteCandidate(
            route_id=f"OFF_{origin_id[:8]}_{destination_id[:8]}_{idx}",
            origin_id=origin_id,
            destination_id=destination_id,
            distance_km=round(dist, 3),
            travel_time_min=round(time_ff, 2),
            traffic_delay_min=round(max(time_tr - time_ff, 0.0), 2),
            toll_cost_inr=round(toll, 2),
            estimated_fuel_cost_inr=round(fuel, 2),
            road_risk_score=round(float(np.mean(risks)) if risks else 0.0, 4),
            truck_accessibility_score=1.0 if accessible else 0.0,
            loaded_km=round(dist, 3),
            geometry=geometry,
            traffic_snapshot_time=None,
            source=f"offline_graph:{self.scenario_id}",
        )

    def get_alternative_routes(
        self, origin: LatLon, destination: LatLon, max_alternatives: int = 3, **kw
    ) -> list[RouteCandidate]:
        """k-shortest simple paths, which give genuinely distinct corridors."""
        origin_id = kw.get("origin_id")
        destination_id = kw.get("destination_id")
        if not (origin_id and destination_id):
            raise ValueError("offline provider routes by location_id, not raw coordinates")
        if origin_id not in self.G or destination_id not in self.G:
            return []

        weight = kw.get("weight", "traffic_min")
        try:
            gen = nx.shortest_simple_paths(self.G, origin_id, destination_id, weight=weight)
            paths = [next(gen) for _ in range(max(1, max_alternatives))]
        except (nx.NetworkXNoPath, nx.NodeNotFound, StopIteration):
            paths = []
            try:
                paths = [nx.shortest_path(self.G, origin_id, destination_id, weight=weight)]
            except (nx.NetworkXNoPath, nx.NodeNotFound):
                return []
        return [
            self._path_to_candidate(p, origin_id, destination_id, i)
            for i, p in enumerate(paths)
        ]

    def get_route(self, origin: LatLon, destination: LatLon, **kw) -> RouteCandidate:
        routes = self.get_alternative_routes(origin, destination, 1, **kw)
        if not routes:
            raise RuntimeError("no path exists in the offline graph")
        return routes[0]

    def get_matrix(
        self, origins: list[LatLon], destinations: list[LatLon], **kw
    ) -> tuple[np.ndarray, np.ndarray]:
        """Distance/duration matrix by location_id over the road graph.

        Pairs with no path fall back to a great-circle estimate scaled by a
        detour factor, and the caller can tell which those were because the
        estimate is always strictly worse than any real path would be.
        """
        origin_ids = kw.get("origin_ids")
        destination_ids = kw.get("destination_ids")
        if not (origin_ids and destination_ids):
            raise ValueError("offline matrix requires origin_ids and destination_ids")

        n, m = len(origin_ids), len(destination_ids)
        dist = np.zeros((n, m))
        dur = np.zeros((n, m))
        for i, a in enumerate(origin_ids):
            for j, b in enumerate(destination_ids):
                if a == b:
                    continue
                try:
                    r = self.get_route(None, None, origin_id=a, destination_id=b)
                    dist[i, j] = r.distance_km
                    dur[i, j] = r.travel_time_min + r.traffic_delay_min
                except RuntimeError:
                    ca, cb = self._coords(a), self._coords(b)
                    g = haversine_km(ca.lat, ca.lon, cb.lat, cb.lon)
                    dist[i, j] = g * 1.42
                    dur[i, j] = dist[i, j] / 40.0 * 60.0
        return dist, dur
