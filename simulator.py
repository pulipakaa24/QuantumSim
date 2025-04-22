import numpy as np
from registers import qReg
from Gate_Defs import *

# Gate mappings (lowercase to match QASM)
GATE_MAP = {
    'x': X, 'y': Y, 'z': Z, 'h': H,
    's': S, 't': T, 'sdg': SDG, 'tdg': TDG
}

TWO_QUBIT_GATES = {
    'cx': CX, 'cz': CZ, 'cy': CY, 'ch': CH
}


def parse_qasm(qasm_code):
    """c
    Parse QASM into:
      metadata: list of include/OpenQASM lines
      qregs:    dict name->size
      cregs:    dict name->size
      operations: list of dicts, each one is either
         - a gate:     {'gate':'h','qubits':[1]}
         - a measure:  {'gate':'measure', 'qubit':2, 'creg':'c','cbit':1}
         - a cond‑op:  {'gate':'if','creg':'c','value':1,
                        'inner':{'gate':'x','qubits':[0]}}
    """
    lines = [ln.strip().rstrip(';') for ln in qasm_code.splitlines() if ln.strip()]
    metadata, qregs, cregs, ops = [], {}, {}, []

    for line in lines:
        if line.startswith(('OPENQASM', 'include')):
            metadata.append(line)

        elif line.startswith('qreg'):
            name, size = line[len('qreg'):].strip().split('[')
            qregs[name] = int(size.rstrip(']'))

        elif line.startswith('creg'):
            name, size = line[len('creg'):].strip().split('[')
            cregs[name] = int(size.rstrip(']'))

        else:
            parts = line.split()
            head = parts[0]

            # conditional if (c==v) op
            if head == 'if':
                cond = parts[1].strip('()')   # e.g. "c==1"
                creg_name, val = cond.split('==')
                val = int(val)
                inner_line = ' '.join(parts[2:])
                inner = _parse_one_op(inner_line)
                ops.append({
                    'gate': 'if',
                    'creg': creg_name,
                    'value': val,
                    'inner': inner
                })
            # measurement
            elif head == 'measure':
                _, src, _, dst = parts
                q_name, q_idx = src.split('['); q_idx = int(q_idx.rstrip(']'))
                c_name, c_idx = dst.split('['); c_idx = int(c_idx.rstrip(']'))
                ops.append({
                    'gate': 'measure',
                    'qubit': q_idx,
                    'creg': c_name,
                    'cbit': c_idx
                })
            # normal gates
            else:
                ops.append(_parse_one_op(line))

    return {
        'metadata':   metadata,
        'qregs':      qregs,
        'cregs':      cregs,
        'operations': ops
    }


def _parse_one_op(op_line):
    """Helper to parse a single gate line like 'cx q[1], q[0]'."""
    parts = op_line.split()
    gate = parts[0]
    tokens = [t.strip() for t in ' '.join(parts[1:]).split(',') if t.strip()]
    idxs = []
    for tok in tokens:
        if '[' in tok:
            _, num = tok.split('[')
            idxs.append(int(num.rstrip(']')))
        else:
            idxs.append(int(tok))
    return {'gate': gate, 'qubits': idxs}


def apply_gate(qreg, gate, qubits):
    """Apply single- or two-qubit gates."""
    if gate in GATE_MAP:
        qreg.state = apply_single_qubit_gate(GATE_MAP[gate], qubits[0], qreg)
    elif gate in TWO_QUBIT_GATES:
        qreg.state = apply_two_qubit_gate(TWO_QUBIT_GATES[gate], qubits[0], qubits[1], qreg)


def simulate(qasm_code, shots=1024, error=0):
    parsed = parse_qasm(qasm_code)
    qreg   = qReg(parsed['qregs']['q'], error)
    # initialize classical registers
    creg   = {name: [0]*size for name,size in parsed['cregs'].items()}

    for op in parsed['operations']:
        if op['gate'] == 'if':
            # only checking c[0] for simplicity
            if creg[op['creg']][0] == op['value']:
                inner = op['inner']
                apply_gate(qreg, inner['gate'], inner['qubits'])

        elif op['gate'] == 'measure':
            bit = qreg.measure(op['qubit'])
            creg[op['creg']][op['cbit']] = bit

        else:
            apply_gate(qreg, op['gate'], op.get('qubits', []))

    # final statevector + histogram
    statevec = qreg.get_ibm_statevector()
    counts   = qreg.measure_all(shots)
    # reformat counts into IBM bit-order
    ibm_counts = {k[::-1]: v for k,v in counts.items()}
    return statevec, ibm_counts

if __name__ == '__main__':
    with open('input.qasm', 'r') as file:
        qasm_code = file.read()

    shots = 1024
    error = 0.01

    state_vector, counts = simulate(qasm_code, shots, error)

    # Display the results
    print("State Vector:")
    print(state_vector)
    print("\nMeasurement Counts:")
    for outcome, count in sorted(counts.items()):
        print(f"{outcome}: {count}")