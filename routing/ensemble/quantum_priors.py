"""Quantum-derived artifacts: distillation, storage and provenance.

The premise the follow-up brief sets is that offline quantum experiments must
produce something the live system actually uses. This module is where a
measurement distribution becomes a deployable artifact -- and where an artifact
that fails to generalise is refused.

**What gets distilled.** A QAOA run returns a distribution over bitstrings, not
just one answer. Aggregating that distribution over many problems in a family
gives a *marginal selection probability* per decision variable: how often the
quantum optimizer wanted a given return load, weighted by how good the samples
containing it were. That marginal is a prior, and it is small, portable and
scenario-conditioned.

**Provenance is never lost.** Every artifact records whether it came from a
simulator, real hardware, or a classical QUBO solve. Simulator and hardware
results are stored separately and never silently merged -- they are different
experiments with different noise characteristics, and averaging them would hide
exactly the comparison the ablation needs to make.

**Artifacts must earn deployment.** ``validate_prior`` measures a prior against
held-out problems. A prior that does not beat the no-prior baseline on held-out
data is marked ``deployable=False`` and the ensemble will refuse to load it.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field

import numpy as np

from routing.cache.result_store import ArtifactStore
from vb.enums import Volatility
from vb.io import git_commit

PRIOR_VERSION = "quantum_prior_v1"

ARTIFACT_SOURCES = ("classical", "quantum_simulator", "quantum_hardware", "hybrid")


@dataclass
class QuantumPrior:
    """A deployable, versioned quantum-derived artifact."""

    artifact_id: str
    artifact_version: str
    source: str  # one of ARTIFACT_SOURCES
    problem_family: str
    # Marginal probability that each decision variable is selected in good
    # quantum samples. Keyed by a stable variable label, not an index, so it
    # survives a change in variable ordering.
    variable_marginals: dict[str, float]
    # Learned QAOA angles for warm-starting the same family.
    qaoa_params: list[float] | None
    n_layers: int | None
    dataset_version: str
    graph_version: str
    training_split: str
    cost_snapshot_ids: list[str]
    quantum_backend: str | None
    n_problems_distilled: int
    mean_feasible_rate: float | None
    deployable: bool = False
    validation: dict = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    git_commit: str = field(default_factory=git_commit)
    notes: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def distil_marginals(
    samples: list[tuple[dict[str, int], dict[str, float]]],
    *,
    energy_weighting: bool = True,
) -> dict[str, float]:
    """Turn measurement distributions into per-variable selection marginals.

    Args:
        samples: One entry per problem: (counts_by_label, energy_by_label) where
            counts_by_label maps a stable variable label to how many shots
            selected it, and energy_by_label gives the mean energy of samples
            selecting it.

    Weighting by energy matters. An unweighted marginal counts every shot
    equally, including the overwhelming majority that violate constraints, and
    would mostly encode the mixer's uniform prior rather than anything the cost
    Hamiltonian learned.
    """
    totals: dict[str, list[float]] = {}
    for counts, energies in samples:
        total_shots = sum(counts.values()) or 1
        for label, c in counts.items():
            p = c / total_shots
            if energy_weighting and label in energies:
                # Lower energy is better; weight good outcomes more.
                e = energies[label]
                w = 1.0 / (1.0 + max(e, 0.0))
                p = p * w
            totals.setdefault(label, []).append(p)

    if not totals:
        return {}
    raw = {k: float(np.mean(v)) for k, v in totals.items()}
    hi = max(raw.values()) or 1.0
    return {k: round(v / hi, 6) for k, v in raw.items()}


def validate_prior(
    prior: QuantumPrior,
    heldout_scores: list[tuple[float, float]],
    *,
    min_improvement: float = 0.0,
) -> QuantumPrior:
    """Decide whether a prior may be deployed, using held-out problems only.

    Args:
        heldout_scores: (baseline_objective, with_prior_objective) pairs from
            problems the prior was NOT distilled from.

    A prior that does not beat the baseline on held-out data is not deployed.
    This is the guard against shipping a "quantum feature" that is really noise
    fitted to the training set.
    """
    if not heldout_scores:
        prior.deployable = False
        prior.validation = {"reason": "no held-out evaluation was performed"}
        return prior

    base = np.array([b for b, _ in heldout_scores], dtype=float)
    with_p = np.array([w for _, w in heldout_scores], dtype=float)
    delta = base - with_p  # positive means the prior helped

    improved = int((delta > 1e-9).sum())
    degraded = int((delta < -1e-9).sum())
    mean_delta = float(delta.mean())

    prior.validation = {
        "n_heldout": len(heldout_scores),
        "n_improved": improved,
        "n_degraded": degraded,
        "n_unchanged": len(heldout_scores) - improved - degraded,
        "mean_delta": mean_delta,
        "improvement_rate": improved / len(heldout_scores),
        "criterion": f"mean_delta > {min_improvement}",
    }
    prior.deployable = bool(mean_delta > min_improvement)
    if not prior.deployable:
        prior.validation["reason"] = (
            "did not improve held-out objectives; not deployed")
    return prior


def save_prior(prior: QuantumPrior, store: ArtifactStore | None = None) -> str:
    """Persist a prior under Res/ensemble/quantum_priors with its manifest."""
    if prior.source not in ARTIFACT_SOURCES:
        raise ValueError(f"unknown artifact source: {prior.source}")
    store = store or ArtifactStore()
    store.save(
        "ensemble/quantum_priors", prior.artifact_id, prior.to_dict(),
        instance_id=prior.problem_family,
        cost_snapshot_id=(prior.cost_snapshot_ids[0]
                          if prior.cost_snapshot_ids else "unspecified"),
        algorithm_family="quantum" if prior.source.startswith("quantum") else "hybrid",
        algorithm_name=f"qaoa_prior_p{prior.n_layers}",
        volatility=Volatility.STATIC,
        artifact_version=prior.artifact_version,
        source=prior.source,
        deployable=prior.deployable,
    )
    return prior.artifact_id


def load_priors(
    store: ArtifactStore | None = None, *, source: str | None = None,
    deployable_only: bool = True,
) -> list[QuantumPrior]:
    """Load stored priors, optionally filtered by provenance.

    ``source`` filtering is what lets the ablation run "simulator-derived only"
    and "hardware-derived only" arms separately, which is the only way to answer
    whether hardware information is worth more than simulator information.
    """
    store = store or ArtifactStore()
    out: list[QuantumPrior] = []
    for name in store.list("ensemble/quantum_priors"):
        raw = store.load("ensemble/quantum_priors", name)
        if not raw:
            continue
        p = QuantumPrior(**raw)
        if source and p.source != source:
            continue
        if deployable_only and not p.deployable:
            continue
        out.append(p)
    return out
