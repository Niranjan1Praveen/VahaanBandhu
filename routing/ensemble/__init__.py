"""VB-QER -- VahaanBandhu Quantum-Enhanced Routing ensemble.

The final routing algorithm. One canonical entry point:

    from routing.ensemble import VBQEROptimizer
    solution = VBQEROptimizer().solve(instance)

Four terms are used precisely throughout this package and must not be
interchanged:

* **Classical Routing** -- traditional optimization alone.
* **Quantum Optimization** -- a direct QUBO/QAOA experiment.
* **Hybrid Quantum-Classical Optimization** -- classical reduction + QAOA +
  classical post-processing.
* **Quantum-Enhanced Ensemble (VB-QER)** -- the final algorithm: classical
  members, validated quantum-derived artifacts, and an incumbent guard.

Live inference never calls a QPU. It consumes offline-validated artifacts.
"""

from routing.ensemble.inference import VBQEROptimizer, VBQERSolution

__all__ = ["VBQEROptimizer", "VBQERSolution"]

VBQER_VERSION = "vbqer_v1"
