import numpy as np
from math import pi, cos, sin, sqrt


CX = np.array([[1,0,0,0],
               [0,1,0,0],
               [0,0,0,1],
               [0,0,1,0]])

CZ = np.array([[1,0,0,0],
               [0,1,0,0],
               [0,0,1,0],
               [0,0,0,-1]])

CY = np.array([[1,0,0,0],
               [0,0,0,-1j],
               [0,0,1,0],
               [0,1j,0,0]])

CH = np.array([[sqrt(2),0,0,0],
               [0,1,0,1],
               [0,0,sqrt(2),0],
               [0,1,0,-1]]) / sqrt(2)

SWAP = np.array([[1,0,0,0],
                 [0,0,1,0],
                 [0,1,0,0],
                 [0,0,0,1]])

CCX = np.array([[1,0,0,0,0,0,0,0],
                [0,1,0,0,0,0,0,0],
                [0,0,1,0,0,0,0,0],
                [0,0,0,1,0,0,0,0],
                [0,0,0,0,1,0,0,0],
                [0,0,0,0,0,1,0,0],
                [0,0,0,0,0,0,0,1],
                [0,0,0,0,0,0,1,0]])

I = np.array([[1,0],
              [0,1]])

X = np.array([[0,1],
              [1,0]])

Y = np.array([[0,-1j],
              [1j,0]])

Z = np.array([[1,0],
              [0,-1]])

H = np.array([[1,1],
              [1,-1]]) / sqrt(2)

S = np.array([[1,0],
              [0,1j]])

T = np.array([[1, 0],
              [0, np.exp(1j*pi/4)]])

SDG = S.conj().T
TDG = T.conj().T

def reset(target):
  target.set(np.array([[0],[0]]))

def M(target, destination):
  probArray = np.abs(target) ** 2
  result = np.random.choice([0,1], p=probArray)
  destination.set(result)
  if (result): target.set(np.array([[0],[1]]))
  else: target.set(np.array([[1],[0]]))

def apply_single_qubit_gate(gate, qubitNum, qreg):
    """Applies a single-qubit gate to the given qubit in the full statevector."""
    #Creates identity matrices for each qubit
    # and applies the gate to the specified qubit
    # The state is represented as a vector of size 2^num_qubits
    gates = [np.eye(2, dtype=complex) for _ in range(qreg.num)]
    gates[qubitNum] = gate
    full_gate = gates[0]
    for g in gates[1:]:
        full_gate = np.kron(full_gate, g)
    return full_gate @ qreg.state