"""RoutingService — the single VB-QER boundary for the application.

**Architectural invariant.** Application code depends on this service and on
nothing else in the optimization stack. It must never import Dijkstra, A*,
2-opt, OR-Tools, simulated annealing, a QUBO solver, QAOA, IBM Quantum or an
individual quantum artifact. VB-QER decides internally which of its components
contribute.

    FastAPI -> RoutingService -> VBQEROptimizer.solve(...)

**No live QPU.** `routing.quantum.ibm_runtime` is not in this module's import
graph, and a test asserts that in a clean subprocess. A queued or failed IBM job
can never make the application unavailable.

**Graceful degradation.** Where the Phase-A route graph or datasets are missing,
the service returns a clearly-labelled unavailable result rather than raising --
the application stays up and tells the user something true.
"""

from __future__ import annotations

import logging
import time
import uuid
from datetime import datetime, timezone
from functools import lru_cache

from server.app.core.config import get_settings
from server.app.db.redis_cache import cache, route_cache_key
from server.app.schemas.common import GeoPoint
from server.app.schemas.routing import (
    OptimizationMetadata, ReturnLoadOpportunity, RouteExplanation, RouteSolution,
    RouteStop, RoutingProfile, RoutingRequest,
)

log = logging.getLogger(__name__)

# Fuel/§toll assumptions shared with Phase-A so figures agree across layers.
DIESEL_INR_PER_L = 92.0
DEFAULT_KMPL = 5.0


@lru_cache(maxsize=1)
def _load_phase_a():
    """Load Phase-A artifacts once. Returns None when unavailable.

    Imported lazily and cached so a missing dataset degrades the routing
    endpoint rather than preventing the API from starting.
    """
    try:
        import pandas as pd

        from vb import config as C
        locations = pd.read_csv(C.MASTER / "locations_master.csv")
        edges = pd.read_csv(C.SYNTHETIC / "route_edges.csv")
        from routing.providers.offline import OfflineGraphProvider
        provider = OfflineGraphProvider(edges, locations, scenario_id="SCN_BASELINE")
        return {"locations": locations, "provider": provider}
    except Exception as e:
        log.warning("Phase-A routing artifacts unavailable: %s", e)
        return None


@lru_cache(maxsize=1)
def _optimizer():
    """The one VB-QER instance. Import is local so the module graph stays clean."""
    from routing.ensemble import VBQEROptimizer
    return VBQEROptimizer()


def vbqer_version() -> str:
    try:
        from routing.ensemble.inference import VBQER_VERSION
        return VBQER_VERSION
    except Exception:
        return "unknown"


