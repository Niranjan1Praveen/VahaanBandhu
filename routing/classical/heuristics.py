"""TSP/VRP heuristics and an exact solver for small instances.

The exact solver exists specifically to serve the quantum comparison: for
instances small enough to brute-force, we know the true optimum, so a QAOA
result can be reported as an honest optimality gap instead of "close to a
heuristic". Without a ground truth, "the quantum solution matched the classical
one" says nothing about quality.
"""

from __future__ import annotations

import itertools
import time
from dataclasses import dataclass

import numpy as np


@dataclass
class TourResult:
    tour: list[int]
    cost: float
    runtime_ms: float
    algorithm: str
    is_optimal: bool = False


def tour_cost(tour: list[int], D: np.ndarray) -> float:
    """Closed-tour cost, returning to the start."""
    return float(sum(D[tour[i], tour[(i + 1) % len(tour)]] for i in range(len(tour))))


def brute_force_tsp(D: np.ndarray, depot: int = 0, max_nodes: int = 10) -> TourResult:
    """Exact TSP by enumeration. Ground truth for the quantum benchmark.

    Refuses above ``max_nodes`` rather than silently taking hours: 10 nodes is
    9! = 362,880 permutations, and 12 would be 39.9 million.
    """
    n = D.shape[0]
    if n > max_nodes:
        raise ValueError(f"{n} nodes exceeds the exact-solver limit of {max_nodes}")
    t0 = time.perf_counter()
    others = [i for i in range(n) if i != depot]
    best, best_cost = None, float("inf")
    for perm in itertools.permutations(others):
        tour = [depot, *perm]
        c = tour_cost(tour, D)
        if c < best_cost:
            best, best_cost = tour, c
    return TourResult(best, best_cost, (time.perf_counter() - t0) * 1000,
                      "brute_force_exact", is_optimal=True)


def nearest_neighbour(D: np.ndarray, depot: int = 0) -> TourResult:
    t0 = time.perf_counter()
    n = D.shape[0]
    unvisited = set(range(n)) - {depot}
    tour, current = [depot], depot
    while unvisited:
        nxt = min(unvisited, key=lambda j: D[current, j])
        tour.append(nxt)
        unvisited.remove(nxt)
        current = nxt
    return TourResult(tour, tour_cost(tour, D),
                      (time.perf_counter() - t0) * 1000, "nearest_neighbour")


def two_opt(D: np.ndarray, tour: list[int], max_iter: int = 1000) -> TourResult:
    """2-opt local search. Segment reversal on an asymmetric matrix changes the
    cost of every reversed edge, so the whole tour is re-evaluated rather than
    using the symmetric delta shortcut."""
    t0 = time.perf_counter()
    best = list(tour)
    best_cost = tour_cost(best, D)
    for _ in range(max_iter):
        improved = False
        for i in range(1, len(best) - 1):
            for j in range(i + 1, len(best)):
                cand = best[:i] + best[i:j + 1][::-1] + best[j + 1:]
                c = tour_cost(cand, D)
                if c < best_cost - 1e-9:
                    best, best_cost, improved = cand, c, True
        if not improved:
            break
    return TourResult(best, best_cost, (time.perf_counter() - t0) * 1000, "two_opt")


def simulated_annealing(
    D: np.ndarray, depot: int = 0, *, seed: int = 0,
    iterations: int = 20000, t_start: float = 100.0, t_end: float = 0.1,
) -> TourResult:
    rng = np.random.default_rng(seed)
    t0 = time.perf_counter()
    n = D.shape[0]
    current = [depot] + list(rng.permutation([i for i in range(n) if i != depot]))
    current_cost = tour_cost(current, D)
    best, best_cost = list(current), current_cost

    for step in range(iterations):
        temp = t_start * (t_end / t_start) ** (step / max(iterations - 1, 1))
        i, j = sorted(rng.choice(range(1, n), size=2, replace=False))
        cand = current[:i] + current[i:j + 1][::-1] + current[j + 1:]
        c = tour_cost(cand, D)
        if c < current_cost or rng.random() < np.exp(-(c - current_cost) / max(temp, 1e-9)):
            current, current_cost = cand, c
            if c < best_cost:
                best, best_cost = list(cand), c

    return TourResult(best, best_cost, (time.perf_counter() - t0) * 1000,
                      "simulated_annealing")
