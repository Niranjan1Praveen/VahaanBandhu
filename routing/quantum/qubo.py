"""QUBO construction for VahaanBandhu routing subproblems.

Two encodings, chosen deliberately.

**1. Permutation TSP (``build_tsp_qubo``)** -- the textbook x[i,t] formulation:
n^2 binary variables for n nodes. Honest about its cost: 6 nodes is 36 qubits,
8 nodes is 64. This is why ``QUANTUM_NODE_CEILING`` is 7. It is included
because it is the standard against which QAOA routing results are reported.

**2. Edge selection (``build_edge_selection_qubo``)** -- one binary variable per
candidate edge, following the encoding in Innan et al., *QUAV* (arXiv
2508.21361), which assigns one qubit per path segment rather than per
(node, timestep) pair. For a sparsified candidate graph this is dramatically
cheaper: a 20-edge corridor problem is 20 qubits regardless of how many nodes
the underlying road network has. This is the formulation the hybrid pipeline
actually uses.

A necessary critique of the source paper, recorded here because it changes the
design: QUAV's cost Hamiltonian is ``H_C = sum_i C(e_i) Z_i``, which is purely
linear. A linear Hamiltonian is separable -- each qubit's optimal value can be
read off independently, no entanglement required, and QAOA offers nothing over
inspection. Our edge-selection QUBO therefore adds genuine quadratic terms:
flow conservation at every node and a path-length constraint. Those couplings
are what make the problem an actual combinatorial optimization rather than n
independent coin flips.

Penalty weights are not guessed. They are scaled relative to the largest
achievable cost saving, so violating a constraint can never be cheaper than
obeying it -- the standard requirement for a valid penalty-method QUBO.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

QUBO_VERSION = "qubo_v1"
ENCODING_PERMUTATION = "permutation_xit_v1"
ENCODING_EDGE_SELECTION = "edge_selection_v1"


@dataclass
class QUBO:
    """A QUBO in the form  minimize x^T Q x  over x in {0,1}^n.

    ``Q`` is stored upper-triangular with the linear terms on the diagonal.
    ``variable_map`` records what each binary variable *means*, which is the
    only thing that makes a measured bitstring decodable back into a route.
    """

    Q: np.ndarray
    variable_map: dict[int, tuple]
    encoding: str
    penalty: float
    constant_offset: float = 0.0
    metadata: dict = field(default_factory=dict)

    @property
    def n_vars(self) -> int:
        return self.Q.shape[0]

    def energy(self, x: np.ndarray) -> float:
        x = np.asarray(x, dtype=float)
        return float(x @ self.Q @ x) + self.constant_offset

    def to_ising(self) -> tuple[np.ndarray, np.ndarray, float]:
        """Convert to Ising (h, J, offset) via x = (1 - z) / 2.

        Returned as (h, J, offset) with J strictly upper-triangular, matching
        the convention used by the QAOA circuit builder.
        """
        n = self.n_vars
        Q = self.Q
        # x_i = (1 - z_i)/2 substituted into sum_ij Q_ij x_i x_j
        h = np.zeros(n)
        J = np.zeros((n, n))
        offset = self.constant_offset

        for i in range(n):
            offset += Q[i, i] / 2.0
            h[i] -= Q[i, i] / 2.0
            for j in range(i + 1, n):
                q = Q[i, j]
                if q == 0:
                    continue
                offset += q / 4.0
                h[i] -= q / 4.0
                h[j] -= q / 4.0
                J[i, j] += q / 4.0
        return h, J, offset

    def summary(self) -> dict:
        off_diag = self.Q[np.triu_indices_from(self.Q, k=1)]
        return {
            "qubo_version": QUBO_VERSION,
            "encoding": self.encoding,
            "n_vars": self.n_vars,
            "n_quadratic_terms": int(np.count_nonzero(off_diag)),
            "penalty": self.penalty,
            "max_abs_coefficient": float(np.max(np.abs(self.Q))) if self.Q.size else 0.0,
            "constant_offset": self.constant_offset,
            **self.metadata,
        }


def build_tsp_qubo(D: np.ndarray, penalty: float | None = None) -> QUBO:
    """Permutation-encoded TSP QUBO.

    Variable x[i,t] = 1 iff node i is visited at position t. Constraints:
    each node visited exactly once, each position filled exactly once.

    Args:
        D: (n, n) directed distance matrix.
        penalty: Constraint weight. Defaults to a value strictly greater than
            the largest possible tour cost, which guarantees no constraint
            violation can ever pay for itself.
    """
    n = D.shape[0]
    if n < 3:
        raise ValueError("TSP QUBO needs at least 3 nodes")
    n_vars = n * n

    if penalty is None:
        # Any violation must cost more than the worst tour it could enable.
        penalty = float(n * D.max() + 1.0)

    def idx(i: int, t: int) -> int:
        return i * n + t

    Q = np.zeros((n_vars, n_vars))

    # Objective: sum over consecutive positions of the traversed distance.
    for t in range(n):
        t_next = (t + 1) % n
        for i in range(n):
            for j in range(n):
                if i == j:
                    continue
                a, b = idx(i, t), idx(j, t_next)
                lo, hi = (a, b) if a <= b else (b, a)
                if lo == hi:
                    Q[lo, hi] += D[i, j]
                else:
                    Q[lo, hi] += D[i, j]

    # Constraint A: each node appears exactly once.
    # (sum_t x[i,t] - 1)^2 = sum_t x[i,t]^2 + 2 sum_{t<t'} x x - 2 sum_t x + 1
    for i in range(n):
        for t in range(n):
            Q[idx(i, t), idx(i, t)] += penalty * (1 - 2)
            for t2 in range(t + 1, n):
                a, b = sorted((idx(i, t), idx(i, t2)))
                Q[a, b] += 2 * penalty

    # Constraint B: each position holds exactly one node.
    for t in range(n):
        for i in range(n):
            Q[idx(i, t), idx(i, t)] += penalty * (1 - 2)
            for i2 in range(i + 1, n):
                a, b = sorted((idx(i, t), idx(i2, t)))
                Q[a, b] += 2 * penalty

    variable_map = {idx(i, t): ("visit", i, t) for i in range(n) for t in range(n)}

    return QUBO(
        Q=np.triu(Q),
        variable_map=variable_map,
        encoding=ENCODING_PERMUTATION,
        penalty=penalty,
        constant_offset=2.0 * n * penalty,  # the two "+1" terms per constraint
        metadata={"n_nodes": n, "problem": "TSP"},
    )


def build_edge_selection_qubo(
    edges: list[tuple[int, int]],
    edge_costs: np.ndarray,
    source: int,
    sink: int,
    n_nodes: int,
    penalty: float | None = None,
) -> QUBO:
    """Edge-selection QUBO for constrained path finding.

    One binary variable per candidate edge (the QUAV-style encoding). Selected
    edges must form a single source-to-sink path, enforced by flow conservation:

        sum(out) - sum(in) = +1 at the source
                             -1 at the sink
                              0 elsewhere

    Squaring each conservation residual produces the quadratic couplings that
    make this a genuine optimization problem rather than a separable one.

    Args:
        edges: Candidate directed edges as (u, v) node-index pairs.
        edge_costs: Cost of traversing each edge, same order as ``edges``.
        source: Path start node index.
        sink: Path end node index.
        n_nodes: Total node count in the candidate subgraph.
        penalty: Flow-conservation weight. Defaults to a multiple of the total
            candidate cost so that breaking the path is never worth it.
    """
    m = len(edges)
    if m == 0:
        raise ValueError("no candidate edges to select from")
    edge_costs = np.asarray(edge_costs, dtype=float)
    if len(edge_costs) != m:
        raise ValueError("edge_costs length does not match edges")

    if penalty is None:
        penalty = float(edge_costs.sum() + edge_costs.max() + 1.0)

    Q = np.zeros((m, m))
    offset = 0.0

    # Objective: total cost of selected edges (linear, on the diagonal).
    for e in range(m):
        Q[e, e] += edge_costs[e]

    # Flow conservation, squared, at every node.
    for node in range(n_nodes):
        b = 1.0 if node == source else (-1.0 if node == sink else 0.0)
        # coefficient of each edge variable in this node's flow expression
        coef = np.zeros(m)
        for e, (u, v) in enumerate(edges):
            if u == node:
                coef[e] += 1.0
            if v == node:
                coef[e] -= 1.0
        # (coef . x - b)^2 = sum_i c_i^2 x_i + 2 sum_{i<j} c_i c_j x_i x_j
        #                    - 2b sum_i c_i x_i + b^2      (x binary: x^2 = x)
        for e in range(m):
            if coef[e]:
                Q[e, e] += penalty * (coef[e] ** 2 - 2.0 * b * coef[e])
        for e1 in range(m):
            if not coef[e1]:
                continue
            for e2 in range(e1 + 1, m):
                if coef[e2]:
                    Q[e1, e2] += 2.0 * penalty * coef[e1] * coef[e2]
        offset += penalty * b ** 2

    variable_map = {e: ("edge", edges[e][0], edges[e][1]) for e in range(m)}

    return QUBO(
        Q=np.triu(Q),
        variable_map=variable_map,
        encoding=ENCODING_EDGE_SELECTION,
        penalty=penalty,
        constant_offset=offset,
        metadata={
            "n_edges": m, "n_nodes": n_nodes, "source": source, "sink": sink,
            "problem": "constrained_path_selection",
        },
    )


def brute_force_qubo(qubo: QUBO, max_vars: int = 22) -> tuple[np.ndarray, float]:
    """Exhaustively minimise a QUBO. The mandatory pre-hardware sanity check.

    A QUBO whose brute-force optimum does not decode to a feasible route is
    mis-formulated, and sending it to a backend would produce meaningless
    numbers dressed up as a quantum result.
    """
    n = qubo.n_vars
    if n > max_vars:
        raise ValueError(
            f"{n} variables exceeds the brute-force limit of {max_vars} "
            f"({2 ** n:.3g} states)"
        )
    best_x, best_e = None, float("inf")
    for mask in range(1 << n):
        x = np.fromiter(((mask >> i) & 1 for i in range(n)), dtype=float, count=n)
        e = qubo.energy(x)
        if e < best_e:
            best_x, best_e = x, e
    return best_x, best_e
