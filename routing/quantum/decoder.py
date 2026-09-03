"""Decode measured bitstrings back into routes, and judge their feasibility.

The decoder is where quantum results become honest or dishonest. A QAOA
measurement is a probability distribution over bitstrings, most of which
violate the constraints. Reporting only the best feasible sample while quietly
discarding thousands of infeasible ones, without saying so, would overstate the
method badly -- so ``decode_counts`` returns the feasible *rate* alongside the
best solution, and that rate is recorded in every benchmark row.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from routing.quantum.qubo import (
    ENCODING_EDGE_SELECTION, ENCODING_PERMUTATION, QUBO,
)


@dataclass
class DecodedRoute:
    tour: list[int] | None
    edges: list[tuple[int, int]] | None
    feasible: bool
    violations: list[str]
    energy: float
    route_cost: float | None


def bitstring_to_array(bits: str, n_vars: int) -> np.ndarray:
    """Qiskit returns little-endian bitstrings; reverse to variable order."""
    b = bits.replace(" ", "")
    if len(b) != n_vars:
        b = b.zfill(n_vars)[:n_vars]
    return np.array([int(c) for c in reversed(b)], dtype=float)


def decode_permutation(x: np.ndarray, qubo: QUBO, D: np.ndarray) -> DecodedRoute:
    n = int(round(np.sqrt(qubo.n_vars)))
    grid = x.reshape(n, n)  # [node, position]
    violations = []

    node_counts = grid.sum(axis=1)
    pos_counts = grid.sum(axis=0)
    if not np.allclose(node_counts, 1):
        violations.append("node_visited_wrong_number_of_times")
    if not np.allclose(pos_counts, 1):
        violations.append("position_filled_wrong_number_of_times")

    if violations:
        return DecodedRoute(None, None, False, violations, qubo.energy(x), None)

    tour = [int(np.argmax(grid[:, t])) for t in range(n)]
    cost = float(sum(D[tour[i], tour[(i + 1) % n]] for i in range(n)))
    return DecodedRoute(tour, list(zip(tour, tour[1:] + tour[:1])), True, [],
                        qubo.energy(x), cost)


def decode_edge_selection(x: np.ndarray, qubo: QUBO) -> DecodedRoute:
    """Reconstruct a path from selected edges, verifying it is a single
    connected source-to-sink walk rather than a disjoint set of fragments."""
    source = qubo.metadata["source"]
    sink = qubo.metadata["sink"]
    selected = [qubo.variable_map[i][1:] for i in range(qubo.n_vars) if x[i] > 0.5]
    violations: list[str] = []

    if not selected:
        return DecodedRoute(None, None, False, ["no_edges_selected"], qubo.energy(x), None)

    out_map: dict[int, list[int]] = {}
    for u, v in selected:
        out_map.setdefault(u, []).append(v)

    # Walk from source; a valid solution is one unbranched path to the sink.
    tour, current, seen = [source], source, {source}
    while current != sink:
        nxts = out_map.get(current, [])
        if len(nxts) != 1:
            violations.append(
                "dead_end_at_node" if not nxts else "branching_at_node")
            break
        current = nxts[0]
        if current in seen:
            violations.append("cycle_detected")
            break
        seen.add(current)
        tour.append(current)

    if current != sink and "cycle_detected" not in violations:
        violations.append("path_does_not_reach_sink")
    if len(selected) != len(tour) - 1:
        violations.append("selected_edges_not_all_on_path")

    feasible = not violations
    return DecodedRoute(
        tour if feasible else None,
        selected,
        feasible,
        violations,
        qubo.energy(x),
        None,
    )


def decode(
    x: np.ndarray, qubo: QUBO, D: np.ndarray | None = None,
    decode_fn=None,
) -> DecodedRoute:
    """Decode a bitstring for any registered encoding.

    ``decode_fn`` lets a caller supply a decoder for an encoding this module
    does not know about (the segment-partition and return-load QUBOs carry
    problem context that cannot live in the QUBO itself). It must return a dict
    with at least a ``feasible`` key; a ``violations`` list is used if present.
    Keeping this pluggable avoids importing every problem type into the decoder
    and creating an import cycle.
    """
    if decode_fn is not None:
        out = decode_fn(x)
        return DecodedRoute(
            tour=out.get("tour"), edges=None,
            feasible=bool(out.get("feasible", False)),
            violations=list(out.get("violations", [])),
            energy=qubo.energy(x),
            route_cost=out.get("objective"),
        )
    if qubo.encoding == ENCODING_PERMUTATION:
        if D is None:
            raise ValueError("permutation decoding needs the distance matrix")
        return decode_permutation(x, qubo, D)
    if qubo.encoding == ENCODING_EDGE_SELECTION:
        return decode_edge_selection(x, qubo)
    raise ValueError(
        f"unknown encoding {qubo.encoding!r}; pass decode_fn= for custom encodings"
    )


def decode_counts(
    counts: dict[str, int], qubo: QUBO, D: np.ndarray | None = None,
    decode_fn=None,
) -> dict:
    """Decode a full measurement histogram.

    Returns the best feasible solution *and* the feasibility rate, so a result
    can never be reported without disclosing how much of the distribution was
    junk.
    """
    total = sum(counts.values())
    best: DecodedRoute | None = None
    best_bits = None
    n_feasible_shots = 0

    for bits, shots in counts.items():
        x = bitstring_to_array(bits, qubo.n_vars)
        dec = decode(x, qubo, D, decode_fn=decode_fn)
        if dec.feasible:
            n_feasible_shots += shots
            if best is None or dec.energy < best.energy:
                best, best_bits = dec, bits

    return {
        "best": best,
        "best_bitstring": best_bits,
        "total_shots": total,
        "feasible_shots": n_feasible_shots,
        "feasible_rate": n_feasible_shots / total if total else 0.0,
        "n_distinct_bitstrings": len(counts),
        "found_feasible": best is not None,
    }
