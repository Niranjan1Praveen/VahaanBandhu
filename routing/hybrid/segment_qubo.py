"""Set-partitioning QUBO over candidate route segments.

This is the QUAV-inspired encoding, adapted to trucks.

    x_s = 1  iff candidate segment s is selected

Three constraint families, each contributing genuine quadratic couplings:

1. **Leg selection** -- exactly one segment per leg:
   ``A_leg * (sum_{s in leg L} x_s - 1)^2``

2. **Customer coverage** -- every customer served exactly once across all
   selected segments:
   ``A_cover * (sum_{s covering v} x_s - 1)^2``

3. **Continuity** -- selected segments must chain end-to-start. In this
   construction legs are already anchored, so continuity follows from (1); the
   term is retained explicitly (weight configurable, default 0) so the
   formulation stays correct if legs are ever allowed to overlap.

**Why this and not one-hot candidate selection.** Picking one of k whole routes
is an O(k) argmin -- a pointless thing to hand a quantum optimizer, as the
research notes already recorded. Set partitioning is NP-hard: segments overlap in
which customers they cover, so leg choices are coupled through constraint (2).
That coupling is the entire justification for using QAOA here rather than a sort.

**Why not QUAV's Hamiltonian.** QUAV uses ``H_C = sum_i C(e_i) Z_i``, which is
purely linear and therefore separable -- each qubit's optimum is readable by
inspection and no entanglement is needed. Constraints (1) and (2) above are what
make this a real optimization problem. ``coupling_density()`` measures that the
couplings actually exist, and a test asserts it is non-zero.

Penalty weights are derived from the cost scale rather than guessed, so a
constraint violation can never pay for itself.
"""

from __future__ import annotations

import numpy as np

from routing.hybrid.corridor import Corridor
from routing.quantum.qubo import QUBO

ENCODING_SEGMENT_PARTITION = "segment_set_partition_v1"
QUBO_VERSION = "quav_hybrid_v1"


def build_segment_qubo(
    corridor: Corridor,
    *,
    penalty_leg: float | None = None,
    penalty_cover: float | None = None,
    penalty_continuity: float = 0.0,
) -> QUBO:
    """Build the set-partitioning QUBO for a corridor.

    Args:
        penalty_leg: Weight on "exactly one segment per leg".
        penalty_cover: Weight on "each customer covered exactly once".
            Both default to a multiple of the maximum segment cost, which
            guarantees no violation is ever cheaper than compliance.
    """
    segs = corridor.segments
    m = len(segs)
    if m == 0:
        raise ValueError("corridor has no segments to select from")

    costs = np.array([s.cost for s in segs], dtype=float)
    scale = float(costs.max()) if costs.size else 1.0
    # Any violation must outweigh the largest possible cost saving, which is
    # bounded by the total cost of every segment.
    default_penalty = float(costs.sum() + scale + 1.0)
    A_leg = default_penalty if penalty_leg is None else penalty_leg
    A_cover = default_penalty if penalty_cover is None else penalty_cover

    Q = np.zeros((m, m))
    offset = 0.0

    # --- objective: total cost of selected segments (linear, on the diagonal)
    for i in range(m):
        Q[i, i] += costs[i]

    def add_exactly_one(indices: list[int], A: float) -> float:
        """(sum_i x_i - 1)^2 = sum_i x_i^2 - 2 sum_i x_i + 2 sum_{i<j} x_i x_j + 1
        with x binary so x^2 = x, giving a -A on each diagonal and +2A coupling."""
        for i in indices:
            Q[i, i] += A * (1 - 2)
        for a in range(len(indices)):
            for b in range(a + 1, len(indices)):
                i, j = sorted((indices[a], indices[b]))
                Q[i, j] += 2 * A
        return A  # the constant +1 term

    # --- constraint 1: exactly one segment per leg
    by_leg: dict[str, list[int]] = {}
    for idx, s in enumerate(segs):
        by_leg.setdefault(s.segment_id.split("_")[0], []).append(idx)
    for indices in by_leg.values():
        offset += add_exactly_one(indices, A_leg)

    # --- constraint 2: every customer covered exactly once
    # This is the coupling that makes leg choices interdependent.
    by_customer: dict[int, list[int]] = {}
    for idx, s in enumerate(segs):
        for v in s.interior:
            by_customer.setdefault(v, []).append(idx)
    for indices in by_customer.values():
        offset += add_exactly_one(indices, A_cover)

    # --- constraint 3: continuity (inactive by default; legs are pre-anchored)
    if penalty_continuity > 0:
        for i, si in enumerate(segs):
            for j, sj in enumerate(segs):
                if i >= j:
                    continue
                # Penalise co-selecting two segments that start at the same
                # anchor -- they would fork the route.
                if si.start == sj.start:
                    Q[i, j] += penalty_continuity

    variable_map = {
        i: ("segment", segs[i].segment_id, tuple(segs[i].path)) for i in range(m)
    }

    return QUBO(
        Q=np.triu(Q),
        variable_map=variable_map,
        encoding=ENCODING_SEGMENT_PARTITION,
        penalty=float(max(A_leg, A_cover)),
        constant_offset=offset,
        metadata={
            "qubo_version": QUBO_VERSION,
            "problem": "segment_set_partition",
            "instance_id": corridor.instance_id,
            "n_segments": m,
            "n_legs": len(by_leg),
            "n_customers_covered": len(by_customer),
            "penalty_leg": A_leg,
            "penalty_cover": A_cover,
            "penalty_continuity": penalty_continuity,
            "anchors": corridor.anchors,
        },
    )


