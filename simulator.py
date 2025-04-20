
from registers import qReg
def parse_qasm(qasm_code):
    lines = qasm_code.strip().splitlines()
    quantum_registers = {}
    classical_registers = {}
    operations = []
    metadata = []

    for line in lines:
        line = line.strip()
        if not line or line.startswith('//'):
            continue
        elif line.startswith("OPENQASM") or line.startswith("include"):
            metadata.append(line)
        elif line.startswith("qreg"):
            name, size = line[5:].strip(" ;").split('[')
            size = int(size.strip(']'))
            quantum_registers[name.strip()] = size
        elif line.startswith("creg"):
            name, size = line[5:].strip(" ;").split('[')
            size = int(size.strip(']'))
            classical_registers[name.strip()] = size
        else:
            operations.append(line)

    return {
        "metadata": metadata,
        "quantum_registers": quantum_registers,
        "classical_registers": classical_registers,
        "operations": operations
    }
def parse_operations(operations):
    parsed_ops = []

    for line in operations:
        line = line.strip().rstrip(";")
        op = {}

        if line.startswith("if"):
            start = line.find('(')
            end = line.find(')')
            condition = line[start + 1:end].strip()

            cond_parts = condition.split("==")
            reg = cond_parts[0].strip()
            val = int(cond_parts[1].strip())
            op["condition"] = {"creg": reg, "val": val}

           
            rest = line[end + 1:].strip()
        else:
            rest = line.strip()
        if " " in rest:
            gate, args = rest.split(" ", 1)
            qubit_strs = [q.strip() for q in args.split(',')]
            qubits = [int(q[q.find('[')+1:q.find(']')]) for q in qubit_strs]
        else:
            gate = rest
            qubits = []

        op["gate"] = gate
        op["qubits"] = qubits
        parsed_ops.append(op)

    return parsed_ops
sample_qasm = """
OPENQASM 2.0;
include "qelib1.inc";

qreg q[2];
creg c[2];
if (c == 0) ch q[1], q[0];
x q[1];
cx q[0], q[1];

"""

data = parse_qasm(sample_qasm)
q = qReg(data["quantum_registers"]['q'])
operate = parse_operations(data["operations"])

for op in operate:
    print(op)
#def simulate(shots):
    