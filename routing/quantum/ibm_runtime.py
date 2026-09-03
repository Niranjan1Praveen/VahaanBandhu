"""IBM Quantum hardware access, for the offline research stage only.

Architectural rule, enforced by design rather than convention: this module is
never imported by the live request path. Hardware queue times are measured in
minutes to hours; a farmer asking for a truck cannot wait on a QPU queue, and
building the product that way would be indefensible regardless of how good the
results were.

What hardware runs are *for* is producing reusable artifacts -- validated QAOA
parameters, benchmark reference solutions, feasibility statistics for a problem
family -- which the fast classical online layer then consumes.

Credentials come from the environment. If none are configured, ``available``
is False and callers must record the hardware experiment as blocked rather
than substituting a simulator result and labelling it hardware.
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass

log = logging.getLogger(__name__)


@dataclass
class BackendInfo:
    name: str
    n_qubits: int
    simulator: bool
    pending_jobs: int | None = None
    operational: bool | None = None


class IBMQuantumRunner:
    """Thin wrapper over qiskit-ibm-runtime with explicit availability checks."""

    def __init__(self, token: str | None = None, channel: str | None = None) -> None:
        self.token = token or os.environ.get("IBM_QUANTUM_TOKEN", "")
        self.channel = channel or os.environ.get("IBM_QUANTUM_CHANNEL", "ibm_cloud")
        self._service = None
        self._error: str | None = None

    @property
    def available(self) -> bool:
        return bool(self.token) and self.service is not None

    @property
    def service(self):
        """Lazily connect. A failure is recorded, never raised at import time."""
        if self._service is not None or self._error is not None:
            return self._service
        if not self.token:
            self._error = "IBM_QUANTUM_TOKEN is not set"
            return None
        try:
            from qiskit_ibm_runtime import QiskitRuntimeService
            self._service = QiskitRuntimeService(channel=self.channel, token=self.token)
        except Exception as e:  # network, auth, or package issues
            self._error = f"{type(e).__name__}: {e}"
            log.warning("IBM Quantum unavailable -- %s", self._error)
        return self._service

    @property
    def status(self) -> dict:
        """Report used verbatim in the QA/experiment record."""
        return {
            "token_configured": bool(self.token),
            "channel": self.channel,
            "connected": self._service is not None,
            "error": self._error,
        }

    def list_backends(self, min_qubits: int = 5) -> list[BackendInfo]:
        if not self.available:
            return []
        out = []
        for b in self.service.backends(min_num_qubits=min_qubits, operational=True):
            try:
                st = b.status()
                out.append(BackendInfo(b.name, b.num_qubits, b.simulator,
                                       st.pending_jobs, st.operational))
            except Exception:
                out.append(BackendInfo(b.name, b.num_qubits, b.simulator))
        return out

    def least_busy(self, min_qubits: int = 5):
        if not self.available:
            return None
        try:
            return self.service.least_busy(operational=True, simulator=False,
                                           min_num_qubits=min_qubits)
        except Exception as e:
            log.warning("least_busy failed: %s", e)
            return None

    def run_circuit(self, circuit, shots: int = 1024, backend=None) -> dict:
        """Submit one circuit and return counts plus execution provenance.

        Returns a dict with ``executed=False`` and a reason when hardware is
        unavailable. Callers must propagate that into their results rather than
        falling back silently -- a simulator result labelled as hardware is a
        fabricated experimental claim.
        """
        if not self.available:
            return {"executed": False, "reason": self._error or "no credentials",
                    "counts": None, "backend": None}

        backend = backend or self.least_busy(min_qubits=circuit.num_qubits)
        if backend is None:
            return {"executed": False, "reason": "no operational backend available",
                    "counts": None, "backend": None}

        try:
            from qiskit import transpile
            from qiskit_ibm_runtime import SamplerV2

            t0 = time.time()
            isa = transpile(circuit, backend=backend, optimization_level=3)
            sampler = SamplerV2(mode=backend)
            job = sampler.run([isa], shots=shots)
            result = job.result()
            counts = result[0].data.c.get_counts()
            return {
                "executed": True,
                "counts": counts,
                "backend": backend.name,
                "job_id": job.job_id(),
                "shots": shots,
                "transpiled_depth": isa.depth(),
                "transpiled_n_qubits": isa.num_qubits,
                "logical_depth": circuit.depth(),
                "wall_clock_s": round(time.time() - t0, 2),
            }
        except Exception as e:
            log.error("hardware execution failed: %s", e)
            return {"executed": False, "reason": f"{type(e).__name__}: {e}",
                    "counts": None, "backend": getattr(backend, "name", None)}
