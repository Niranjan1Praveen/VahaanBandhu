"""The multi-objective route score.

The shortest route is very often not the best one for this business. A route
that is 12 km longer but avoids a congested corridor, has a lower toll, and
ends near a shop with a waiting return load can beat it decisively once empty
running is priced in.

Weights live in configuration and are carried on every instance and every
result, never hard-coded into a solver. Changing a weight must change the
recorded ``objective_weights`` too, or two results stop being comparable.
"""

from __future__ import annotations

from dataclasses import dataclass

from routing.models import RouteCandidate

# Mirrors vb.generate.instances.DEFAULT_OBJECTIVE_WEIGHTS. Kept in sync by
# tests/test_routing.py::test_objective_weights_match_dataset.
DEFAULT_WEIGHTS: dict[str, float] = {
    "distance_km": 1.0,
    "time_min": 0.35,
    "fuel_inr": 0.010,
    "toll_inr": 0.010,
    "risk": 12.0,
    "empty_km": 0.85,
    "circular_bonus": -1.10,
}


@dataclass(frozen=True)
class ScoreBreakdown:
    """Per-term contributions, so a route choice can be explained rather than
    asserted."""

    total: float
    terms: dict[str, float]

    def top_reasons(self, k: int = 3) -> list[str]:
        """The terms that dominated this score, largest absolute first."""
        ranked = sorted(self.terms.items(), key=lambda kv: -abs(kv[1]))
        out = []
        for name, val in ranked[:k]:
            direction = "favoured" if val < 0 else "penalised"
            out.append(f"{name} {direction} ({val:+.1f})")
        return out


def score_candidate(
    c: RouteCandidate, weights: dict[str, float] | None = None
) -> ScoreBreakdown:
    """Lower is better. Returns the total and the per-term breakdown."""
    w = {**DEFAULT_WEIGHTS, **(weights or {})}
    terms = {
        "distance_km": w["distance_km"] * c.distance_km,
        "time_min": w["time_min"] * (c.travel_time_min + c.traffic_delay_min),
        "fuel_inr": w["fuel_inr"] * c.estimated_fuel_cost_inr,
        "toll_inr": w["toll_inr"] * c.toll_cost_inr,
        "risk": w["risk"] * c.road_risk_score,
        "empty_km": w["empty_km"] * c.empty_km,
        "circular_bonus": w["circular_bonus"] * c.circular_logistics_score,
    }
    # A route a truck physically cannot take is not a cheap route; it is not a
    # route. Penalise rather than filter, so the reason survives into the log.
    if c.truck_accessibility_score < 0.5:
        terms["accessibility_penalty"] = 500.0 * (0.5 - c.truck_accessibility_score)
    return ScoreBreakdown(total=sum(terms.values()), terms=terms)


def select_best(
    candidates: list[RouteCandidate], weights: dict[str, float] | None = None
) -> tuple[RouteCandidate, ScoreBreakdown, list[tuple[RouteCandidate, ScoreBreakdown]]]:
    """Score every candidate and return the winner plus the full ranking."""
    if not candidates:
        raise ValueError("no candidate routes to select from")
    scored = [(c, score_candidate(c, weights)) for c in candidates]
    scored.sort(key=lambda cs: cs[1].total)
    best, breakdown = scored[0]
    return best, breakdown, scored


def explain_selection(
    best: RouteCandidate, breakdown: ScoreBreakdown,
    ranking: list[tuple[RouteCandidate, ScoreBreakdown]],
) -> dict:
    """Human-readable justification for the chosen route.

    Deliberately reports the margin over the runner-up. A 0.3% margin is not a
    meaningful preference and the UI should not present it as one.
    """
    runner_up = ranking[1] if len(ranking) > 1 else None
    margin = (runner_up[1].total - breakdown.total) if runner_up else None
    return {
        "selected_route_id": best.route_id,
        "distance_km": round(best.distance_km, 2),
        "eta_min": round(best.travel_time_min + best.traffic_delay_min, 1),
        "traffic_delay_min": round(best.traffic_delay_min, 1),
        "estimated_fuel_cost_inr": round(best.estimated_fuel_cost_inr, 2),
        "estimated_toll_inr": round(best.toll_cost_inr, 2),
        "total_estimated_cost_inr": round(
            best.estimated_fuel_cost_inr + best.toll_cost_inr, 2),
        "empty_km": round(best.empty_km, 2),
        "loaded_km": round(best.loaded_km, 2),
        "circular_logistics_score": round(best.circular_logistics_score, 3),
        "selection_score": round(breakdown.total, 3),
        "margin_over_runner_up": round(margin, 3) if margin is not None else None,
        "margin_is_decisive": bool(margin is not None and margin > 0.02 * breakdown.total),
        "primary_selection_reasons": breakdown.top_reasons(),
        "n_candidates_considered": len(ranking),
    }
