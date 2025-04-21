import numpy as np
from registers import qReg
from Gate_Defs import *

# Gate mappings (lowercase to match QASM)
GATE_MAP = {
    'x': X,
    'y': Y,
    'z': Z,
    'h': H,
    's': S,
    't': T,
    'sdg': SDG,
    'tdg': TDG
}

TWO_QUBIT_GATES = {
    'cx': CX,
    'cz': CZ,
    'cy': CY,
    'ch': CH
}

def parse_qasm(qasm_code):
    """Parse QASM code into quantum circuit"""
    lines = [line.strip() for line in qasm_code.splitlines() if line.strip()]
    metadata = []
    qregs = {}
    cregs = {}
    operations = []

    for line in lines:
        if line.startswith(('OPENQASM', 'include')):
            metadata.append(line)
        elif line.startswith('qreg'):
            name, size = line[4:].strip().rstrip(';').split('[')
            qregs[name.strip()] = int(size.rstrip(']'))
        elif line.startswith('creg'):
            name, size = line[4:].strip().rstrip(';').split('[')
            cregs[name.strip()] = int(size.rstrip(']'))
        else:
            operations.append(line)

    return {
        'metadata': metadata,
        'qregs': qregs,
        'cregs': cregs,
        'operations': operations
    }

def parse_operation(op_line):
    """Parse a single QASM operation"""
    op_line = op_line.rstrip(';')
    parts = op_line.split()
    
    if len(parts) == 1:
        return {'gate': parts[0], 'qubits': []}
    
    gate = parts[0]
    qubits = [q.strip() for q in ' '.join(parts[1:]).split(',')]
    
    # Extract qubit indices
    qubit_indices = []
    for q in qubits:
        if '[' in q:
            name, idx = q.split('[')
            qubit_indices.append(int(idx.rstrip(']')))
        else:
            qubit_indices.append(int(q))
    
    return {'gate': gate, 'qubits': qubit_indices}

def apply_gate(qreg, gate, qubits):
    """Apply gate to quantum register"""
    if gate in GATE_MAP:
        target = qubits[0]
        qreg.state = apply_single_qubit_gate(GATE_MAP[gate], target, qreg)
    elif gate in TWO_QUBIT_GATES:
        control, target = qubits
        qreg.state = apply_two_qubit_gate(TWO_QUBIT_GATES[gate], control, target, qreg)

def simulate(qasm_code, shots=1024):
    parsed = parse_qasm(qasm_code)
    qreg = qReg(parsed['qregs']['q'])
    
    for op_line in parsed['operations']:
        op = parse_operation(op_line)
        apply_gate(qreg, op['gate'], op['qubits'])
    
    # Get counts in IBM order
    counts = qreg.measure_all(shots)
    ibm_counts = {}
    for bits, count in counts.items():
        reversed_bits = bits[::-1] 
        ibm_counts[reversed_bits] = ibm_counts.get(reversed_bits, 0) + count
    
    return qreg.get_ibm_statevector(), ibm_counts

if __name__ == '__main__':
    sample_qasm = """
    OPENQASM 2.0;
    include "qelib1.inc";
    qreg q[3];
    creg c[2];
    h q[1];
    x q[2];
    cx q[1], q[0];
    h q[1];
    """
    
    state_vector, counts = simulate(sample_qasm)
    print("State Vector:")
    print(state_vector)
    print("\nMeasurement Counts:")
    for outcome, count in sorted(counts.items()):
        print(f"{outcome}: {count}")