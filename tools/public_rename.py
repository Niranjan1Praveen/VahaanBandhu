"""Normalise public-facing naming across the repository.

Two jobs:

1. **Branding.** The public project is "VahaanBandhu", not "VahaanBandhu 2.0".
2. **Internal stage labels.** Phase-A / Phase-B were private development
   labels. Publicly they should read as what they actually are: the research
   work and the application.

Deliberately context-aware rather than a blind find-replace. "Phase-A dataset"
becomes "research dataset", "Phase-B backend" becomes "application backend", and
so on, because a single mechanical substitution would produce nonsense like
"the research backend tests".

Stable internal identifiers (the `phase_a_v0.1` source tag written into data
rows, `PHASE_A_*` constants, filenames referenced by code) are left alone: they
are not public-facing and renaming them would invalidate committed artifacts.
"""

from __future__ import annotations

import pathlib
import re
import subprocess

# Ordered: longest / most specific first, so a general rule cannot pre-empt a
# specific one.
RULES: list[tuple[str, str]] = [
    # --- branding
    ("VahaanBandhu 2.0", "VahaanBandhu"),
    ("VahaanBandhu2.0", "VahaanBandhu"),

    # --- specific phrases, most specific first
    ("Phase-A research notebook", "Research notebook"),
    ("Phase-A/Phase-B boundary", "research/application boundary"),
    ("Phase-A/Phase-B", "research/application"),
    ("Phase-A and Phase-B", "the research and application layers"),
    ("Phase-A dataset", "research dataset"),
    ("Phase-A datasets", "research datasets"),
    ("Phase-A data", "research data"),
    ("Phase-A artifacts", "research artifacts"),
    ("Phase-A artifact", "research artifact"),
    ("Phase-A masters", "research masters"),
    ("Phase-A graph", "research road graph"),
    ("Phase-A benchmark", "research benchmark"),
    ("Phase-A research", "the routing research"),
    ("Phase-A quantum", "quantum routing research"),
    ("Phase-A tests", "research and routing tests"),
    ("Phase-A test", "research and routing test"),
    ("Phase-A suite", "research and routing suite"),
    ("Phase-A runtime", "research runtime"),
    ("Phase-A rule", "the quantity rule"),
    ("Phase-A note", "research note"),
    ("Phase-A result", "research result"),
    ("Phase-A work", "the routing research"),
    ("Phase-A stage", "the research stage"),
    ("Phase-A loader", "research data loader"),
    ("Phase-A packages", "research packages"),
    ("Phase-A optimization", "routing optimization"),
    ("Phase-A experiment", "research experiment"),
    ("Phase-A source", "research source"),

    ("Phase-B backend tests", "application backend tests"),
    ("Phase-B backend", "application backend"),
    ("Phase-B application", "the application"),
    ("Phase-B tests", "application tests"),
    ("Phase-B test", "application test"),
    ("Phase-B rule", "the application rule"),
    ("Phase-B architecture", "application architecture"),
    ("Phase-B development", "application development"),
    ("Phase-B work", "application development"),
    ("Phase-B progress", "application status"),

    # --- generic fallbacks, last
    ("Phase-A", "the routing research"),
    ("Phase A", "the routing research"),
    ("Phase-B", "the application"),
    ("Phase B", "the application"),
]

# Paths where internal labels are load-bearing identifiers, not prose.
SKIP_PATHS = {
    ".gitignore", ".dockerignore",
    "Data/source_registry.csv",
    "Res/quantum/hardware_job_registry.json",
}

# Tokens that must survive untouched wherever they appear: they are stable data
# values or code identifiers, not public copy.
PROTECTED = [
    "phase_a_v0.1", "PHASE_A_PROGRESS", "PHASE_B_PROGRESS", "phase_a",
    "PHASE_A", "PHASE_B", "phase-b-app-revamp",
]


def tracked_text_files() -> list[pathlib.Path]:
    out = subprocess.run(["git", "ls-files"], capture_output=True, text=True).stdout
    keep_ext = {".md", ".py", ".js", ".jsx", ".json", ".yml", ".yaml",
                ".txt", ".ini", ".ipynb"}
    paths = []
    for line in out.splitlines():
        p = pathlib.Path(line)
        if line in SKIP_PATHS or p.suffix not in keep_ext:
            continue
        paths.append(p)
    return paths


def main() -> None:
    changed = 0
    for p in tracked_text_files():
        try:
            s = original = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue

        # Shield protected tokens so the generic rules cannot mangle them.
        shields = {}
        for i, tok in enumerate(PROTECTED):
            if tok in s:
                key = f"\x00SHIELD{i}\x00"
                shields[key] = tok
                s = s.replace(tok, key)

        for old, new in RULES:
            if old in s:
                s = s.replace(old, new)
            # Case-insensitive variants that appear in prose.
            s = re.sub(rf"\b{re.escape(old.lower())}\b", new.lower(), s)

        for key, tok in shields.items():
            s = s.replace(key, tok)

        if s != original:
            p.write_text(s, encoding="utf-8")
            changed += 1
            print(f"  {p}")
    print(f"\n{changed} file(s) updated")


if __name__ == "__main__":
    main()
