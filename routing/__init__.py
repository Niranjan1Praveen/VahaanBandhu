"""VahaanBandhu hybrid route optimization engine.

Layering, deliberately:

    providers/   fetch road-network reality (TomTom, or an offline graph)
    classical/   robust solvers that run in the live request path
    quantum/     offline research: QUBO encoding, QAOA, IBM hardware
    hybrid/      candidate reduction + the fast scoring layer that ships
    evaluation/  benchmarking across all of the above on identical instances

The live application depends only on providers + classical + hybrid. Nothing in
the request path imports ``routing.quantum``.
"""