def coupling_density(qubo: QUBO) -> float:
    """Fraction of possible off-diagonal terms that are non-zero.

    A density of zero would mean the Hamiltonian is separable and QAOA has
    nothing to do -- exactly the QUAV weakness we are avoiding.
    """
    n = qubo.n_vars
    if n < 2:
        return 0.0
    off = qubo.Q[np.triu_indices(n, k=1)]
    return float(np.count_nonzero(off) / len(off))


def incumbent_bitstring(corridor: Corridor, qubo: QUBO) -> np.ndarray:
    """The binary vector corresponding to the classical incumbent.

    Used to warm-start QAOA and to assert that the incumbent is representable in
    the reduced problem at all.
    """
    x = np.zeros(qubo.n_vars)
    ids = {qubo.variable_map[i][1]: i for i in range(qubo.n_vars)}
    for sid in corridor.incumbent_segment_ids:
        if sid in ids:
            x[ids[sid]] = 1.0
    return x


def decode_segments(x: np.ndarray, corridor: Corridor, qubo: QUBO) -> dict:
    """Turn a bitstring into a tour, reporting exactly why it fails if it does.

    Returns a dict with ``feasible``, ``tour`` and ``violations``. A quantum
    sample that does not chain into a single covering tour is rejected here, not
    repaired silently -- the caller decides whether to attempt repair.
    """
    selected = [qubo.variable_map[i][1] for i in range(qubo.n_vars) if x[i] > 0.5]
    violations: list[str] = []
    if not selected:
        return {"feasible": False, "tour": None, "segments": [],
                "violations": ["no_segments_selected"]}

    segs = [corridor.segment_by_id(s) for s in selected]

    # Exactly one per leg.
    by_leg: dict[str, int] = {}
    for s in segs:
        by_leg[s.segment_id.split("_")[0]] = by_leg.get(s.segment_id.split("_")[0], 0) + 1
    expected_legs = {s.segment_id.split("_")[0] for s in corridor.segments}
    for leg in expected_legs:
        got = by_leg.get(leg, 0)
        if got != 1:
            violations.append(f"leg_{leg}_selected_{got}_times")

    # Coverage exactly once.
    covered: list[int] = []
    for s in segs:
        covered.extend(s.interior)
    all_customers = {v for s in corridor.segments for v in s.interior}
    for v in all_customers:
        c = covered.count(v)
        if c != 1:
            violations.append(f"customer_{v}_covered_{c}_times")

    if violations:
        return {"feasible": False, "tour": None,
                "segments": [s.segment_id for s in segs], "violations": violations}

    # Chain segments start -> end into a tour.
    by_start = {s.start: s for s in segs}
    depot = corridor.incumbent_tour[0]
    tour = [depot]
    current = depot
    guard = 0
    while guard <= len(segs):
        guard += 1
        s = by_start.get(current)
        if s is None:
            break
        tour.extend(s.interior)
        if s.end == depot:
            break
        tour.append(s.end)
        current = s.end
    if len(set(tour)) != len(tour):
        violations.append("tour_revisits_a_node")
    if violations:
        return {"feasible": False, "tour": None,
                "segments": [s.segment_id for s in segs], "violations": violations}

    return {"feasible": True, "tour": tour,
            "segments": [s.segment_id for s in segs], "violations": []}
