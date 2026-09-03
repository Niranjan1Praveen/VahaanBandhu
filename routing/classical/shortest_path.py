"""Shortest-path baselines over the road graph.

A* uses a great-circle admissible heuristic. Admissibility matters: the
heuristic must never overestimate the remaining road distance, and since road
distance is always at least the geodesic, haversine is safe. Scaling it up to
"tighten" the heuristic would break optimality guarantees, which is exactly the
kind of silent quality loss a benchmark would not catch.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import networkx as nx

from vb.geo import haversine_km


@dataclass
class PathResult:
    path: list[str]
    cost: float
    distance_km: float
    time_min: float
    runtime_ms: float
    algorithm: str
    nodes_expanded: int | None = None


def _accumulate(G: nx.DiGraph, path: list[str]) -> tuple[float, float]:
    dist = sum(G[u][v]["distance_km"] for u, v in zip(path[:-1], path[1:]))
    time_min = sum(G[u][v]["traffic_min"] for u, v in zip(path[:-1], path[1:]))
    return dist, time_min


def dijkstra(G: nx.DiGraph, source: str, target: str, weight: str = "distance_km") -> PathResult:
    t0 = time.perf_counter()
    path = nx.shortest_path(G, source, target, weight=weight)
    cost = nx.shortest_path_length(G, source, target, weight=weight)
    dist, tmin = _accumulate(G, path)
    return PathResult(path, float(cost), dist, tmin,
                      (time.perf_counter() - t0) * 1000, "dijkstra")


def astar(
    G: nx.DiGraph, source: str, target: str,
    coords: dict[str, tuple[float, float]], weight: str = "distance_km",
) -> PathResult:
    def h(u: str, v: str) -> float:
        if u not in coords or v not in coords:
            return 0.0
        a, b = coords[u], coords[v]
        # Admissible: road distance >= great-circle distance, always.
        return haversine_km(a[0], a[1], b[0], b[1])

    t0 = time.perf_counter()
    path = nx.astar_path(G, source, target, heuristic=h, weight=weight)
    cost = sum(G[u][v][weight] for u, v in zip(path[:-1], path[1:]))
    dist, tmin = _accumulate(G, path)
    return PathResult(path, float(cost), dist, tmin,
                      (time.perf_counter() - t0) * 1000, "astar")


def k_shortest_paths(
    G: nx.DiGraph, source: str, target: str, k: int = 3, weight: str = "traffic_min"
) -> list[PathResult]:
    """Distinct candidate corridors, which is what the selection layer scores."""
    t0 = time.perf_counter()
    out: list[PathResult] = []
    try:
        gen = nx.shortest_simple_paths(G, source, target, weight=weight)
        for i, path in enumerate(gen):
            if i >= k:
                break
            cost = sum(G[u][v][weight] for u, v in zip(path[:-1], path[1:]))
            dist, tmin = _accumulate(G, path)
            out.append(PathResult(path, float(cost), dist, tmin,
                                  (time.perf_counter() - t0) * 1000, f"k_shortest[{i}]"))
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        pass
    return out
