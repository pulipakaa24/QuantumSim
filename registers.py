import numpy as np
import random
from Gate_Defs import X, Y, Z, I

ERROR_OPTIONS = [X, Y, Z, I]

class qReg:
    def __init__(self, num_qubits, error_prob=0):
        self.num = num_qubits
        self.state = np.zeros(2**num_qubits, dtype=complex)
        self.state[0] = 1 + 0j
        self.error_prob = error_prob
        self.error_weights = [error_prob/3, error_prob/3, error_prob/3, 1-error_prob]

    def error_tick(self):
        if self.error_prob <= 0:
            return
        error_gates = random.choices(ERROR_OPTIONS, weights=self.error_weights, k=self.num)
        full_error = error_gates[0]
        for g in error_gates[1:]:
            full_error = np.kron(full_error, g)
        self.state = full_error @ self.state

    def get_ibm_statevector(self):
        n = self.num
        ibm_state = np.zeros(2**n, dtype=complex)
        for i in range(2**n):
            bits = format(i, f'0{n}b')[::-1]
            ibm_state[int(bits,2)] = self.state[i]
        return ibm_state

    def measure_all(self, shots=1):
        probs = np.abs(self.state)**2
        outcomes = np.random.choice(len(probs), size=shots, p=probs)
        return {format(o, f'0{self.num}b'): np.count_nonzero(outcomes==o) for o in outcomes}

    def measure(self, target):
        """
        Measure a single qubit at index `target`, collapse state, and return 0 or 1.
        """
        # compute marginal probabilities
        zero_inds = []
        one_inds = []
        for idx in range(len(self.state)):
            bit = (idx >> target) & 1
            (one_inds if bit else zero_inds).append(idx)
        p0 = np.sum(np.abs(self.state[zero_inds])**2)
        result = np.random.rand() >= p0
        # collapse
        keep = one_inds if result else zero_inds
        new_state = np.zeros_like(self.state)
        new_state[keep] = self.state[keep]
        # renormalize
        if np.sum(np.abs(new_state)**2) > 0:
            new_state /= np.linalg.norm(new_state)
        self.state = new_state
        return int(result)