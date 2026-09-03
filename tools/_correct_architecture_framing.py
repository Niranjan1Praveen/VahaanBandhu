"""One-shot: correct the architectural framing in the research report.

Corrects an interpretation error. The Part II and Part III *measurements* stand
unchanged -- the QAOA prior did fail validation and that remains stated. What was
wrong was the recommendation language, which framed "classical" as an
alternative to VB-QER when the classical ensemble is a VB-QER component.
"""

from __future__ import annotations

import pathlib

INVARIANT = r"""
---

## 0a. PROJECT INVARIANT - VB-QER is the final algorithm

**VB-QER (VahaanBandhu Quantum-Enhanced Routing Ensemble) is VahaanBandhu's final
routing algorithm. Its architecture is FIXED and is not under evaluation.**

```
                         VB-QER
                           |
        +------------------+------------------+
        |                  |                  |
        v                  v                  v
   CLASSICAL          QUANTUM /          LOGISTICS
   ENSEMBLE             QUBO              OPTIMIZERS
        |                  |                  |
        +------------------+------------------+
                           v
                 ENSEMBLE DECISION
                           v
                FEASIBILITY VALIDATION
                           v
                  INCUMBENT GUARD
                           v
                      FINAL ROUTE
```

Dijkstra, A*, OR-Tools, 2-opt, simulated annealing, classical QUBO and standalone
QAOA are **components, baselines or research arms inside VB-QER**. None of them
is an alternative to it. The application entry point is always:

```python
solution = VBQEROptimizer().solve(instance)
```

never a conditional such as `if quantum_available: ... else: use_classical()`.

### Architecture status vs component status

These are reported separately from here on, because conflating them produced an
incorrect recommendation in an earlier revision of this document.

| Item | Status |
|---|---|
| **Final algorithm: VB-QER** | **FIXED** |
| Classical ensemble | ACTIVE |
| Circular-logistics QUBO formulation | ACTIVE |
| Objective-alignment layer | ACTIVE |
| Incumbent guard | ACTIVE |
| QAOA simulator research | ACTIVE OFFLINE |
| IBM Quantum hardware | OFFLINE ONLY |
| Quantum-derived production artifacts | VALIDATION-GATED |

The last row may move between EXPERIMENTAL / VALIDATED / ACTIVE / REJECTED /
STALE **without changing the identity of the final algorithm**. A component
failing validation means that component is not deployed; it does not mean the
ensemble should be replaced by one of its own members.

Machine-readable equivalent: `routing/ensemble/status.py`.

### Correction notice

An earlier revision of this report recommended "ship the return-load formulation
solved classically" in language that implied choosing classical routing *instead
of* VB-QER. That framing was wrong. The classical ensemble and the circular QUBO
are VB-QER components, and both are ACTIVE. The correct statement is: **ship
VB-QER, in which the classical members and the circular QUBO are active and the
quantum-derived artifacts remain validation-gated.**

The experimental results themselves are unchanged and are not restated
favourably: the route-track QAOA prior failed held-out validation (0/15) and is
REJECTED. See Part III.
"""

