"""Chip-honest dream memories: firing rates stored in a few bits, learned online with stochastic rounding.

RateMemory     : per class, per code bit, a B-bit firing rate r (0 .. 2^B-1). For every example of class c:
                 r += (target - r) >> k, target = 2^B-1 if the bit fired else 0, with the shifted-out remainder
                 rounded up with probability remainder / 2^k (a random draw + compare, like a stochastic synapse).
                 Dreams of class c: bit on when a random B-bit number is below r.
Integer arithmetic throughout (numpy int arrays), so this is the reference the RTL must match."""
import numpy as np


class RateMemory:
    def __init__(self, n_bits, n_cls, B=8, k=6, seed=0, kmax=None):
        self.B, self.k, self.top, self.kmax = B, k, (1 << B) - 1, kmax
        self.r = np.zeros((n_cls, n_bits), np.int32); self.seen = np.zeros(n_cls, np.int64)
        self.rng = np.random.RandomState(seed)

    def _step(self, r, x, seen=None):
        """r: (n_bits,) int, x: (n_bits,) bool -> new r. With kmax set (metaplasticity), the shift grows with
        experience: k = min(bit length of the class's example count, kmax), so early examples move the rate a lot
        and later ones a little (a running average up to ~2^kmax examples)."""
        k = self.k if self.kmax is None else min(int(seen).bit_length(), self.kmax)
        d = np.where(x, self.top, 0) - r
        q, rem = d >> k, d & ((1 << k) - 1)                                 # floor shift and its remainder
        up = self.rng.randint(0, 1 << k, size=r.shape) < rem                 # stochastic rounding
        return np.clip(r + q + up, 0, self.top)

    def learn(self, code, y):
        for c in np.unique(y):
            for x in code[y == c]:
                if self.seen[c] == 0:
                    self.r[c] = np.where(x, self.top, 0)                       # first example sets the rates
                else:
                    self.r[c] = self._step(self.r[c], x, self.seen[c] + 1)
                self.seen[c] += 1
        return self

    def dreams(self, classes, n, seed=0):
        g = np.random.RandomState(seed); X, Y = [], []
        for c in classes:
            X.append(g.randint(0, self.top + 1, size=(n, self.r.shape[1])) < self.r[c]); Y.append(np.full(n, c))
        return np.concatenate(X), np.concatenate(Y)

    def bits(self):
        return self.r.size * self.B


class ConceptRates:
    """P concept cells per class, each a vector of B-bit firing rates learned with the metaplastic rule of RateMemory
    (each cell has its own experience count). An example of class c trains the cell of class c that matches it best.
    Match = sum over bits of a small integer table: LUT1[r] if the bit fired, LUT0[r] if not (log-likelihood in
    1/8 units, precomputed), i.e. lookups and adds only. Cells start from the first P examples of the class."""

    def __init__(self, n_bits, n_cls, P=4, B=4, kmax=9, seed=0, soft=False):
        self.P, self.B, self.top, self.kmax, self.soft = P, B, (1 << B) - 1, kmax, soft
        self.r = np.zeros((n_cls, P, n_bits), np.int32); self.seen = np.zeros((n_cls, P), np.int64)
        self.rng = np.random.RandomState(seed)
        p = (np.arange(self.top + 1) + 0.5) / (self.top + 1)
        self.L1 = np.round(8 * np.log(p)).astype(np.int32); self.L0 = np.round(8 * np.log1p(-p)).astype(np.int32)

    def match(self, x, c):
        r = self.r[c]                                                        # (P, n_bits)
        return np.where(x[None], self.L1[r], self.L0[r]).sum(1)

    def learn(self, code, y):
        for c in np.unique(y):
            for x in code[y == c]:
                empty = np.where(self.seen[c] == 0)[0]
                if len(empty):
                    j = empty[0]; self.seen[c, j] = 1
                    # soft imprint: a new cell starts at 3/4 or 1/4 of full rate, not all-or-nothing
                    self.r[c, j] = np.where(x, 3 * self.top // 4, self.top // 4) if self.soft else np.where(x, self.top, 0)
                    continue
                j = int(self.match(x, c).argmax())
                k = min(int(self.seen[c, j] + 1).bit_length(), self.kmax)
                d = np.where(x, self.top, 0) - self.r[c, j]
                up = self.rng.randint(0, 1 << k, size=d.shape) < (d & ((1 << k) - 1))
                self.r[c, j] = np.clip(self.r[c, j] + (d >> k) + up, 0, self.top); self.seen[c, j] += 1
        return self

    def dreams(self, classes, n, seed=0):
        g = np.random.RandomState(seed); X, Y = [], []
        for c in classes:
            w = self.seen[c] / self.seen[c].sum(); cell = g.choice(self.P, n, p=w)
            X.append(g.randint(0, self.top + 1, size=(n, self.r.shape[2])) < self.r[c][cell]); Y.append(np.full(n, c))
        return np.concatenate(X), np.concatenate(Y)

    def bits(self):
        return self.r.size * self.B
