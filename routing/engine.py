"""The live route-selection engine.

This is what the application calls. It must be fast, must degrade gracefully,
and must never block on a quantum backend.

    request
      -> resolve entities
      -> fetch candidate routes (TomTom, else offline graph)
      -> normalize to RouteCandidate
      -> attach circular-logistics potential
      -> reduce candidates
      -> load any relevant precomputed artifacts
      -> score with the multi-objective function
      -> constraint check
      -> best route + explanation

The precomputed-artifact step is where offline quantum work is allowed to
influence production, and only in a bounded way: a stored prior can reweight
candidates, but a missing or stale artifact simply means the classical score
stands. Nothing here waits on a QPU.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass

from routing.cache.result_store import ArtifactStore
from routing.circular import evaluate_circular_trip
from routing.hybrid.candidate_reduction import reduce_candidates
from routing.models import LatLon, RouteCandidate
from routing.objective import DEFAULT_WEIGHTS, explain_selection, select_best

log = logging.getLogger(__name__)


@dataclass
class RouteDecision:
    selected: RouteCandidate
    explanation: dict
    all_candidates: list[dict]
    reduction_stats: dict
    provider_used: str
    quantum_artifact_applied: str | None
    runtime_ms: float
    degraded: bool
    warnings: list[str]


class RouteEngine:
    def __init__(
        self, primary_provider=None, fallback_provider=None,
        artifact_store: ArtifactStore | None = None,
        weights: dict[str, float] | None = None,
    ) -> None:
        self.primary = primary_provider
        self.fallback = fallback_provider
        self.artifacts = artifact_store or ArtifactStore()
        self.weights = {**DEFAULT_WEIGHTS, **(weights or {})}

    def _fetch(
        self, origin: LatLon, destination: LatLon, origin_id: str,
        destination_id: str, max_alternatives: int,
    ) -> tuple[list[RouteCandidate], str, list[str]]:
        warnings: list[str] = []
        for provider, label in ((self.primary, "primary"), (self.fallback, "fallback")):
            if provider is None:
                continue
            if not getattr(provider, "available", True):
                warnings.append(f"{provider.name} unavailable, falling through")
                continue
            try:
                routes = provider.get_alternative_routes(
                    origin, destination, max_alternatives,
                    origin_id=origin_id, destination_id=destination_id,
                )
                if routes:
                    return routes, provider.name, warnings
                warnings.append(f"{provider.name} returned no routes")
            except Exception as e:
                warnings.append(f"{provider.name} failed: {type(e).__name__}: {e}")
        return [], "none", warnings

    def _apply_quantum_prior(
        self, candidates: list[RouteCandidate], corridor_key: str
    ) -> str | None:
        """Apply a stored offline optimization prior, if one is valid.

        Priors adjust the circular-logistics term only, and only within a
        bounded range, so a stale artifact can shade a decision but never
        override the live cost data.
        """
        prior = self.artifacts.load("learned_parameters", f"prior_{corridor_key}")
        if not prior:
            return None
        adjustments = prior.get("route_priors", {})
        applied = False
        for c in candidates:
            if c.route_id in adjustments:
                delta = float(adjustments[c.route_id])
                c.circular_logistics_score += max(min(delta, 0.25), -0.25)
                applied = True
        return prior.get("artifact_name") if applied else None

    def select_route(
        self,
        origin: LatLon, destination: LatLon, *,
        origin_id: str = "O", destination_id: str = "D",
        max_alternatives: int = 4,
        load_kg: float = 0.0,
        vehicle_capacity_kg: float = 0.0,
        return_load_candidates: list[dict] | None = None,
        corridor_key: str | None = None,
    ) -> RouteDecision:
        t0 = time.perf_counter()
        candidates, provider_used, warnings = self._fetch(
            origin, destination, origin_id, destination_id, max_alternatives
        )
        if not candidates:
            raise RuntimeError(
                "no route candidates from any provider: " + "; ".join(warnings)
            )

        # Loaded/empty split and capacity utilisation, which the objective
        # needs in order to prefer a route that enables a return load.
        for c in candidates:
            c.loaded_km = c.distance_km
            c.empty_km = 0.0
            if vehicle_capacity_kg > 0:
                c.capacity_utilization = min(load_kg / vehicle_capacity_kg, 1.0)

        if return_load_candidates:
            best_return = max(
                return_load_candidates, key=lambda r: r.get("return_load_score", 0.0)
            )
            for c in candidates:
                c.circular_logistics_score = float(best_return.get("return_load_score", 0.0))

        reduced, stats = reduce_candidates(candidates, max_candidates=8)

        artifact = None
        if corridor_key:
            artifact = self._apply_quantum_prior(reduced, corridor_key)

        best, breakdown, ranking = select_best(reduced, self.weights)

        if best.truck_accessibility_score < 0.5:
            warnings.append(
                "best-scoring route has poor truck accessibility; verify before dispatch"
            )

        explanation = explain_selection(best, breakdown, ranking)
        if not explanation["margin_is_decisive"]:
            warnings.append(
                "the top two routes score within 2% of each other -- treat the "
                "selection as a near-tie rather than a clear winner"
            )

        return RouteDecision(
            selected=best,
            explanation=explanation,
            all_candidates=[
                {**c.to_dict(), "score": round(s.total, 3), "terms": s.terms}
                for c, s in ranking
            ],
            reduction_stats=stats,
            provider_used=provider_used,
            quantum_artifact_applied=artifact,
            runtime_ms=(time.perf_counter() - t0) * 1000,
            degraded=provider_used != getattr(self.primary, "name", None),
            warnings=warnings,
        )