REPLACEMENTS = [
    # --- Part II recommendation
    (
        """## 18. Recommendation

Ship the quadratic-knapsack return-load formulation solved **classically**. Keep
QAOA as an offline research arm. The architecture supports swapping the solver
without any other change, so this is reversible when hardware or algorithms
improve.""",
        """## 18. Recommendation

**Within VB-QER**, activate the quadratic-knapsack return-load formulation with
the **exact classical solver** as its current backend, and keep QAOA as an
offline research arm feeding the same formulation.

This is a component-level decision, not an architecture-level one. The QUBO
formulation is a VB-QER component either way; only the solver behind it changes,
and the architecture supports swapping that solver without touching anything
else. When QAOA or hardware improves, the backend flips and no interface moves.""",
    ),
    # --- Part III recommendation heading and body
    (
        """## 24. Production recommendation

**Ship VB-QER as the routing interface, with the quantum path disabled by
default until an artifact passes validation.**

This is not a retreat. The architecture is exactly what the brief specifies -
classical members, offline quantum artifacts, ensemble scoring, incumbent guard,
one entry point - and the quantum path is live code that engages the moment a
prior passes the gate. What the evidence does not currently support is *claiming*
a quantum contribution, and the system measures that rather than asserting it.

Concretely:

* **Adopt now:** the classical ensemble (2.7% objective, 63% empty-km reduction)
  and the quadratic-knapsack return-load formulation solved **classically**
  (77.5% -> 95% optimal).
* **Keep offline:** QAOA, as a research arm.
* **Do not claim:** any quantum advantage, speedup, or contribution to the live
  routing decision. There is none in the current evidence.""",
        """## 24. Production recommendation

**Ship VB-QER.** That is the fixed architecture and it is not in question here.
What this section reports is the *current status of VB-QER's components*.

| VB-QER component | Status | Contribution measured |
|---|---|---|
| Classical ensemble | **ACTIVE** | +2.7% objective, -63% empty km vs the best single member |
| Circular-logistics QUBO | **ACTIVE** (exact backend) | 77.5% -> 95.0% optimal |
| Objective-alignment layer | **ACTIVE** | corrected a 2.4% systematic excess |
| Incumbent guard | **ACTIVE** | 50% raw degradation -> 0% deployed |
| QAOA research arm | **ACTIVE OFFLINE** | 85.0% optimal; not yet a deployable artifact |
| Route-track quantum prior | **REJECTED** | failed held-out validation, 0/15 |
| Circular-track quantum artifacts | **VALIDATION-GATED** | under active investigation |

The quantum path is live code inside VB-QER that engages the moment an artifact
passes the gate. What the evidence does not currently support is *claiming* a
quantum contribution to live decisions, and the system measures that rather than
asserting it.

**Do not claim:** any quantum advantage, speedup, or contribution to the live
routing decision. There is none in the current evidence.""",
    ),
    # --- "What would change the answer" -> reframe as improving the component
    (
        """## 25. What would change the answer""",
        """## 25. Improving the quantum contribution inside VB-QER

The question is not whether to use VB-QER. It is how to raise the quantum
component's contribution within it. In priority order:""",
    ),
    # --- Part II section 11 framing
    (
        """> **Can a QUAV-inspired quantum refinement layer improve the strongest classical
> route, after classical search-space reduction?**

Architecture: `CLASSICAL + QUANTUM + CLASSICAL`, with the classical solution as a
safety net rather than a competitor.""",
        """> **Can a QUAV-inspired quantum refinement layer improve the strongest classical
> route, after classical search-space reduction?**

Architecture: `CLASSICAL + QUANTUM + CLASSICAL`, with the classical solution as a
safety net rather than a competitor. Both halves live inside VB-QER; this is a
question about one component's contribution, not about which algorithm to ship.""",
    ),
]


def main() -> None:
    p = pathlib.Path("Research/QUANTUM_ROUTE_OPTIMIZATION.md")
    s = p.read_text(encoding="utf-8")

    if "PROJECT INVARIANT - VB-QER is the final algorithm" not in s:
        marker = "\n---\n\n## 1. Review of the QUAV paper"
        assert marker in s, "invariant insertion marker not found"
        s = s.replace(marker, "\n" + INVARIANT.rstrip() + marker, 1)

    applied = 0
    for old, new in REPLACEMENTS:
        if old in s:
            s = s.replace(old, new, 1)
            applied += 1

    # Correct the Part I summary line that reads as an architecture verdict.
    s = s.replace(
        "**Phase-A answer: no improvement observed.** Details in §6.",
        "**Phase-A answer (component level): standalone QAOA showed no improvement.** "
        "This is a finding about one VB-QER component, not about the architecture. "
        "Details in §6.",
        1,
    )

    p.write_text(s, encoding="utf-8")
    print(f"updated {p}: invariant inserted, {applied}/{len(REPLACEMENTS)} replacements")


if __name__ == "__main__":
    main()
