"""Versioned dataset writing with manifests.

Every write records enough metadata -- seed, config hash, git commit, row/column
counts, file hash -- that a reader can tell exactly which generation run produced
a file, and a maintainer can tell whether two files are comparable.

Published versions are never silently overwritten: writing to an existing
(version, table) pair requires an explicit ``overwrite=True``.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from vb.config import MANIFESTS, GenerationConfig
from vb.ids import file_sha256


def git_commit() -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, timeout=10,
        )
        return out.stdout.strip() if out.returncode == 0 else "unavailable"
    except Exception:
        return "unavailable"


def write_table(
    df: pd.DataFrame,
    path: Path,
    cfg: GenerationConfig,
    *,
    description: str,
    provenance: str,
    overwrite: bool = False,
) -> dict:
    """Write a CSV and its manifest entry.

    Args:
        provenance: "verified", "synthetic", "mixed", or "derived". Recorded in
            the manifest so consumers never have to guess whether a table is
            real-world data.
    """
    if path.exists() and not overwrite:
        raise FileExistsError(
            f"{path} already exists for version {cfg.dataset_version}. "
            "Bump dataset_version or pass overwrite=True."
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8")

    entry = {
        "table": path.stem,
        "path": str(path.relative_to(path.parents[2]) if len(path.parents) > 2 else path),
        "dataset_version": cfg.dataset_version,
        "stage": cfg.stage,
        "provenance": provenance,
        "description": description,
        "rows": int(len(df)),
        "columns": list(df.columns),
        "n_columns": int(df.shape[1]),
        "seed": cfg.seed,
        "config_hash": cfg.config_hash(),
        "git_commit": git_commit(),
        "file_sha256": file_sha256(path),
        "written_at": datetime.now(timezone.utc).isoformat(),
    }

    MANIFESTS.mkdir(parents=True, exist_ok=True)
    manifest_path = MANIFESTS / f"{cfg.dataset_version}_{cfg.stage}.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {"tables": {}}
    manifest["tables"][path.stem] = entry
    manifest["dataset_version"] = cfg.dataset_version
    manifest["updated_at"] = entry["written_at"]
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return entry


def read_table(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, encoding="utf-8")
