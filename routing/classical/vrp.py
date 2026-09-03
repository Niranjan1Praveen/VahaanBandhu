"""OR-Tools CVRP / VRPTW / circular-return solving.

OR-Tools works in integers, so distances are scaled to metres and times to
seconds before being handed over. Rounding at the wrong scale is a classic
source of "the solver found a better tour than the optimum": always scale up,
never truncate km to int.
"""

from __future__ import annotations

import time

import numpy as np
from ortools.constraint_solver import pywrapcp, routing_enums_pb2

from routing.models import RouteSolution, RoutingInstance
from vb.ids import content_id

DISTANCE_SCALE = 1000  # km -> metres
TIME_SCALE = 60        # minutes -> seconds


def _first_solution_strategy(name: str):
    return {
        "savings": routing_enums_pb2.FirstSolutionStrategy.SAVINGS,
        "path_cheapest_arc": routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC,
        "christofides": routing_enums_pb2.FirstSolutionStrategy.CHRISTOFIDES,
    }[name]


def solve_vrp(
    inst: RoutingInstance, *,
    time_limit_s: int = 10,
    first_solution: str = "path_cheapest_arc",
    local_search: str = "guided_local_search",
    seed: int = 0,
) -> RouteSolution:
    """Solve a CVRP or VRPTW with OR-Tools routing."""
    t0 = time.perf_counter()
    n = inst.n_nodes
    n_vehicles = len(inst.vehicle_capacities)

    manager = pywrapcp.RoutingIndexManager(n, n_vehicles, inst.depot_index)
    routing = pywrapcp.RoutingModel(manager)

    dist_int = np.rint(inst.distance_matrix * DISTANCE_SCALE).astype(np.int64)
    time_int = np.rint(inst.time_matrix * TIME_SCALE).astype(np.int64)

    def distance_cb(from_index, to_index):
        return int(dist_int[manager.IndexToNode(from_index), manager.IndexToNode(to_index)])

    transit = routing.RegisterTransitCallback(distance_cb)
    routing.SetArcCostEvaluatorOfAllVehicles(transit)

    demands_int = np.rint(inst.demands).astype(np.int64)

    def demand_cb(from_index):
        return int(demands_int[manager.IndexToNode(from_index)])

    demand_idx = routing.RegisterUnaryTransitCallback(demand_cb)
    routing.AddDimensionWithVehicleCapacity(
        demand_idx, 0,
        [int(round(c)) for c in inst.vehicle_capacities],
        True, "Capacity",
    )

    if inst.time_windows:
        def time_cb(from_index, to_index):
            return int(time_int[manager.IndexToNode(from_index), manager.IndexToNode(to_index)])

        time_idx = routing.RegisterTransitCallback(time_cb)
        routing.AddDimension(time_idx, 3600, 24 * 3600, False, "Time")
        time_dim = routing.GetDimensionOrDie("Time")
        for node, (start, end) in enumerate(inst.time_windows):
            if node == inst.depot_index:
                continue
            index = manager.NodeToIndex(node)
            if index >= 0:
                time_dim.CumulVar(index).SetRange(int(start * 60), int(end * 60))

    params = pywrapcp.DefaultRoutingSearchParameters()
    params.first_solution_strategy = _first_solution_strategy(first_solution)
    if local_search == "guided_local_search":
        params.local_search_metaheuristic = (
            routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH)
    params.time_limit.FromSeconds(time_limit_s)
    params.log_search = False

    solver_t0 = time.perf_counter()
    solution = routing.SolveWithParameters(params)
    solver_ms = (time.perf_counter() - solver_t0) * 1000

    if solution is None:
        return RouteSolution(
            solution_id=content_id("solution", inst.instance_id, "ortools", seed),
            instance_id=inst.instance_id, algorithm_family="classical",
            algorithm_name="ortools_routing", ordered_stops=[],
            total_distance_km=0.0, total_time_min=0.0, empty_distance_km=0.0,
            total_cost_inr=0.0, objective_value=float("inf"), feasible=False,
            constraint_violations=["no_solution_found"],
            runtime_ms=(time.perf_counter() - t0) * 1000, solver_runtime_ms=solver_ms,
            hyperparameters={"first_solution": first_solution,
                             "local_search": local_search, "time_limit_s": time_limit_s},
            seed=seed, cost_snapshot_id=inst.cost_snapshot_id,
            scenario_id=inst.scenario_id, dataset_version=inst.dataset_version,
            graph_version=inst.graph_version,
        )

    routes, total_km, total_min, empty_km = [], 0.0, 0.0, 0.0
    for v in range(n_vehicles):
        index = routing.Start(v)
        route, load = [], 0.0
        while not routing.IsEnd(index):
            node = manager.IndexToNode(index)
            route.append(node)
            nxt = solution.Value(routing.NextVar(index))
            nxt_node = manager.IndexToNode(nxt) if not routing.IsEnd(nxt) else inst.depot_index
            leg_km = float(inst.distance_matrix[node, nxt_node])
            total_km += leg_km
            total_min += float(inst.time_matrix[node, nxt_node])
            # The leg leaving the last customer back to the depot runs empty.
            if routing.IsEnd(nxt):
                empty_km += leg_km
            load += float(inst.demands[node])
            index = nxt
        route.append(inst.depot_index)
        if len(route) > 2:
            routes.append(route)

    w = inst.objective_weights
    fuel = total_km / 5.0 * 92.0
    objective = (w.get("distance_km", 1.0) * total_km
                 + w.get("time_min", 0.0) * total_min
                 + w.get("fuel_inr", 0.0) * fuel
                 + w.get("empty_km", 0.0) * empty_km)

    return RouteSolution(
        solution_id=content_id("solution", inst.instance_id, "ortools", seed),
        instance_id=inst.instance_id,
        algorithm_family="classical",
        algorithm_name="ortools_routing",
        ordered_stops=routes,
        total_distance_km=round(total_km, 3),
        total_time_min=round(total_min, 2),
        empty_distance_km=round(empty_km, 3),
        total_cost_inr=round(fuel, 2),
        objective_value=round(objective, 4),
        feasible=True,
        runtime_ms=(time.perf_counter() - t0) * 1000,
        solver_runtime_ms=solver_ms,
        hyperparameters={"first_solution": first_solution,
                         "local_search": local_search, "time_limit_s": time_limit_s},
        seed=seed,
        cost_snapshot_id=inst.cost_snapshot_id,
        scenario_id=inst.scenario_id,
        dataset_version=inst.dataset_version,
        graph_version=inst.graph_version,
    )
