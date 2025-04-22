import numpy as np
from math import pi, sqrt

# Two-qubit gates
CX = np.array([[1,0,0,0],[0,1,0,0],[0,0,0,1],[0,0,1,0]])
CZ = np.array([[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,-1]])
CY = np.array([[1,0,0,0],[0,0,0,-1j],[0,0,1,0],[0,1j,0,0]])
CH = np.array([[sqrt(2),0,0,0],[0,1,0,1],[0,0,sqrt(2),0],[0,1,0,-1]])/sqrt(2)

# Single-qubit gates
I   = np.array([[1,0],[0,1]])
X   = np.array([[0,1],[1,0]])
Y   = np.array([[0,-1j],[1j,0]])
Z   = np.array([[1,0],[0,-1]])
H   = np.array([[1,1],[1,-1]])/sqrt(2)
S   = np.array([[1,0],[0,1j]])
T   = np.array([[1,0],[0,np.exp(1j*pi/4)]])
SDG = S.conj().T
TDG = T.conj().T

# Helpers

def reset(target):
    target.set(np.array([[0],[0]]))

def apply_single_qubit_gate(gate, target, qreg):
    ops = [I]*qreg.num
    ops[target] = gate
    full = ops[0]
    for op in ops[1:]: full = np.kron(full, op)
    return full @ qreg.state



def apply_two_qubit_gate(gate, ctrl, tgt, qreg):
    dim = 2**qreg.num
    new = np.zeros(dim, dtype=complex)
    for i in range(dim):
        bits = [(i >> (qreg.num - 1 - j)) & 1 for j in range(qreg.num)]
        amp  = qreg.state[i]
        if bits[ctrl] == 1:
            if np.array_equal(gate, CX):
                bits_copy = bits.copy()
                bits_copy[tgt] ^= 1
                j = sum(b << (qreg.num - 1 - k) for k, b in enumerate(bits_copy))
                new[j] += amp
            elif np.array_equal(gate, CZ):
                phase = -1 if bits[tgt] == 1 else 1
                new[i] += phase * amp
            elif np.array_equal(gate, CY):
                bits_copy = bits.copy()
                orig = bits[tgt]
                bits_copy[tgt] ^= 1
                j = sum(b << (qreg.num - 1 - k) for k, b in enumerate(bits_copy))
                factor =  1j if orig == 0 else -1j
                new[j] += factor * amp
            #splits amplitude
            elif np.array_equal(gate, CH):
                orig = bits[tgt]
                for val in (0, 1):
                    bits_copy = bits.copy()
                    bits_copy[tgt] = val
                    j = sum(b << (qreg.num - 1 - k) for k, b in enumerate(bits_copy))
                    if val == 0:
                        coef = 1/np.sqrt(2)
                    else:
                        coef = (1/np.sqrt(2)) * (1 if orig == 0 else -1)
                    new[j] += coef * amp
            else:
                new[i] += amp
        else:
            new[i] += amp

    return new