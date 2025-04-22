from registers import qReg
from Gate_Defs import *
from tkinter import *
from tkinter import filedialog
import os
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

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
    # initialize classical registers
    cregs = {name: 0 for name in parsed['cregs']}

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

        qreg.error_tick()

    statevec = qreg.get_ibm_statevector()
    counts   = qreg.measure_all(shots)
    ibm_counts = {k[::-1]: v for k, v in counts.items()}
    return statevec, ibm_counts


def only_numeric(new_val):
    return new_val.isdigit() or new_val == ""

def only_float(val):
    if val == "":
        return True  # allow clearing the entry
    try:
        float(val)
        return True
    except ValueError:
        return False

filePath = None

def getFile():
    global filePath
    filePath = filedialog.askopenfilename(title="Select a QASM file")
    if filePath:
        name, ext = os.path.splitext(filePath)
        if ext != ".qasm":
            print("Invalid File")
            filePath = None

            
def update_graph(counts_dict):
    ax.clear()
    ax.set_title("Results")
    ax.set_xlabel("States")
    ax.set_ylabel("Counts")
    labels = list(counts_dict.keys())
    values = list(counts_dict.values())
    ax.bar(labels, values)
    fig.tight_layout()
    canvas.draw()

def update_statevec(labels, mags, colors):
    ax1.clear()
    ax1.bar(list(labels), list(mags), color=colors)
    ax1.set_ylabel("Magnitude")
    ax1.set_xlabel("States")
    ax1.set_title("Statevector")
    fig1.tight_layout()
    canvas1.draw()

def sim():
  with open(filePath, 'r') as file:
        qasm_code = file.read()
  
  passingShots = shots.get()
  passingError = errRate.get()
  stateVec, cts = simulate(qasm_code, passingShots, passingError)

  num_qubits = int(np.log2(len(stateVec)))
  labels = [format(i, f'0{num_qubits}b') for i in range(len(stateVec))]

  mags = np.abs(stateVec)
  phases = np.angle(stateVec)
  norm_phases = (phases + np.pi) / (2 * np.pi)

  import matplotlib.colors as mcolors
  colors = [mcolors.hsv_to_rgb((hue, 1, 1)) for hue in norm_phases]

  update_statevec(labels, mags, colors)


  update_graph(dict(sorted(cts.items())))


root = Tk()
root.title("Quantum Simulator GUI")

vcmd = (root.register(only_numeric), '%S')
vcmdFlt = (root.register(only_float), '%P')
Label(root, text="Shots:").grid(row=0, column=3)
shots = IntVar()
entry = Entry(root, validate='key', validatecommand=vcmd, textvariable=shots)
entry.grid(row=1, column=3)
Label(root, text="Error Rate:").grid(row=2, column=3)
errRate = DoubleVar()
entry = Entry(root, validate='key', validatecommand=vcmdFlt, textvariable=errRate)
entry.grid(row=3, column=3)


fileButton = Button(root, text="Select QASM", width=10, command=getFile)
fileButton.grid(row=4, column=3)

startButton = Button(root, text="Run Simulation", width=10, command=sim)
startButton.grid(row=5, column=3)


# Create the figure and axes
fig, ax = plt.subplots(figsize=(4, 2))
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().grid(row=0, column=0, rowspan=10, columnspan=2)  # left side of window
ax.set_title("Results")
ax.set_xlabel("States")
ax.set_ylabel("Counts")
ax.bar([0, 1], [0, 0])
fig.tight_layout()

fig1, ax1 = plt.subplots(figsize=(4, 2))
canvas1 = FigureCanvasTkAgg(fig1, master=root)
canvas1.get_tk_widget().grid(row=10, column=0, rowspan=10, columnspan=2)
ax1.bar([0,1], [0,0])
ax1.set_ylabel("Magnitude")
ax1.set_xlabel("States")
ax1.set_title("Statevector")
fig1.tight_layout()

if __name__ == '__main__':
    root.mainloop()