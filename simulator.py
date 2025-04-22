import numpy as np
from registers import qReg
from Gate_Defs import *

GATE_MAP = {
    'x':       X,
    'y':       Y,
    'z':       Z,
    'h':       H,
    's':       S,
    't':       T,
    'sdg':     SDG,
    'tdg':     TDG,
    'rx':      RX,       
    'ry':      RY,       
    'rz':      RZ,       
    'u':       U,       

}
TWO_QUBIT_GATES = {
    'cx': CX,
    'cz': CZ,
    'cy': CY,
    'ch': CH
}


def parse_qasm(qasm_code):
    """
    Parse QASM into:
      metadata:   list of include/OpenQASM lines
      qregs:      dict name->size
      cregs:      dict name->size
      operations: list of dicts, each one is either
         - {'gate':'h',   'qubits':[1]}
         - {'gate':'measure','qubit':2,'creg':'c','cbit':1}
         - {'gate':'if',  'creg':'c','value':1,'inner':{...}}
         - parameterized: {'gate':'rx','params':[θ],'qubits':[0]}
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
            head = parts[0].lower()

            if head == 'if':
                # reconstruct condition and inner op
                cond_expr = ' '.join(parts[1:])
                cond_part, rest = cond_expr.split(')', 1)
                cond = cond_part.strip('()').replace(' ', '')
                creg_name, val = cond.split('==')
                val = int(val)
                inner = _parse_one_op(rest.strip())
                ops.append({
                    'gate':   'if',
                    'creg':   creg_name,
                    'value':  val,
                    'inner':  inner
                })

            elif head == 'measure':
                _, src, _, dst = parts
                _, q_idx = src.split('[');  q_idx = int(q_idx.rstrip(']'))
                _, c_idx = dst.split('[');  c_idx = int(c_idx.rstrip(']'))
                ops.append({
                    'gate':   'measure',
                    'qubit':  q_idx,
                    'creg':   parts[-1].split('[')[0],
                    'cbit':   c_idx
                })

            else:
                ops.append(_parse_one_op(line))

    return {
        'metadata':   metadata,
        'qregs':      qregs,
        'cregs':      cregs,
        'operations': ops
    }


def _parse_one_op(op_line):
    """
    Parse a single operation line, supporting:
      - 'cx q[1], q[0]'
      - 'rx(pi/2) q[0]'
      - 'u(theta,phi,lam) q[1]'
    Returns {'gate': name, 'params': [...], 'qubits': [...]}
    """
    s = op_line.strip()
    params = []

    if '(' in s:
        i1 = s.find('(')
        i2 = s.find(')', i1)
        gate = s[:i1].lower().strip()
        param_str = s[i1+1:i2]
        raw = [p.strip() for p in param_str.split(',')]
        params = [float(eval(p, {"pi": np.pi, "np": np})) for p in raw if p]
        remainder = s[i2+1:].strip()
    else:
        gate = s.split()[0].lower()
        remainder = s[len(gate):].strip()

    # parse qubit indices
    idxs = []
    for tok in [t.strip() for t in remainder.split(',') if t.strip()]:
        if '[' in tok:
            _, num = tok.split('[')
            idxs.append(int(num.rstrip(']')))
        else:
            try:
                idxs.append(int(tok))
            except ValueError:
                pass

    return {'gate': gate, 'params': params, 'qubits': idxs}


def apply_gate(qreg, gate, qubits, params=None):
    """
    Dispatch single‑ and two‑qubit gates:
      • Fixed matrices in GATE_MAP (X, H, …)
      • Callable constructors in GATE_MAP (RX, RZ, U, etc.)
      • Two‑qubit gates in TWO_QUBIT_GATES (CX, CZ, CY, CH)
    """
    params = params or []

    if gate in GATE_MAP:
        entry = GATE_MAP[gate]
        mat = entry(*params) if callable(entry) else entry
        qreg.state = apply_single_qubit_gate(mat, qubits[0], qreg)

    elif gate in TWO_QUBIT_GATES:
        mat = TWO_QUBIT_GATES[gate]
        qreg.state = apply_two_qubit_gate(mat, qubits[0], qubits[1], qreg)

    else:
        raise ValueError(f"Unknown gate: {gate}")


def simulate(qasm_code, shots=1024, error=0):
    parsed = parse_qasm(qasm_code)
    qreg   = qReg(parsed['qregs']['q'], error)
    cregs  = {name: 0 for name in parsed['cregs']}

    for op in parsed['operations']:
        if op['gate'] == 'if':
            if cregs[op['creg']] == op['value']:
                inner = op['inner']
                apply_gate(qreg, inner['gate'], inner['qubits'], inner.get('params', []))

        elif op['gate'] == 'measure':
            bit = qreg.measure(op['qubit'])
            cregs[op['creg']] |= (bit << op['cbit'])

        else:
            apply_gate(qreg, op['gate'], op.get('qubits', []), op.get('params', []))

    statevec = qreg.get_ibm_statevector()
    counts   = qreg.measure_all(shots)
    ibm_counts = {k[::-1]: v for k, v in counts.items()}
    return statevec, ibm_counts


if __name__ == '__main__':
    with open('input.qasm', 'r') as file:
        qasm_code = file.read()

    shots = 1024
    error = 0.01
    state_vector, counts = simulate(qasm_code, shots, error)

    print("State Vector:")
    print(state_vector)
    print("\nMeasurement Counts:")
    for outcome, count in sorted(counts.items()):
        print(f"{outcome}: {count}")
