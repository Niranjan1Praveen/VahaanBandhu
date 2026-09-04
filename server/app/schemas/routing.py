"""Application-facing routing contract — the frozen research/application boundary.

`RoutingRequest` and `RouteSolution` are versioned application types. They
deliberately expose **no** VB-QER internals: no QUBO matrices, no bitstrings, no
QAOA parameters, no artifact payloads. The application knows it asked for a
route and got one, plus enough provenance to reason about staleness.

the routing research may replace every internal component behind this boundary
without any frontend or API change.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from server.app.schemas.common import GeoPoint, Quantity, UserRole


class RoutingProfile(str, Enum):
    """Execution profiles *inside* VB-QER. Not different algorithms.

    VB-QER remains the fixed final algorithm; these select how much of its
    ensemble runs, trading latency against solution quality.
    """

    LIVE = "live"        # latency-aware subset + validated artifacts
    QUALITY = "quality"  # full classical ensemble
    RESEARCH = "research"  # everything, with instrumentation


class RoutingContext(str, Enum):
    LIVE = "live"       # current traffic where a provider is configured
    OFFLINE = "offline"  # research road graph adapter


class RouteStop(BaseModel):
    location_id: str | None = None
    name: str | None = None
    point: GeoPoint | None = None
    kind: str = Field(default="waypoint",
                      description="origin | farm | mandi | dealer | depot | waypoint")


class RoutingRequest(BaseModel):
    """What the application asks VB-QER for."""

    origin: RouteStop
    destination: RouteStop
    stops: list[RouteStop] = Field(default_factory=list)

    role: UserRole
    request_id: str | None = None

    vehicle_id: str | None = None
    vehicle_class: str | None = None
    capacity_kg: float | None = Field(default=None, gt=0)
    load: Quantity | None = None

    mandi_id: str | None = None
    dealer_requirement_id: str | None = None

    scenario_id: str = "SCN_BASELINE"
    context: RoutingContext = RoutingContext.OFFLINE
    profile: RoutingProfile = RoutingProfile.LIVE
    consider_return_load: bool = True


class ReturnLoadOpportunity(BaseModel):
    """A circular-logistics match — the product's core differentiator."""

    available: bool = False
    requirement_id: str | None = None
    dealer_name: str | None = None
    destination: RouteStop | None = None
    load_kg: float | None = None
    detour_km: float | None = None
    empty_km_avoided: float | None = None
    estimated_revenue_inr: float | None = None


class RouteExplanation(BaseModel):
    """User-facing reasoning. Not a research report.

    ``reasons_hi`` carries Hindi strings for the primary interface; the
    structured fields let the UI render its own phrasing.
    """

    reasons_hi: list[str] = Field(default_factory=list)
    reasons_en: list[str] = Field(default_factory=list)
    primary_factor: str | None = None
    margin_is_decisive: bool = True


class OptimizationMetadata(BaseModel):
    """Provenance the application legitimately needs.

    Enough to reason about staleness and to trace a decision; not enough to
    leak research internals.
    """

    vbqer_version: str
    dataset_version: str | None = None
    graph_version: str | None = None
    cost_snapshot_id: str | None = None
    artifact_version: str | None = None
    profile: RoutingProfile = RoutingProfile.LIVE
    problem_type: str | None = None
    final_route_source: str | None = None
    quantum_component_invoked: bool = False
    quantum_artifact_used: bool = False
    quantum_artifact_source: str = "none"
    # Always False. There is no live QPU call in the HTTP request path.
    quantum_hardware_called_live: bool = False
    computed_at: datetime | None = None
    cached: bool = False
    compute_ms: float | None = None


class RouteSolution(BaseModel):
    """What the application gets back."""

    route_id: str
    request_id: str | None = None

    stops: list[RouteStop] = Field(default_factory=list)
    geometry_ref: str | None = Field(
        default=None, description="Reference to stored geometry, not inline coords")
    polyline: list[list[float]] = Field(
        default_factory=list, description="[[lat, lon], ...] for map rendering")

    distance_km: float
    estimated_time_min: float
    objective: float
    feasible: bool
    violations: list[str] = Field(default_factory=list)

    loaded_km: float = 0.0
    empty_km: float = 0.0
    empty_km_avoided: float = 0.0
    estimated_fuel_cost_inr: float = 0.0
    estimated_toll_inr: float = 0.0
    total_estimated_cost_inr: float = 0.0

    selected_vehicle_id: str | None = None
    return_load: ReturnLoadOpportunity = Field(default_factory=ReturnLoadOpportunity)

    explanation: RouteExplanation = Field(default_factory=RouteExplanation)
    optimization: OptimizationMetadata


class RouteOptimizeResponse(BaseModel):
    solution: RouteSolution
    warnings: list[str] = Field(default_factory=list)
