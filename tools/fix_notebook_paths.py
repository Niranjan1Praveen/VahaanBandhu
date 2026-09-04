"""Make the research notebooks locate the repository root robustly.

The notebooks previously assumed they sat one directory below the repo root and
used `Path.cwd().parent`. They now live in `research/notebooks/`, two levels
down, so that assumption is wrong and every import would fail.

Rather than hard-coding a new depth (which breaks again on the next move), walk
upward until a directory containing the `vb` package is found.
"""

from __future__ import annotations

import json
import pathlib

OLD = 'sys.path.insert(0, str(Path.cwd().parent))'
NEW = '''# Walk up to the repository root (the directory containing the `vb` package)
# rather than assuming a fixed depth, so the notebook keeps working wherever it
# is opened from.
_root = Path.cwd()
while not (_root / "vb").is_dir() and _root != _root.parent:
    _root = _root.parent
sys.path.insert(0, str(_root))'''

NOTEBOOKS = [
    "research/notebooks/synthetic_data_generation.ipynb",
    "research/notebooks/route_optimization_classical_quantum.ipynb",
]


def main() -> None:
    for path in NOTEBOOKS:
        p = pathlib.Path(path)
        if not p.exists():
            print(f"  missing: {path}")
            continue
        nb = json.loads(p.read_text(encoding="utf-8"))
        changed = 0
        for cell in nb["cells"]:
            src = "".join(cell.get("source", []))
            if OLD in src:
                cell["source"] = (src.replace(OLD, NEW)).splitlines(keepends=True)
                changed += 1
        if changed:
            p.write_text(json.dumps(nb, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"  {path}: {changed} cell(s) updated")


if __name__ == "__main__":
    main()
