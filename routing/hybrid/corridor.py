"""Candidate corridor construction around a classical incumbent.

This is the search-space reduction step of the QUAV-inspired pipeline, and it is
where most of the scientific care goes.

**What we borrow from QUAV.** The paper's central useful idea is: do not encode
the whole navigation problem. Reduce it classically first, then represent only a
small number of meaningful *segments* quantum mechanically, one binary variable
per segment.

**What we change.** QUAV segments a UAV trajectory into equal-distance chunks of
free space, because free space has no natural structure. A truck route does have
structure: pickups, junctions, mandi approaches, toll transitions. Equal-distance
chunking would cut the route at meaningless places. Our segments are therefore
*sub-routes between anchor nodes*, and the alternatives are genuinely different
ways of covering the same customers.

**Why segments and not "alternative paths".** Selecting one of k precomputed
whole routes is a one-hot pick -- classically an O(k) argmin, and a pointless
thing to hand a quantum optimizer. Selecting a *combination of overlapping
segments subject to covering every customer exactly once* is a set-partitioning
problem: NP-hard, genuinely quadratic in QUBO form, and precisely the structure
real branch-and-price VRP solvers exploit. That is the formulation worth testing.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field

import numpy as np

from routing.classical.heuristics import tour_cost
from routing.models import RoutingInstance


@dataclass(frozen=True)
class Segment:
    """A candidate sub-route between two anchor nodes.

    ``customers`` is the set this segment covers; the coverage constraint in the
    QUBO is what couples segments together.
    """

    segment_id: str
    start: int
    end: int
    interior: tuple[int, ...]
    cost: float
    source: str  # how this alternative was generated

    @property
    def customers(self) -> frozenset[int]:
        return frozenset(self.interior)

    @property
    def path(self) -> tuple[int, ...]:
        return (self.start, *self.interior, self.end)


@dataclass
class Corridor:
    """The reduced problem handed to the quantum layer."""

    instance_id: str
    anchors: list[int]
    segments: list[Segment]
    incumbent_tour: list[int]
    incumbent_segment_ids: list[str]
    incumbent_cost: float
    ambiguity: dict
    n_variables: int
    generation_seed: int
    notes: list[str] = field(default_factory=list)

    def segment_by_id(self, sid: str) -> Segment:
        return next(s for s in self.segments if s.segment_id == sid)

    def summary(self) -> dict:
        return {
            "instance_id": self.instance_id,
            "n_anchors": len(self.anchors),
            "n_segments": len(self.segments),
            "n_variables": self.n_variables,
            "incumbent_cost": round(self.incumbent_cost, 4),
            "n_alternatives_per_leg": self.ambiguity.get("per_leg", {}),
            "mean_leg_ambiguity": self.ambiguity.get("mean_relative_gap"),
            "seed": self.generation_seed,
        }


def _segment_cost(D: np.ndarray, path: tuple[int, ...]) -> float:
    return float(sum(D[a, b] for a, b in zip(path[:-1], path[1:])))


def choose_anchors(
    tour: list[int], depot: int, max_legs: int = 4, target_interior: int = 3,
) -> list[int]:
    """Pick anchor nodes that split the incumbent tour into legs.

    Leg count is driven by ``target_interior``, not by ``max_legs`` alone. This
    matters: splitting a 5-node tour into 4 legs leaves every leg with zero
    interior nodes, so there is nothing to reorder, the QUBO has no coupling and
    the quantum layer has no decision to make. Legs need interior nodes to
    generate alternatives, so we aim for ~``target_interior`` per leg and use
    ``max_legs`` only as a ceiling.
    """
    closed = list(tour)
    if closed[0] != depot and depot in closed:
        k = closed.index(depot)
        closed = closed[k:] + closed[:k]
    n = len(closed)
    if n <= 3:
        return [closed[0], closed[-1]]

    # n - 1 positions after the depot must be divided so each leg holds roughly
    # target_interior interior nodes (each leg consumes target_interior + 1 slots).
    n_legs = max(1, min(max_legs, (n - 1) // (target_interior + 1)))
    idx = sorted({int(round(i * (n - 1) / n_legs)) for i in range(n_legs + 1)})
    anchors = [closed[i] for i in idx]
    if anchors[-1] != closed[-1]:
        anchors.append(closed[-1])
    return anchors


def _best_ordering(D: np.ndarray, start: int, end: int,
                   nodes: tuple[int, ...]) -> tuple[tuple[int, ...], float]:
    """Cheapest ordering of ``nodes`` between two anchors.

    Enumerated exactly for small sets, greedily otherwise. The ordering is not
    the interesting decision here -- *which* nodes belong to the leg is -- so we
    settle ordering classically and let the QUBO decide membership.
    """
    if len(nodes) <= 1:
        return nodes, _segment_cost(D, (start, *nodes, end))
    if len(nodes) <= 6:
        best, best_c = None, float("inf")
        for p in itertools.permutations(nodes):
            c = _segment_cost(D, (start, *p, end))
            if c < best_c:
                best, best_c = p, c
        return best, best_c
    remaining, cur, order = list(nodes), start, []
    while remaining:
        nxt = min(remaining, key=lambda v: D[cur, v])
        order.append(nxt)
        remaining.remove(nxt)
        cur = nxt
    o = tuple(order)
    return o, _segment_cost(D, (start, *o, end))


def _leg_alternatives(
    D: np.ndarray, start: int, end: int, interior: list[int],
    *, neighbour_pool: list[int], max_alternatives: int, rng: np.random.Generator,
) -> list[tuple[tuple[int, ...], str]]:
    """Generate alternative *memberships* for one leg, not just reorderings.

    This is the correction that makes the hybrid layer scientifically meaningful.

    An earlier version generated only permutations of a leg's own interior nodes.
    That neighbourhood is entirely contained within what 2-opt already searches,
    so the QUBO optimum equalled the classical incumbent on 10 of 10 test
    instances -- the quantum layer was structurally incapable of finding
    anything, no matter how well QAOA performed.

    The fix is to let a leg **drop** a customer or **absorb** one from an
    adjacent leg. Coverage is then only satisfiable if a drop in one leg is
    matched by an absorb in another, which is exactly an Or-opt relocation move
    across distant tour positions -- outside the 2-opt neighbourhood, and
    genuinely coupled across legs. That coupling is what the set-partitioning
    QUBO is for.
    """
    incumbent = tuple(interior)
    out: list[tuple[tuple[int, ...], str]] = []
    seen: set[tuple[int, ...]] = set()

    def add(nodes: tuple[int, ...], source: str) -> None:
        order, _ = _best_ordering(D, start, end, nodes)
        if order not in seen:
            seen.add(order)
            out.append((order, source))

    add(incumbent, "incumbent")

    # Reorderings (cheap, sometimes still useful for longer interiors).
    if 2 <= len(interior) <= 4:
        for p in itertools.permutations(interior):
            if p != incumbent:
                add(p, "reorder")

    # Drop one customer -- must be absorbed by another leg to satisfy coverage.
    for v in interior:
        add(tuple(x for x in interior if x != v), "drop")

    # Absorb one customer from an adjacent leg.
    for v in neighbour_pool:
        if v not in interior:
            add((*interior, v), "absorb")

    # Rank by cost and keep the cheapest alternatives, always retaining the
    # incumbent at position 0 so the corridor provably contains it.
    inc = [o for o in out if o[1] == "incumbent"]
    rest = [o for o in out if o[1] != "incumbent"]
    rest.sort(key=lambda o: _segment_cost(D, (start, *o[0], end)))
    return inc + rest[: max(0, max_alternatives - 1)]


def build_corridor(
    inst: RoutingInstance,
    incumbent_tour: list[int],
    *,
    max_variables: int = 18,
    max_alternatives_per_leg: int = 4,
    max_legs: int = 4,
    target_interior: int = 3,
    cost_matrix: np.ndarray | None = None,
    seed: int = 0,
) -> Corridor:
    """Build the reduced segment corridor around a classical incumbent.

    Args:
        max_variables: Hard qubit budget. Segments are dropped from the least
            ambiguous legs first, because a leg whose alternatives are all much
            worse than the incumbent has nothing to decide.

    The incumbent's own segments are **always** retained. This guarantees the
    reduced problem contains the classical solution, so the quantum layer can at
    worst reproduce it -- tested in ``test_corridor_contains_incumbent``.
    """
    rng = np.random.default_rng(seed)
    # Segment costs default to the project's true objective, not raw distance.
    # Using distance here would build a corridor optimizing a different quantity
    # from the one the benchmark scores -- see routing.hybrid.objective_costs.
    if cost_matrix is None:
        from routing.hybrid.objective_costs import objective_cost_matrix
        cost_matrix = objective_cost_matrix(inst)
    D = cost_matrix
    depot = inst.depot_index

    anchors = choose_anchors(incumbent_tour, depot, max_legs=max_legs,
                             target_interior=target_interior)
    closed = list(incumbent_tour)
    if closed[0] != depot and depot in closed:
        k = closed.index(depot)
        closed = closed[k:] + closed[:k]

    # Split the incumbent into legs between consecutive anchors.
    legs: list[tuple[int, int, list[int]]] = []
    positions = [closed.index(a) for a in anchors]
    for (p0, a0), (p1, a1) in zip(zip(positions, anchors), zip(positions[1:], anchors[1:])):
        legs.append((a0, a1, closed[p0 + 1:p1]))
    # Closing leg back to the depot.
    legs.append((anchors[-1], depot, []))

    # Generate alternatives per leg and measure how ambiguous each leg is.
    per_leg: dict[str, int] = {}
    leg_gaps: list[float] = []
    candidates: list[list[Segment]] = []

    for li, (a0, a1, interior) in enumerate(legs):
        # Customers a leg may absorb: the interiors of its immediate neighbours.
        # Restricting to adjacent legs keeps relocations geographically sensible
        # and keeps the variable count bounded.
        pool: list[int] = []
        if li > 0:
            pool.extend(legs[li - 1][2])
        if li + 1 < len(legs):
            pool.extend(legs[li + 1][2])

        alts = _leg_alternatives(D, a0, a1, interior, neighbour_pool=pool,
                                 max_alternatives=max_alternatives_per_leg, rng=rng)
        segs: list[Segment] = []
        for ai, (order, source) in enumerate(alts):
            path = (a0, *order, a1)
            segs.append(Segment(
                segment_id=f"L{li}_A{ai}",
                start=a0, end=a1, interior=tuple(order),
                cost=_segment_cost(D, path), source=source,
            ))
        segs.sort(key=lambda s: s.cost)
        candidates.append(segs)
        per_leg[f"L{li}"] = len(segs)

        # Relative gap between the best and second-best alternative. A small gap
        # means the leg is genuinely ambiguous and worth optimizing; a large gap
        # means the choice is already obvious.
        if len(segs) > 1 and segs[0].cost > 0:
            leg_gaps.append((segs[1].cost - segs[0].cost) / segs[0].cost)
        else:
            leg_gaps.append(float("inf"))

    # Enforce the variable budget: trim alternatives from the least ambiguous
    # legs first. Position 0 of each leg is never trimmed, so every leg keeps at
    # least one option and the incumbent survives.
    total = sum(len(s) for s in candidates)
    notes: list[str] = []
    if total > max_variables:
        order = np.argsort([-g if np.isfinite(g) else -1e9 for g in leg_gaps])
        while total > max_variables:
            trimmed = False
            for li in order:
                if len(candidates[li]) > 1:
                    candidates[li].pop()
                    total -= 1
                    trimmed = True
                    if total <= max_variables:
                        break
            if not trimmed:
                break
        notes.append(f"trimmed to {total} variables from {sum(per_leg.values())}")

    segments = [s for group in candidates for s in group]

    # Identify which segments reconstruct the incumbent.
    incumbent_ids: list[str] = []
    for li, (a0, a1, interior) in enumerate(legs):
        want = tuple(interior)
        match = next((s for s in candidates[li]
                      if s.start == a0 and s.end == a1 and s.interior == want), None)
        if match is None:
            # Reinstate it: the corridor must always contain the incumbent.
            path = (a0, *want, a1)
            match = Segment(f"L{li}_INC", a0, a1, want,
                            _segment_cost(D, path), "incumbent_reinstated")
            segments.append(match)
            notes.append(f"reinstated incumbent segment for leg {li}")
        incumbent_ids.append(match.segment_id)

    finite_gaps = [g for g in leg_gaps if np.isfinite(g)]
    ambiguity = {
        "per_leg": per_leg,
        "leg_relative_gaps": [None if not np.isfinite(g) else round(g, 5) for g in leg_gaps],
        "mean_relative_gap": round(float(np.mean(finite_gaps)), 5) if finite_gaps else None,
        "min_relative_gap": round(float(np.min(finite_gaps)), 5) if finite_gaps else None,
    }

    return Corridor(
        instance_id=inst.instance_id,
        anchors=anchors,
        segments=segments,
        incumbent_tour=closed,
        incumbent_segment_ids=incumbent_ids,
        incumbent_cost=tour_cost(closed, D),
        ambiguity=ambiguity,
        n_variables=len(segments),
        generation_seed=seed,
        notes=notes,
    )


def should_refine(corridor: Corridor, *, gap_threshold: float = 0.05) -> tuple[bool, str]:
    """Decide whether this corridor is worth spending quantum effort on.

    Step 12 of the brief: do not quantum-process every route. If the incumbent's
    alternatives are all clearly worse, the classical answer is already
    confident and refinement can only waste compute.
    """
    gap = corridor.ambiguity.get("min_relative_gap")
    if corridor.n_variables < 3:
        return False, "corridor too small to contain a real decision"
    if gap is None:
        return False, "no leg has an alternative"
    if gap > gap_threshold:
        return False, (f"classical choice is confident (closest alternative is "
                       f"{gap:.1%} worse, threshold {gap_threshold:.0%})")
    return True, f"legs are nearly tied (closest alternative {gap:.1%} worse)"
