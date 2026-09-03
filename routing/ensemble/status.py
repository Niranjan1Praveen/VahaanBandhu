"""VB-QER component status registry.

**Project invariant.** VB-QER is VahaanBandhu's final Quantum-Enhanced Ensemble
routing algorithm. Its architecture is FIXED. Classical solvers, QUBO
formulations, QAOA, quantum-derived artifacts and circular-logistics
optimization are *components within* VB-QER, not alternatives to it. Real
quantum hardware is used offline for training, experimentation and artifact
generation, never as a mandatory live-routing dependency.

This module exists to keep two things from being confused again, because they
were confused once already:

* **Architecture identity** -- which algorithm VahaanBandhu ships. Fixed.
* **Component status** -- which parts are currently contributing. Varies with
  experimental evidence.

A component moving from ACTIVE to REJECTED says nothing about the architecture.
An artifact failing validation means the artifact is not deployed; it does not
mean the ensemble should be replaced by one of its own members.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ComponentStatus(str, Enum):
    """Lifecycle of a VB-QER component or artifact."""

    ACTIVE = "ACTIVE"                    # contributing to live decisions
    ACTIVE_OFFLINE = "ACTIVE_OFFLINE"    # runs offline only (research/training)
    OFFLINE_ONLY = "OFFLINE_ONLY"        # must never enter the live path
    VALIDATION_GATED = "VALIDATION_GATED"  # activates only on passing held-out validation
    EXPERIMENTAL = "EXPERIMENTAL"
    VALIDATED = "VALIDATED"
    REJECTED = "REJECTED"                # failed validation; not deployed
    STALE = "STALE"                      # was valid, now expired


ARCHITECTURE = {
    "final_algorithm": "VB-QER",
    "full_name": "VahaanBandhu Quantum-Enhanced Routing Ensemble",
    "status": "FIXED",
    "entry_point": "routing.ensemble.VBQEROptimizer().solve(instance)",
    "note": (
        "Not under evaluation. Individual solvers are components, baselines or "
        "research arms -- none of them replaces VB-QER."
    ),
}


@dataclass(frozen=True)
class Component:
    name: str
    status: ComponentStatus
    role: str
    evidence: str


COMPONENTS: list[Component] = [
    Component(
        "classical_ensemble", ComponentStatus.ACTIVE,
        "Candidate generation (2-opt / NN / SA / OR-Tools) with consensus and "
        "diversity signals, scored on the true objective.",
        "Beats the best single classical member by 2.7% mean objective and cuts "
        "mean empty running 63% (84.9 -> 31.5 km) on the held-out test split.",
    ),
    Component(
        "circular_qubo", ComponentStatus.ACTIVE,
        "Return-load selection as a quadratic knapsack, solved exactly at "
        "current problem sizes.",
        "Lifts optimal rate from 77.5% (greedy) to 95.0%, mean gap 26.5 -> 3.3.",
    ),
    Component(
        "incumbent_guard", ComponentStatus.ACTIVE,
        "Rejects any infeasible or non-improving candidate.",
        "Converted 50% raw QAOA degradation into 0% deployed degradation.",
    ),
    Component(
        "objective_alignment", ComponentStatus.ACTIVE,
        "Per-edge costs in true objective units for every member.",
        "Classical solvers previously optimized distance; even a distance-exact "
        "solver showed 2.4% objective excess.",
    ),
    Component(
        "qaoa_simulator_research", ComponentStatus.ACTIVE_OFFLINE,
        "QAOA over VB-QER's QUBO formulations; source of candidate artifacts.",
        "Reaches 85.0% optimal on return-load selection vs 77.5% greedy, but "
        "47x slower and worse than the exact solve of the same QUBO.",
    ),
    Component(
        "ibm_quantum_hardware", ComponentStatus.OFFLINE_ONLY,
        "Offline benchmarking and artifact generation.",
        "Connectivity verified (ibm_fez / ibm_marrakesh / ibm_kingston). Never "
        "in the live request path -- enforced by a subprocess import test.",
    ),
    Component(
        "quantum_route_prior_v1", ComponentStatus.REJECTED,
        "Edge marginals distilled from route-track QAOA distributions.",
        "Failed held-out validation: 0/15 instances improved, mean delta 0.0. "
        "Not deployed. Superseded by circular-track distillation.",
    ),
    Component(
        "quantum_circular_artifacts", ComponentStatus.VALIDATION_GATED,
        "Return-load marginals, synergy priors and QAOA parameter priors "
        "distilled from the circular track.",
        "Under active investigation -- the circular track has a 16.4% feasible "
        "sampling rate vs the route track's thin 12/30 yield.",
    ),
]

BY_NAME = {c.name: c for c in COMPONENTS}


def summary() -> dict:
    """Architecture identity and component status, reported separately."""
    return {
        "architecture": ARCHITECTURE,
        "components": {
            c.name: {"status": c.status.value, "role": c.role, "evidence": c.evidence}
            for c in COMPONENTS
        },
    }


def render() -> str:
    lines = [
        f"FINAL ALGORITHM : {ARCHITECTURE['final_algorithm']}  "
        f"[{ARCHITECTURE['status']}]",
        f"ENTRY POINT     : {ARCHITECTURE['entry_point']}",
        "",
        "COMPONENT STATUS (varies with evidence; does not change the architecture)",
    ]
    for c in COMPONENTS:
        lines.append(f"  {c.name:32s} {c.status.value}")
    return "\n".join(lines)
