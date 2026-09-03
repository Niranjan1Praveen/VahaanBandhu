"""Stable, deterministic identifier generation.

IDs must be stable across regeneration runs for a fixed (seed, config), because
route solutions, splits and cached optimization artifacts reference them.
We therefore derive IDs from content, not from row order.
"""

from __future__ import annotations

import hashlib
import re

PREFIXES = {
    "location": "LOC",
    "mandi": "MND",
    "shop": "SHP",
    "farmer_node": "FRM",
    "truck": "TRK",
    "crop": "CRP",
    "request": "REQ",
    "availability": "AVL",
    "edge": "EDG",
    "instance": "INS",
    "solution": "SOL",
    "source": "SRC",
    "scenario": "SCN",
    "cost_snapshot": "CST",
    "qubo": "QBO",
}

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def slug(text: str) -> str:
    """Lowercase ASCII slug. Non-ASCII (e.g. Devanagari) collapses to empty,
    which is why callers must always pass a discriminating English key too."""
    return _SLUG_RE.sub("-", text.strip().lower()).strip("-")


def content_id(kind: str, *parts: object, length: int = 12) -> str:
    """Deterministic ID from the semantic content of a record.

    Two records with identical business keys always get the same ID, so a
    regenerated dataset stays join-compatible with cached solver results.
    """
    if kind not in PREFIXES:
        raise KeyError(f"unknown id kind: {kind!r}")
    key = "|".join(str(p) for p in parts)
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:length].upper()
    return f"{PREFIXES[kind]}_{digest}"


def edge_id(origin_location_id: str, destination_location_id: str, scenario_id: str) -> str:
    """Directed edge ID. A->B and B->A are deliberately different."""
    return content_id("edge", origin_location_id, destination_location_id, scenario_id)


def instance_hash(node_ids: list[str], demands: list[float], capacity: float) -> str:
    """Structural fingerprint of an optimization instance.

    Used to keep near-identical instances out of opposite train/test splits.
    Node order is normalized so a permuted-but-identical instance collides.
    """
    payload = "|".join(sorted(node_ids)) + "#" + "|".join(
        f"{d:.3f}" for d in sorted(demands)
    ) + f"#{capacity:.1f}"
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def file_sha256(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()
