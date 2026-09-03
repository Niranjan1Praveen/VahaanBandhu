"""On-disk caches and the reusable-artifact store under ``Res/``.

Two distinct things live here and must not be confused:

* **RouteCache** is a short-TTL *operational* cache of provider responses. It
  exists to avoid hammering the API while developing and to make notebooks
  reproducible offline. It is explicitly **not** a training corpus -- TomTom's
  terms on storing and redistributing responses are unverified, so nothing from
  this cache may be promoted into ``Data/``.

* **ArtifactStore** holds derived optimization artifacts we *do* own: QUBO
  matrices, benchmark results, learned QAOA parameters, route priors.

Every cached item declares its volatility. Traffic is dynamic and expires in
minutes; a QUBO for a fixed cost matrix is static and never expires. Blindly
reusing a cached route is how a routing engine starts confidently returning
yesterday's traffic.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from vb.config import RES
from vb.enums import Volatility

# Time-to-live by volatility class, in seconds.
TTL_SECONDS = {
    Volatility.DYNAMIC: 15 * 60,        # traffic-adjusted routes
    Volatility.SEMI_STATIC: 30 * 24 * 3600,  # road topology, distances
    Volatility.STATIC: None,            # never expires
}


def _key(payload: dict) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, default=str).encode()
    ).hexdigest()[:24]


@dataclass
class CacheEntry:
    key: str
    value: Any
    volatility: str
    stored_at: float
    meta: dict

    @property
    def age_seconds(self) -> float:
        return time.time() - self.stored_at

    def is_valid(self) -> bool:
        ttl = TTL_SECONDS[Volatility(self.volatility)]
        return ttl is None or self.age_seconds < ttl


class RouteCache:
    """File-backed cache for provider responses."""

    def __init__(self, directory: Path | None = None) -> None:
        self.dir = directory or (RES / "route_cache")
        self.dir.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        return self.dir / f"{key}.json"

    def get(self, request: dict) -> Any | None:
        """Return a cached value, or None if absent or expired."""
        p = self._path(_key(request))
        if not p.exists():
            return None
        try:
            raw = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None
        entry = CacheEntry(**raw)
        if not entry.is_valid():
            # Expired traffic data is worse than none: it looks authoritative.
            p.unlink(missing_ok=True)
            return None
        return entry.value

    def put(
        self, request: dict, value: Any,
        volatility: Volatility = Volatility.DYNAMIC, **meta,
    ) -> str:
        key = _key(request)
        entry = CacheEntry(key=key, value=value, volatility=volatility.value,
                           stored_at=time.time(), meta={"request": request, **meta})
        self._path(key).write_text(
            json.dumps(entry.__dict__, indent=2, default=str), encoding="utf-8"
        )
        return key

    def clear_expired(self) -> int:
        n = 0
        for p in self.dir.glob("*.json"):
            try:
                entry = CacheEntry(**json.loads(p.read_text(encoding="utf-8")))
            except Exception:
                continue
            if not entry.is_valid():
                p.unlink(missing_ok=True)
                n += 1
        return n


class ArtifactStore:
    """Versioned store for reusable optimization outputs under ``Res/``.

    Every artifact is written with a manifest entry naming the instance, cost
    snapshot, algorithm and seed that produced it. An artifact whose manifest
    does not name a cost snapshot cannot be compared against anything and is
    rejected on write.
    """

    def __init__(self, root: Path | None = None) -> None:
        self.root = root or RES
        self.manifest_dir = self.root / "manifests"
        self.manifest_dir.mkdir(parents=True, exist_ok=True)

    def save(
        self, category: str, name: str, payload: dict, *,
        instance_id: str, cost_snapshot_id: str, algorithm_family: str,
        algorithm_name: str, volatility: Volatility = Volatility.STATIC,
        **meta,
    ) -> Path:
        if not cost_snapshot_id:
            raise ValueError(
                "artifact must name the cost snapshot it was computed against; "
                "results without one cannot be compared to anything"
            )
        d = self.root / category
        d.mkdir(parents=True, exist_ok=True)
        path = d / f"{name}.json"
        path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")

        entry = {
            "category": category, "name": name, "path": str(path),
            "instance_id": instance_id, "cost_snapshot_id": cost_snapshot_id,
            "algorithm_family": algorithm_family, "algorithm_name": algorithm_name,
            "volatility": volatility.value, "created_at": time.time(), **meta,
        }
        # A nested category (e.g. "ensemble/quantum_priors") makes the manifest
        # path nested too, so its parent must be created explicitly.
        mpath = self.manifest_dir / f"{category}.json"
        mpath.parent.mkdir(parents=True, exist_ok=True)
        manifest = json.loads(mpath.read_text(encoding="utf-8")) if mpath.exists() else {}
        manifest[name] = entry
        mpath.write_text(json.dumps(manifest, indent=2, default=str), encoding="utf-8")
        return path

    def load(self, category: str, name: str) -> dict | None:
        p = self.root / category / f"{name}.json"
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None

    def list(self, category: str) -> dict:
        mpath = self.manifest_dir / f"{category}.json"
        if not mpath.exists():
            return {}
        try:
            return json.loads(mpath.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
