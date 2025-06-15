import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit.providers.basic_provider import BasicSimulator


def quantum_delay_prediction(traffic_ratios, trained_thetas=None, max_delay=30.0):
    num_qubits = min(5, len(traffic_ratios))
    qc = QuantumCircuit(num_qubits, num_qubits)

    for i, ratio in enumerate(traffic_ratios[:num_qubits]):
        theta = float(ratio) * np.pi
        qc.ry(theta, i)

    if trained_thetas is None:
        trained_thetas = [0.0] * num_qubits
    for i in range(num_qubits):
        qc.rx(trained_thetas[i], i)

    qc.measure(range(num_qubits), range(num_qubits))

    simulator = BasicSimulator()
    compiled = transpile(qc, simulator)
    job = simulator.run(compiled)
    result = job.result()
    counts = result.get_counts(qc)

    total_shots = sum(counts.values())
    exp_z = 0.0
    for bitstring, count in counts.items():
        bit0 = int(bitstring[::-1][0])
        z_val = 1 if bit0 == 0 else -1
        exp_z += z_val * count
    exp_z /= total_shots

    estimated_delay = (1 - exp_z) / 2 * max_delay
    return estimated_delay