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

def apply_single_qubit_gate(gate, target, qreg):
    """Apply single-qubit gate to target qubit"""
    # Create full operator: I ⊗ ... ⊗ gate ⊗ ... ⊗ I
    operators = [I] * qreg.num
    operators[target] = gate
    
    # Build full matrix (little-endian order)
    full_op = operators[0]
    for op in operators[1:]:
        full_op = np.kron(full_op, op)
    
    return full_op @ qreg.state

def apply_two_qubit_gate(gate, control, target, qreg):
    """Apply two-qubit gate with control and target qubits (IBM-compatible)"""
    if control == target:
        raise ValueError("Control and target qubits must be different")
    
    dim = 2**qreg.num
    new_state = np.zeros(dim, dtype=complex)
    
    for basis_idx in range(dim):
        bits = [(basis_idx >> (qreg.num - 1 - i)) & 1 for i in range(qreg.num)]
        # Apply gate condition
        if bits[control] == 1:
            if np.array_equal(gate, CX):  # CNOT gate
                new_bits = bits.copy()
                new_bits[target] ^= 1  # Flip target bit
                # Convert back to index (IBM convention)
                new_idx = sum(bit << (qreg.num - 1 - i) for i, bit in enumerate(new_bits))
                new_state[new_idx] += qreg.state[basis_idx]
            elif np.array_equal(gate, CZ):  # CZ gate
                phase = -1 if bits[target] == 1 else 1
                new_state[basis_idx] += phase * qreg.state[basis_idx]
            
        else:
            new_state[basis_idx] += qreg.state[basis_idx]
    
    return new_state