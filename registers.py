import numpy as np
import random
from Gate_Defs import X, Y, Z, I

ERROR_OPTIONS = [X, Y, Z, I]

class qReg:
  def __init__(self, num, errorProb=0):
    self.state = np.zeros((2**num, 1), dtype=int)
    self.state[0][0] = 1
    self.num = num
    self.errorProb = errorProb
    self.probs = [self.errorProb/3, self.errorProb/3, self.errorProb/3, 1 - self.errorProb]

  def errorTick(self):
    gates = [random.choices(ERROR_OPTIONS, weights=self.probs, k=1)[0] for _ in range(self.num)]

    full_gate = gates[0]
    for g in gates[1:]:
      full_gate = np.kron(full_gate, g)

    self.state = full_gate @ self.state