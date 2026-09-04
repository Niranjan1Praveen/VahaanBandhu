"""Non-blocking IBM Quantum job inspection.

the application rule: hardware monitoring must never block application development, and
must never use a blocking ``job.result()`` call in a foreground process. This
script queries job *status* only, records it, and exits.

Scientific rule enforced here: a real-hardware result means measurements
actually returned from a QPU. Authentication, seeing backends, transpiling
against a backend, or a queued job are **not** hardware results and are
reported in separate categories.

    python tools/ibm_job_monitor.py            # inspect + record
    python tools/ibm_job_monitor.py --retrieve # also pull results for DONE jobs
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from routing.quantum.ibm_runtime import IBMQuantumRunner  # noqa: E402
from vb import config as C  # noqa: E402

STATE_PATH = C.RES / "quantum" / "ibm_job_monitor.json"

# Our the routing research Experiment-H submission. Recorded explicitly because the account
# also contains older, unrelated jobs from previous work: without pinning the
# job id, "a DONE job with counts exists on this account" would be mistaken for
# "our experiment returned hardware measurements". Those are different claims.
OUR_JOB_IDS = {
    "dacft8l1ierc738ji9a0": {
        "experiment": "experiment_h_ibm_hardware",
        "submitted": "2026-09-03T10:29:14+05:30",
        "backend_requested": "ibm_kingston",
        "circuit": "QAOA p=1, 5 qubits, edge-selection QUBO (diamond validation graph)",
        "parameters_source": "optimized on a noiseless simulator, then transferred",
    },
}

# Statuses that mean the job is still legitimately in flight. Per the the application
# brief these must NOT be cancelled merely because they have waited hours.
IN_FLIGHT = {"INITIALIZING", "QUEUED", "VALIDATING", "RUNNING"}


def inspect(retrieve: bool = False) -> dict:
    runner = IBMQuantumRunner()
    record: dict = {
        "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "auth_status": runner.status,
        # Explicitly separated categories -- none of these is a hardware result.
        "authenticated": bool(runner.available),
        "backends_visible": [],
        "jobs": [],
        # Scoped to OUR experiment only. A DONE job elsewhere on the account
        # says nothing about whether our experiment returned measurements.
        "our_jobs": {},
        "our_hardware_measurements_returned": False,
        "other_account_jobs_with_counts": 0,
    }

    if not runner.available:
        record["note"] = ("Not authenticated. This is not a hardware failure, "
                          "and application development continues regardless.")
        _save(record)
        return record

    try:
        record["backends_visible"] = [
            {"name": b.name, "qubits": b.n_qubits, "pending_jobs": b.pending_jobs}
            for b in runner.list_backends(min_qubits=5)
        ]
    except Exception as e:
        record["backend_query_error"] = f"{type(e).__name__}: {e}"

    try:
        jobs = runner.service.jobs(limit=15)
    except Exception as e:
        record["job_query_error"] = f"{type(e).__name__}: {e}"
        _save(record)
        return record

    for j in jobs:
        try:
            status = str(j.status())
        except Exception as e:
            status = f"UNKNOWN({type(e).__name__})"
        entry = {
            "job_id": j.job_id(),
            "status": status,
            "backend": getattr(getattr(j, "backend", lambda: None)(), "name", None),
            "in_flight": any(s in status.upper() for s in IN_FLIGHT),
        }
        for attr, key in (("creation_date", "created"), ("_created", "created")):
            v = getattr(j, attr, None)
            if v is not None:
                entry[key] = str(v() if callable(v) else v)
                break

        # Only a DONE job with retrievable counts is a hardware result.
        if retrieve and "DONE" in status.upper():
            try:
                res = j.result()
                counts = res[0].data.c.get_counts()
                entry["counts_returned"] = True
                entry["n_distinct_bitstrings"] = len(counts)
                entry["total_shots"] = int(sum(counts.values()))
                entry["counts_top10"] = dict(
                    sorted(counts.items(), key=lambda kv: -kv[1])[:10])
            except Exception as e:
                entry["retrieve_error"] = f"{type(e).__name__}: {e}"
        entry["is_ours"] = entry["job_id"] in OUR_JOB_IDS
        if entry["is_ours"]:
            entry.update(OUR_JOB_IDS[entry["job_id"]])
            record["our_jobs"][entry["job_id"]] = entry
            if entry.get("counts_returned"):
                record["our_hardware_measurements_returned"] = True
        elif entry.get("counts_returned"):
            record["other_account_jobs_with_counts"] += 1
        record["jobs"].append(entry)

    record["n_in_flight"] = sum(1 for j in record["jobs"] if j["in_flight"])
    record["our_jobs_in_flight"] = sum(
        1 for j in record["our_jobs"].values() if j["in_flight"])
    _save(record)
    return record


def _save(record: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    history: list = []
    if STATE_PATH.exists():
        try:
            history = json.loads(STATE_PATH.read_text(encoding="utf-8")).get("history", [])
        except json.JSONDecodeError:
            history = []
    history.append(record)
    STATE_PATH.write_text(
        json.dumps({"latest": record, "history": history[-40:]}, indent=2, default=str),
        encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--retrieve", action="store_true",
                    help="pull measurement counts for DONE jobs")
    a = ap.parse_args()
    r = inspect(retrieve=a.retrieve)
    print(json.dumps(
        {k: v for k, v in r.items() if k != "backends_visible"},
        indent=2, default=str)[:2500])
    print(f"\nbackends visible: {[b['name'] for b in r.get('backends_visible', [])]}")
    print("\n--- OUR EXPERIMENT ---")
    for jid, j in r.get("our_jobs", {}).items():
        print(f"  {jid}  status={j['status']}  backend={j.get('backend')}")
    if not r.get("our_jobs"):
        print("  (our job not in the recent-jobs window)")
    print(f"OUR HARDWARE MEASUREMENTS RETURNED: "
          f"{r.get('our_hardware_measurements_returned')}")
    print(f"(unrelated pre-existing account jobs with counts: "
          f"{r.get('other_account_jobs_with_counts')} -- NOT our results)")


if __name__ == "__main__":
    main()
