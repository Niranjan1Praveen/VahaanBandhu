"""VahaanBandhu hardware job registry and controlled multi-QPU submission.

**Ownership rule.** Only jobs this project submits get ``owned_by_project:
true``. The IBM account also contains older jobs from unrelated work; those must
never be counted toward VahaanBandhu hardware totals. Every registry record
carries explicit ownership metadata.

**What counts as a hardware result.** Measurements actually returned from a QPU.
Not: authentication, seeing a backend, transpiling against one, submitting, or a
queued job. Those are tracked as separate states.

**Experiment H1** -- the controlled validation circuit. Identical QUBO, QAOA
depth, parameters, shots, decoding and objective across every backend, so that
only hardware and transpilation differ. Changing several variables at once and
then attributing the difference to hardware would be worthless.

    python tools/hardware_registry.py --inspect
    python tools/hardware_registry.py --submit-h1 --backends ibm_fez,ibm_marrakesh
    python tools/hardware_registry.py --retrieve
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
from dotenv import load_dotenv

load_dotenv()

from routing.quantum.decoder import decode_counts  # noqa: E402
from routing.quantum.ibm_runtime import IBMQuantumRunner  # noqa: E402
from routing.quantum.qaoa import build_qaoa_circuit, run_qaoa  # noqa: E402
from routing.quantum.qubo import brute_force_qubo, build_edge_selection_qubo  # noqa: E402
from vb import config as C  # noqa: E402

REGISTRY = C.RES / "quantum" / "hardware_job_registry.json"

# --- H1: the controlled validation problem. Frozen so every backend gets the
# identical workload. Diamond graph 0->{1,2}->3 plus an expensive direct link;
# true cheapest path is 0->2->3 at cost 2.5.
H1 = {
    "experiment_id": "H1_controlled_validation",
    "problem_id": "demo_diamond_graph",
    "edges": [(0, 1), (1, 3), (0, 2), (2, 3), (0, 3)],
    "costs": [2.0, 2.0, 1.0, 1.5, 9.0],
    "source": 0, "sink": 3, "n_nodes": 4,
    "qubo_version": "qubo_v1",
    "encoding_version": "edge_selection_v1",
    "qaoa_depth": 1,
    "shots": 1024,
    "parameter_source": "optimized on a noiseless simulator, then transferred",
    "cost_snapshot_id": "CST_DEMO_DIAMOND",
}

# Pre-existing Kingston submission from the routing research Experiment H.
SEED_RECORDS = [
    {
        "record_id": "H1-KINGSTON",
        "project": "VahaanBandhu",
        "experiment_id": "H1_controlled_validation",
        "job_id": "dacft8l1ierc738ji9a0",
        "backend": "ibm_kingston",
        "submission_time": "2026-09-03T10:29:14+05:30",
        "problem_id": "demo_diamond_graph",
        "qubo_version": "qubo_v1",
        "qaoa_depth": 1,
        "shots": 1024,
        "parameter_source": H1["parameter_source"],
        "status": "QUEUED",
        "owned_by_project": True,
        "result_retrieved": False,
        "result_path": None,
        "notes": "the routing research Experiment H original submission.",
    },
]


def _load() -> dict:
    if REGISTRY.exists():
        try:
            return json.loads(REGISTRY.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {"project": "VahaanBandhu", "records": SEED_RECORDS.copy()}


def _save(reg: dict) -> None:
    REGISTRY.parent.mkdir(parents=True, exist_ok=True)
    reg["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    REGISTRY.write_text(json.dumps(reg, indent=2, default=str), encoding="utf-8")


def build_h1():
    """Build the H1 QUBO and its simulator-optimized parameters."""
    qubo = build_edge_selection_qubo(
        H1["edges"], np.array(H1["costs"]), H1["source"], H1["sink"], H1["n_nodes"])
    _, optimum = brute_force_qubo(qubo)
    sim = run_qaoa(qubo, p=H1["qaoa_depth"], shots=2048, seed=7, maxiter=60)
    return qubo, optimum, sim


def inspect_backends() -> list[dict]:
    runner = IBMQuantumRunner()
    if not runner.available:
        return []
    out = []
    for name in ("ibm_fez", "ibm_marrakesh", "ibm_kingston"):
        entry = {"backend_name": name, "accessible": False}
        try:
            b = runner.service.backend(name)
            st = b.status()
            entry.update({
                "accessible": True,
                "operational": bool(st.operational),
                "pending_jobs": int(st.pending_jobs),
                "num_qubits": int(b.num_qubits),
                "status_msg": getattr(st, "status_msg", None),
                "simulator": bool(b.simulator),
                "processor_type": str(getattr(b, "processor_type", None)),
            })
        except Exception as e:
            entry["error"] = f"{type(e).__name__}: {e}"
        out.append(entry)
    return out


def submit_h1(backends: list[str]) -> dict:
    """Submit the identical H1 circuit to the named backends."""
    reg = _load()
    runner = IBMQuantumRunner()
    if not runner.available:
        print("IBM Quantum unavailable; no submission. the application continues.")
        return reg

    qubo, optimum, sim = build_h1()
    print(f"H1 classical optimum {optimum:.4f}; "
          f"simulator best {sim.best_energy:.4f} feasible {sim.feasible_rate:.2%}")

    qc, params = build_qaoa_circuit(qubo, H1["qaoa_depth"])
    bound = qc.assign_parameters(dict(zip(params, sim.optimal_params)))

    existing = {r["backend"] for r in reg["records"]
                if r.get("owned_by_project") and r["experiment_id"] == H1["experiment_id"]}

    for name in backends:
        if name in existing:
            print(f"skip {name}: already has an owned H1 job (no duplicate flooding)")
            continue
        try:
            backend = runner.service.backend(name)
            st = backend.status()
            if not st.operational:
                print(f"skip {name}: not operational")
                continue
        except Exception as e:
            print(f"skip {name}: {type(e).__name__}: {e}")
            continue

        print(f"submitting H1 to {name} (pending={st.pending_jobs}) ...")
        hw = runner.run_circuit(bound, shots=H1["shots"], backend=backend)
        rec = {
            "record_id": f"H1-{name.replace('ibm_', '').upper()}",
            "project": "VahaanBandhu",
            "experiment_id": H1["experiment_id"],
            "job_id": hw.get("job_id"),
            "backend": name,
            "submission_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "problem_id": H1["problem_id"],
            "qubo_version": H1["qubo_version"],
            "encoding_version": H1["encoding_version"],
            "qaoa_depth": H1["qaoa_depth"],
            "shots": H1["shots"],
            "parameter_source": H1["parameter_source"],
            "qaoa_parameters": [float(v) for v in sim.optimal_params],
            "classical_optimum": float(optimum),
            "simulator_best_energy": float(sim.best_energy),
            "simulator_feasible_rate": float(sim.feasible_rate),
            "cost_snapshot_id": H1["cost_snapshot_id"],
            "status": "SUBMITTED" if hw.get("executed") else "SUBMIT_FAILED",
            "owned_by_project": True,
            "result_retrieved": False,
            "result_path": None,
            "notes": "" if hw.get("executed") else f"submit failed: {hw.get('reason')}",
        }
        if hw.get("executed"):
            # run_circuit blocks until result; capture it directly.
            rec["status"] = "DONE"
            rec["transpiled_depth"] = hw.get("transpiled_depth")
            rec["transpiled_n_qubits"] = hw.get("transpiled_n_qubits")
            rec["logical_depth"] = hw.get("logical_depth")
            rec["wall_clock_s"] = hw.get("wall_clock_s")
            dec = decode_counts(hw["counts"], qubo, None)
            best = dec["best"]
            path = C.RES / "quantum" / f"H1_{name}_result.json"
            path.write_text(json.dumps({
                "record_id": rec["record_id"], "job_id": rec["job_id"],
                "backend": name, "shots": hw["shots"],
                "counts": hw["counts"],
                "feasible_sample_rate": dec["feasible_rate"],
                "feasible_shots": dec["feasible_shots"],
                "best_feasible_energy": best.energy if best else None,
                "best_feasible_path": best.tour if best else None,
                "classical_optimum": float(optimum),
                "matched_optimum": bool(best and abs(best.energy - optimum) < 1e-6),
                "simulator_best_energy": float(sim.best_energy),
                "simulator_feasible_rate": float(sim.feasible_rate),
                "transpiled_depth": hw.get("transpiled_depth"),
            }, indent=2, default=str), encoding="utf-8")
            rec["result_retrieved"] = True
            rec["result_path"] = str(path)
            rec["feasible_sample_rate"] = dec["feasible_rate"]
            rec["best_feasible_energy"] = best.energy if best else None
            print(f"  DONE  feasible_rate={dec['feasible_rate']:.2%} "
                  f"best={best.energy if best else None}")
        else:
            print(f"  not executed: {hw.get('reason')}")

        reg["records"].append(rec)
        _save(reg)
    return reg


def summarise(reg: dict) -> dict:
    owned = [r for r in reg["records"] if r.get("owned_by_project")]
    return {
        "total_vahaanbandhu_jobs_submitted": len(owned),
        "completed": sum(1 for r in owned if r["status"] == "DONE"),
        "still_queued": sum(1 for r in owned if r["status"] in ("QUEUED", "SUBMITTED")),
        "failed": sum(1 for r in owned if "FAIL" in r["status"]),
        "real_hardware_results_analyzed": sum(
            1 for r in owned if r.get("result_retrieved")),
        "by_backend": {r["backend"]: {"job_id": r["job_id"], "status": r["status"],
                                      "measurements_retrieved": r.get("result_retrieved", False)}
                       for r in owned},
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--inspect", action="store_true")
    ap.add_argument("--submit-h1", action="store_true")
    ap.add_argument("--backends", default="ibm_fez,ibm_marrakesh")
    a = ap.parse_args()

    reg = _load()
    if a.inspect:
        b = inspect_backends()
        reg["backend_inspection"] = {
            "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "backends": b}
        _save(reg)
        print(json.dumps(b, indent=2, default=str))

    if a.submit_h1:
        reg = submit_h1([x.strip() for x in a.backends.split(",") if x.strip()])

    _save(reg)
    print("\n=== VAHAANBANDHU HARDWARE TOTALS (owned jobs only) ===")
    print(json.dumps(summarise(reg), indent=2, default=str))


if __name__ == "__main__":
    main()
