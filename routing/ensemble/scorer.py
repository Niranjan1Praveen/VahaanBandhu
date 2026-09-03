"""VB-QER ensemble scoring.

The score combines classical optimization quality with ensemble-level and
quantum-derived signals:

    score(c) =  w_obj      * normalised_objective(c)
              - w_consensus * consensus(c)
              - w_diversity * diversity(c)
              - w_qprior    * quantum_prior_score(c)
              + w_infeasible * infeasibility_penalty(c)

Design decisions worth stating:

* **The objective term dominates by construction.** Ensemble signals adjust a
  ranking among candidates that are already close; they must never be able to
  promote a substantially worse route. Weights are constrained so the non-
  objective terms cannot exceed a bounded fraction of the objective spread.

* **Objective is normalised per instance**, because raw objective values differ
  by orders of magnitude across instances and a fixed weight against a raw
  objective would mean something different on every problem.

* **Weights are calibrated on training data only** (see ``calibrate.py``), never
  on the held-out test set.

* **A quantum prior contributes only if it was validated and deployed.** An
  unvalidated prior scores 0, which makes VB-QER degrade cleanly to a classical
  ensemble rather than failing.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from routing.ensemble.members import Candidate

# Starting weights. Calibration may adjust these within the bounds below.
DEFAULT_WEIGHTS = {
    "objective": 1.0,
    "consensus": 0.030,
    "diversity": 0.010,
    "quantum_prior": 0.040,
    "infeasible_penalty": 10.0,
}

# Ensemble signals may not move the score by more than this fraction of the
# normalised objective range. Without a cap, a strong consensus signal could
# promote a clearly worse route -- the ensemble would be voting instead of
# optimizing.
MAX_SIGNAL_INFLUENCE = 0.25


@dataclass
class ScoredCandidate:
    candidate: Candidate
    score: float
    terms: dict[str, float] = field(default_factory=dict)


def normalise_objectives(candidates: list[Candidate]) -> dict[str, float]:
    """Map objectives to [0, 1] within this instance; 0 is best."""
    vals = np.array([c.objective for c in candidates], dtype=float)
    finite = vals[np.isfinite(vals)]
    if finite.size == 0:
        return {c.candidate_id: 1.0 for c in candidates}
    lo, hi = float(finite.min()), float(finite.max())
    span = hi - lo
    if span <= 1e-12:
        return {c.candidate_id: 0.0 for c in candidates}
    return {
        c.candidate_id: float((c.objective - lo) / span) if np.isfinite(c.objective) else 1.0
        for c in candidates
    }


def score_candidates(
    candidates: list[Candidate], weights: dict[str, float] | None = None,
) -> list[ScoredCandidate]:
    """Score and rank a candidate pool. Lower score is better."""
    if not candidates:
        return []
    w = {**DEFAULT_WEIGHTS, **(weights or {})}
    norm = normalise_objectives(candidates)

    max_consensus = max(c.consensus for c in candidates) or 1
    out: list[ScoredCandidate] = []
    for c in candidates:
        terms = {
            "objective": w["objective"] * norm[c.candidate_id],
            "consensus": -w["consensus"] * (c.consensus / max_consensus),
            "diversity": -w["diversity"] * c.diversity,
            "quantum_prior": -w["quantum_prior"] * c.quantum_prior_score,
        }
        # Cap the combined influence of the non-objective signals.
        signal = terms["consensus"] + terms["diversity"] + terms["quantum_prior"]
        capped = float(np.clip(signal, -MAX_SIGNAL_INFLUENCE, MAX_SIGNAL_INFLUENCE))
        if capped != signal:
            scale = capped / signal if signal else 0.0
            for k in ("consensus", "diversity", "quantum_prior"):
                terms[k] *= scale
            terms["signal_capped"] = 1.0

        if not c.feasible:
            terms["infeasible_penalty"] = w["infeasible_penalty"]

        out.append(ScoredCandidate(candidate=c, score=float(sum(terms.values())),
                                   terms={k: round(v, 6) for k, v in terms.items()}))

    out.sort(key=lambda s: s.score)
    return out


def apply_quantum_prior(
    candidates: list[Candidate], prior_marginals: dict[str, float],
) -> int:
    """Attach quantum prior scores to candidates.

    A candidate's prior score is the mean marginal of the directed edges it uses,
    i.e. how much the offline quantum experiments favoured this route's
    structure. Returns how many candidates the prior actually touched, which the
    ensemble records so "quantum was used" is a measurement, not an assumption.
    """
    if not prior_marginals:
        return 0
    touched = 0
    for c in candidates:
        edges = [f"{c.tour[i]}->{c.tour[(i + 1) % len(c.tour)]}"
                 for i in range(len(c.tour))]
        hits = [prior_marginals[e] for e in edges if e in prior_marginals]
        if hits:
            c.quantum_prior_score = float(np.mean(hits))
            c.source = "quantum_informed"
            touched += 1
    return touched
