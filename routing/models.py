"""Normalized routing types.

The optimization layer consumes these, never raw provider JSON. That boundary
is what lets TomTom be swapped, mocked or taken offline without touching a
solver.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone

import numpy as np


@dataclass(frozen=True)
class LatLon:
    lat: float
    lon: float

    def as_tuple(self) -> tuple[float, float]:
        return (self.lat, self.lon)


@dataclass
class RouteCandidate:
    """One feasible path between two points, described in decision-relevant terms.

    ``empty_km`` and ``circular_logistics_score`` are what separate this from a
    generic routing result: VahaanBandhu is choosing between routes on total
    operational value, not on arrival time alone.
    """

    route_id: str
    origin_id: str
    destination_id: str
    distance_km: float
    travel_time_min: float
    traffic_delay_min: float = 0.0
    toll_cost_inr: float = 0.0
    estimated_fuel_cost_inr: float = 0.0
    road_risk_score: float = 0.0
    truck_accessibility_score: float = 1.0
    loaded_km: float = 0.0
    empty_km: float = 0.0
    capacity_utilization: float = 0.0
    circular_logistics_score: float = 0.0
    geometry: list[tuple[float, float]] = field(default_factory=list)
    traffic_snapshot_time: str | None = None
    source: str = "unknown"

    def to_dict(self) -> dict:
        d = asdict(self)
        d.pop("geometry", None)
        d["n_geometry_points"] = len(self.geometry)
        return d


@dataclass
class RoutingInstance:
    """A canonical optimization problem, loaded from ``route_instances.csv``.

    ``cost_snapshot_id`` is the load-bearing field. Two solver results are only
    comparable if they carry the same one, and every solver records it.
    """

    instance_id: str
    problem_type: str
    depot_index: int
    node_ids: list[str]
    coords: np.ndarray            # (n, 2) lat/lon, depot at depot_index
    distance_matrix: np.ndarray   # (n, n) km, directed
    time_matrix: np.ndarray       # (n, n) minutes, directed
    demands: np.ndarray           # (n,) kg, depot demand is 0
    vehicle_capacities: list[float]
    time_windows: list[tuple[float, float]] | None
    objective_weights: dict[str, float]
    cost_snapshot_id: str
    scenario_id: str
    dataset_version: str
    graph_version: str

    # Additional cost components, all derived from the SAME shortest paths as
    # distance_matrix. Optional so older callers keep working, but required for
    # the project's real multi-objective score -- without them a solver would be
    # optimizing distance alone while claiming to optimize cost.
    toll_matrix: np.ndarray | None = None
    fuel_matrix: np.ndarray | None = None
    risk_matrix: np.ndarray | None = None

    @property
    def n_nodes(self) -> int:
        return len(self.node_ids)

    @property
    def n_customers(self) -> int:
        return self.n_nodes - 1

    def validate(self) -> None:
        n = self.n_nodes
        if self.distance_matrix.shape != (n, n):
            raise ValueError(f"distance matrix is {self.distance_matrix.shape}, expected ({n},{n})")
        if self.time_matrix.shape != (n, n):
            raise ValueError(f"time matrix is {self.time_matrix.shape}, expected ({n},{n})")
        if len(self.demands) != n:
            raise ValueError("demand vector length does not match node count")
        if self.demands[self.depot_index] != 0:
            raise ValueError("depot must have zero demand")
        if np.any(np.diag(self.distance_matrix) != 0):
            raise ValueError("distance matrix has a non-zero diagonal")


@dataclass
class RouteSolution:
    """A solver result, carrying enough provenance to be compared honestly."""

    solution_id: str
    instance_id: str
    algorithm_family: str        # classical | quantum | hybrid
    algorithm_name: str
    ordered_stops: list[list[int]]
    total_distance_km: float
    total_time_min: float
    empty_distance_km: float
    total_cost_inr: float
    objective_value: float
    feasible: bool
    constraint_violations: list[str] = field(default_factory=list)
    runtime_ms: float = 0.0
    solver_runtime_ms: float = 0.0
    optimality_gap: float | None = None
    hyperparameters: dict = field(default_factory=dict)
    seed: int | None = None

    # Quantum-only fields. Absent for classical runs rather than zero-filled,
    # so a reader can tell "not applicable" from "measured zero".
    quantum_backend: str | None = None
    quantum_qubits: int | None = None
    quantum_depth: int | None = None
    quantum_shots: int | None = None
    quantum_optimizer: str | None = None
    qubo_version: str | None = None
    encoding_version: str | None = None

    # Provenance of the exact cost data used.
    cost_snapshot_id: str = ""
    scenario_id: str = ""
    dataset_version: str = ""
    graph_version: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_row(self) -> dict:
        d = asdict(self)
        d["ordered_stops"] = "|".join(
            ",".join(str(i) for i in route) for route in self.ordered_stops
        )
        d["constraint_violations"] = ";".join(self.constraint_violations)
        import json
        d["hyperparameters_json"] = json.dumps(self.hyperparameters, sort_keys=True)
        d.pop("hyperparameters")
        return d