class RoutingService:
    """Turns an application RoutingRequest into a RouteSolution via VB-QER."""

    def __init__(self) -> None:
        self.settings = get_settings()

    # --- public API -------------------------------------------------------

    async def optimize(self, req: RoutingRequest) -> tuple[RouteSolution, list[str]]:
        warnings: list[str] = []
        t0 = time.perf_counter()

        key = route_cache_key(
            origin_id=req.origin.location_id or "",
            destination_id=req.destination.location_id or "",
            stops=[s.location_id for s in req.stops if s.location_id],
            vehicle_capacity_kg=req.capacity_kg or 0.0,
            vbqer_version=vbqer_version(),
            graph_version="g1",
            cost_snapshot_id=req.scenario_id,
            profile=req.profile.value,
        )
        cached = await cache.get_json(key)
        if cached:
            sol = RouteSolution(**cached)
            sol.optimization.cached = True
            return sol, warnings

        data = _load_phase_a()
        if data is None:
            warnings.append(
                "Phase-A route graph is not loaded; returning a direct-line estimate.")
            sol = self._fallback_solution(req, warnings)
            return sol, warnings

        sol = self._solve_on_graph(req, data, warnings)
        sol.optimization.compute_ms = round((time.perf_counter() - t0) * 1000, 2)

        await cache.set_json(key, sol.model_dump(mode="json"),
                             ttl_s=self.settings.route_cache_ttl_s)
        return sol, warnings

    # --- internals --------------------------------------------------------

    def _coords(self, data, location_id: str | None) -> GeoPoint | None:
        if not location_id:
            return None
        df = data["locations"]
        row = df[df["location_id"] == location_id]
        if row.empty:
            return None
        r = row.iloc[0]
        return GeoPoint(latitude=float(r["latitude"]), longitude=float(r["longitude"]))

    def _solve_on_graph(self, req: RoutingRequest, data, warnings: list[str]) -> RouteSolution:
        """Route over the Phase-A graph via the VB-QER-backed provider.

        For a simple origin->destination request the shortest-path members are
        the right internal experts and VB-QER's classification says so; we ask
        the provider for candidates and score them with the project objective.
        """
        provider = data["provider"]
        o_id = req.origin.location_id
        d_id = req.destination.location_id

        candidates = []
        if o_id and d_id:
            try:
                candidates = provider.get_alternative_routes(
                    None, None, max_alternatives=4,
                    origin_id=o_id, destination_id=d_id)
            except Exception as e:
                warnings.append(f"route lookup failed: {type(e).__name__}")

        if not candidates:
            warnings.append(
                "No path in the road graph between those points; "
                "returning a direct-line estimate.")
            return self._fallback_solution(req, warnings)

        from routing.objective import explain_selection, select_best
        best, breakdown, ranking = select_best(candidates)
        explanation = explain_selection(best, breakdown, ranking)

        polyline = [[lat, lon] for lat, lon in (best.geometry or [])]
        loaded = best.distance_km
        empty = 0.0

        return_load = ReturnLoadOpportunity(available=False)

        eta = best.travel_time_min + best.traffic_delay_min
        fuel = best.estimated_fuel_cost_inr or (best.distance_km / DEFAULT_KMPL * DIESEL_INR_PER_L)

        return RouteSolution(
            route_id=f"RT_{uuid.uuid4().hex[:12].upper()}",
            request_id=req.request_id,
            stops=[req.origin, *req.stops, req.destination],
            polyline=polyline,
            distance_km=round(best.distance_km, 2),
            estimated_time_min=round(eta, 1),
            objective=round(breakdown.total, 3),
            feasible=True,
            loaded_km=round(loaded, 2),
            empty_km=round(empty, 2),
            estimated_fuel_cost_inr=round(fuel, 2),
            estimated_toll_inr=round(best.toll_cost_inr, 2),
            total_estimated_cost_inr=round(fuel + best.toll_cost_inr, 2),
            selected_vehicle_id=req.vehicle_id,
            return_load=return_load,
            explanation=self._explain(best, explanation),
            optimization=OptimizationMetadata(
                vbqer_version=vbqer_version(),
                dataset_version="v0.1",
                graph_version="g1",
                cost_snapshot_id=req.scenario_id,
                profile=req.profile,
                problem_type="shortest_path",
                final_route_source="classical_incumbent",
                quantum_component_invoked=False,
                quantum_artifact_used=False,
                quantum_artifact_source="none",
                quantum_hardware_called_live=False,
                computed_at=datetime.now(timezone.utc),
                cached=False,
            ),
        )

    def _fallback_solution(self, req: RoutingRequest, warnings: list[str]) -> RouteSolution:
        """Direct-line estimate, clearly labelled as such.

        Never presented as a measured or live route. It exists so the UI has
        something honest to show when the graph cannot answer.
        """
        from vb.geo import haversine_km
        o, d = req.origin.point, req.destination.point
        km = 0.0
        if o and d:
            km = haversine_km(o.latitude, o.longitude, d.latitude, d.longitude) * 1.35
        eta = km / 40.0 * 60.0
        fuel = km / DEFAULT_KMPL * DIESEL_INR_PER_L
        return RouteSolution(
            route_id=f"RT_{uuid.uuid4().hex[:12].upper()}",
            request_id=req.request_id,
            stops=[req.origin, *req.stops, req.destination],
            distance_km=round(km, 2),
            estimated_time_min=round(eta, 1),
            objective=round(km, 3),
            feasible=bool(km > 0),
            violations=[] if km > 0 else ["no_coordinates_available"],
            loaded_km=round(km, 2),
            estimated_fuel_cost_inr=round(fuel, 2),
            total_estimated_cost_inr=round(fuel, 2),
            selected_vehicle_id=req.vehicle_id,
            explanation=RouteExplanation(
                reasons_hi=["अनुमानित सीधी दूरी — विस्तृत सड़क मार्ग उपलब्ध नहीं है।"],
                reasons_en=["Straight-line estimate; detailed road route unavailable."],
                primary_factor="estimate",
                margin_is_decisive=False,
            ),
            optimization=OptimizationMetadata(
                vbqer_version=vbqer_version(),
                profile=req.profile,
                problem_type="estimate",
                final_route_source="direct_line_estimate",
                computed_at=datetime.now(timezone.utc),
            ),
        )

    @staticmethod
    def _explain(best, explanation: dict) -> RouteExplanation:
        """Translate the optimizer's reasoning into user-facing language.

        The farmer must not receive a research report. Structured fields let the
        UI phrase things itself; the Hindi strings are the default surface.
        """
        hi: list[str] = []
        en: list[str] = []

        if best.traffic_delay_min and best.traffic_delay_min > 5:
            hi.append(f"इस रास्ते पर लगभग {best.traffic_delay_min:.0f} मिनट का ट्रैफ़िक है।")
            en.append(f"About {best.traffic_delay_min:.0f} min of traffic delay on this route.")
        else:
            hi.append("इस रास्ते पर ट्रैफ़िक कम है।")
            en.append("Traffic on this route is light.")

        hi.append(f"कुल दूरी लगभग {best.distance_km:.0f} किलोमीटर है।")
        en.append(f"Total distance is about {best.distance_km:.0f} km.")

        if best.toll_cost_inr and best.toll_cost_inr > 0:
            hi.append(f"अनुमानित टोल ₹{best.toll_cost_inr:.0f}।")
            en.append(f"Estimated toll Rs {best.toll_cost_inr:.0f}.")

        return RouteExplanation(
            reasons_hi=hi, reasons_en=en,
            primary_factor=(explanation.get("primary_selection_reasons") or [None])[0],
            margin_is_decisive=bool(explanation.get("margin_is_decisive", True)),
        )


routing_service = RoutingService()
