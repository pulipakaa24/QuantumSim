import numpy as np
import random
from Gate_Defs import X, Y, Z, I

ERROR_OPTIONS = [X, Y, Z, I]

class qReg:
    def __init__(self, num_qubits, error_prob=0):
        """
        Initialize quantum register in |0...0⟩ state (little-endian)
        q[0] is least significant bit (rightmost in bitstring)
        """
        self.num = num_qubits
        self.state = np.zeros(2**num_qubits, dtype=complex)
        self.state[0] = 1 + 0j  # Initialize to |0...0⟩
        self.error_prob = error_prob
        self.error_weights = [
            error_prob/3,  # X error
            error_prob/3,  # Y error
            error_prob/3,  # Z error
            1 - error_prob  # No error (I)
        ]

    def error_tick(self):
        """Apply random Pauli errors to each qubit with given probability"""
        if self.error_prob <= 0:
            return
        error_gates = [random.choices(ERROR_OPTIONS, weights=self.error_weights, k=1)[0] 
                     for _ in range(self.num)]
        full_error = error_gates[0]
        for gate in error_gates[1:]:
            full_error = np.kron(full_error, gate)

        self.state = full_error @ self.state
    def get_ibm_statevector(self):
        """Return state vector in IBM display order (q0 as MSB)"""
        n = self.num
        ibm_state = np.zeros(2**n, dtype=complex)
        
        for i in range(2**n):
            # Convert index to binary string
            bits = format(i, f'0{n}b')
            # Reverse the bit order for IBM display
            reversed_bits = bits[::-1]
            reversed_idx = int(reversed_bits, 2)
            ibm_state[reversed_idx] = self.state[i]
            
        return ibm_state
    
    def measure_all(self, shots=1):
        """Measure all qubits and return counts"""
        probs = np.abs(self.state)**2
        outcomes = np.random.choice(len(probs), size=shots, p=probs)
        counts = {format(outcome, f'0{self.num}b'): np.count_nonzero(outcomes == outcome) 
                 for outcome in outcomes}
        return counts