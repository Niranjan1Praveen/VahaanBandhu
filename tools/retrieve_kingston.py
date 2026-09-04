"""Retrieve and decode the Kingston H1 result, completing the cross-QPU set.

Decoding uses the identical QUBO, feasibility rules and objective as the Fez and
Marrakesh runs, so the three are genuinely comparable — only hardware and
transpilation differ.
"""

from __future__ import annotations

import json
import time

from dotenv import load_dotenv

load_dotenv()

from routing.quantum.decoder import decode_counts  # noqa: E402
from routing.quantum.ibm_runtime import IBMQuantumRunner  # noqa: E402
from routing.quantum.qubo import brute_force_qubo  # noqa: E402
from tools.hardware_registry import H1, _load, _save, build_h1  # noqa: E402
from vb import config as C  # noqa: E402

JOB_ID = "dacft8l1ierc738ji9a0"
BACKEND = "ibm_kingston"


def main() -> None:
    runner = IBMQuantumRunner()
    if not runner.available:
        print("IBM Quantum unavailable; cannot retrieve.")
        return

    job = runner.service.job(JOB_ID)
    status = str(job.status())
    print(f"job {JOB_ID} status={status}")
    if "DONE" not in status.upper():
        print("not finished; nothing to retrieve.")
        return

    res = job.result()
    counts = res[0].data.c.get_counts()
    shots = int(sum(counts.values()))
    print(f"retrieved {len(counts)} distinct bitstrings over {shots} shots")

    # Rebuild the identical problem so decoding matches the other backends.
    qubo, optimum, sim = build_h1()
    dec = decode_counts(counts, qubo, None)
    best = dec["best"]

    out = {
        "record_id": "H1-KINGSTON",
        "job_id": JOB_ID,
        "backend": BACKEND,
        "shots": shots,
        "counts": counts,
        "feasible_sample_rate": dec["feasible_rate"],
        "feasible_shots": dec["feasible_shots"],
        "best_feasible_energy": best.energy if best else None,
        "best_feasible_path": best.tour if best else None,
        "classical_optimum": float(optimum),
        "matched_optimum": bool(best and abs(best.energy - optimum) < 1e-6),
        "simulator_best_energy": float(sim.best_energy),
        "simulator_feasible_rate": float(sim.feasible_rate),
        "queue_note": ("submitted 2026-09-03T10:29 IST, completed later the same "
                       "day; Kingston had 76 pending jobs at submission time "
                       "while Fez and Marrakesh had 0."),
        "retrieved_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    path = C.RES / "quantum" / f"H1_{BACKEND}_result.json"
    path.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print(f"feasible_rate={dec['feasible_rate']:.4f} "
          f"best={out['best_feasible_energy']} path={out['best_feasible_path']} "
          f"matched_optimum={out['matched_optimum']}")

    # Update the registry record in place.
    reg = _load()
    for r in reg["records"]:
        if r.get("job_id") == JOB_ID:
            r.update({
                "status": "DONE",
                "result_retrieved": True,
                "result_path": str(path),
                "feasible_sample_rate": dec["feasible_rate"],
                "best_feasible_energy": out["best_feasible_energy"],
            })
    _save(reg)
    print(f"registry updated -> {path}")


if __name__ == "__main__":
    main()
