"""Generation configuration and project paths.

Every generator takes a GenerationConfig. The config is serialized alongside
each dataset release so a run can be reproduced exactly from seed + config.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Literal

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Data"
RAW = DATA / "raw"
RAW_OFFICIAL = RAW / "official"
RAW_OSM = RAW / "osm"
STAGING = DATA / "staging"
MASTER = DATA / "master"
SYNTHETIC = DATA / "synthetic"
FEATURES = DATA / "features"
SPLITS = DATA / "splits"
QA = DATA / "qa"
SOURCE_REGISTRY = DATA / "source_registry.csv"

METADATA = ROOT / "metadata"
GENERATION_CONFIGS = METADATA / "generation_configs"
MANIFESTS = METADATA / "manifests"
SCHEMAS = METADATA / "schemas"
VERSIONS = METADATA / "versions"

RES = ROOT / "Res"
RESEARCH = ROOT / "research"
NOTEBOOKS = RESEARCH / "notebooks"
RESEARCH_DOCS = RESEARCH / "docs"

Stage = Literal["prototype", "pilot", "training"]

# WGS84 everywhere in canonical tables.
CRS_WGS84 = "EPSG:4326"
# Metric CRS for distance/area math over north India. Only ever used inside
# derived feature computation; never replaces the canonical lat/lon.
CRS_METRIC = "EPSG:32644"  # UTM zone 44N

# Coarse rejection box for the four target states. This is a smoke test only;
# real containment is checked against district envelopes in vb.validate.qa.
#
# The the routing research spec suggested 23.0-31.5 N. That upper bound is too tight: it
# excludes Gurdaspur (~32.04 N) and Pathankot (~32.27 N), which are genuine
# Punjab districts, and rejected 176 valid locations. Raised to 32.6 N with
# headroom for their district envelopes.
COARSE_BBOX = {"lat_min": 23.0, "lat_max": 32.6, "lon_min": 73.0, "lon_max": 85.0}


@dataclass(frozen=True)
class StageSizes:
    """Row-count targets per generation stage."""

    n_villages: int
    n_shops: int
    n_farmer_nodes: int
    n_trucks: int
    n_requests: int
    n_route_instances: int
    n_quantum_instances: int


STAGE_SIZES: dict[str, StageSizes] = {
    "prototype": StageSizes(
        n_villages=2400,
        n_shops=900,
        n_farmer_nodes=1400,
        n_trucks=600,
        n_requests=18000,
        n_route_instances=2000,
        n_quantum_instances=200,
    ),
    "pilot": StageSizes(
        n_villages=26000,
        n_shops=9000,
        n_farmer_nodes=14000,
        n_trucks=6000,
        n_requests=180000,
        n_route_instances=20000,
        n_quantum_instances=1200,
    ),
    "training": StageSizes(
        n_villages=120000,
        n_shops=45000,
        n_farmer_nodes=70000,
        n_trucks=30000,
        n_requests=1200000,
        n_route_instances=120000,
        n_quantum_instances=2000,
    ),
}


@dataclass(frozen=True)
class GenerationConfig:
    """Everything needed to reproduce a dataset release."""

    stage: Stage = "prototype"
    seed: int = 20260903
    dataset_version: str = "v0.1"
    states: tuple[str, ...] = ("DL", "HR", "PB", "UP")

    # Request-mix knobs. Fractions of the total request corpus.
    frac_shop_requests: float = 0.30
    frac_infeasible: float = 0.08
    frac_ambiguous: float = 0.10
    frac_voice: float = 0.55
    lang_mix: tuple[float, float, float] = (0.40, 0.25, 0.35)  # hi, en, hinglish

    # Route graph knobs.
    knn_edges: int = 8
    max_edge_km: float = 180.0

    # Held-out districts for leakage-safe evaluation.
    holdout_districts: tuple[str, ...] = ("Karnal", "Bulandshahr", "Bathinda")
    # Late enough that the temporal holdout does not swallow the whole kharif
    # arrival season and blow the test share past ~20%.
    holdout_time_from: str = "2026-11-20"

    sizes: StageSizes = field(default=None)  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.sizes is None:
            object.__setattr__(self, "sizes", STAGE_SIZES[self.stage])

    def to_dict(self) -> dict:
        d = asdict(self)
        d["states"] = list(self.states)
        d["lang_mix"] = list(self.lang_mix)
        d["holdout_districts"] = list(self.holdout_districts)
        return d

    def config_hash(self) -> str:
        """Stable hash of the config, used to key generated artifacts."""
        blob = json.dumps(self.to_dict(), sort_keys=True).encode()
        return hashlib.sha256(blob).hexdigest()[:16]

    def save(self) -> Path:
        GENERATION_CONFIGS.mkdir(parents=True, exist_ok=True)
        path = GENERATION_CONFIGS / f"{self.dataset_version}_{self.stage}.json"
        payload = self.to_dict() | {"config_hash": self.config_hash()}
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return path


def ensure_dirs() -> None:
    for p in (
        RAW_OFFICIAL, RAW_OSM, STAGING, MASTER, SYNTHETIC, FEATURES, SPLITS, QA,
        GENERATION_CONFIGS, MANIFESTS, SCHEMAS, VERSIONS,
    ):
        p.mkdir(parents=True, exist_ok=True)
