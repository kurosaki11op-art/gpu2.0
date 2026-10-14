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


class OnlineConcepts:
    """Concept cells with exact counters (16-bit on-counts per bit + a use count per cell), learned in ONE pass, as a
    streaming chip must: each example is matched against its class's cells and the best one counts it. Match =
    log-likelihood from the counts (simulated in float; on chip a log table indexed by a normalised count ratio).
    A new cell is opened when the best match is worse than `open_at` per active bit (novelty), until P cells exist.
    Meant for the slow dream store (PSRAM on the Tang Nano), read only during sleep."""

    def __init__(self, n_bits, n_cls, P=8, alpha=0.5, seed=0):
        self.P, self.alpha = P, alpha
        self.on = np.zeros((n_cls, P, n_bits), np.int32); self.n = np.zeros((n_cls, P), np.int32)
        self.rng = np.random.RandomState(seed)
        self.dl = np.zeros(self.on.shape, np.float32); self.b0 = np.zeros((n_cls, P), np.float32)   # cached logs

    def _refresh(self, c, j):
        p = (self.on[c, j] + self.alpha) / (self.n[c, j] + 2 * self.alpha)
        self.dl[c, j] = np.log(p) - np.log1p(-p); self.b0[c, j] = np.log1p(-p).sum()

    def _ll(self, c, x):
        used = np.where(self.n[c] > 0)[0]
        return self.dl[c][used] @ x.astype(np.float32) + self.b0[c][used], used

    def learn(self, code, y):
        for c in np.unique(y):
            for x in code[y == c]:
                if self.n[c, 0] == 0:
                    j = 0
                else:
                    ll, ids = self._ll(c, x); j = ids[ll.argmax()]
                    free = np.where(self.n[c] == 0)[0]
                    if len(free) and self.rng.random_sample() < 1.0 / (1 + self.n[c].sum() / (50 * len(ids))):
                        j = free[0]                                          # open a new cell early in learning
                self.on[c, j] += x; self.n[c, j] += 1; self._refresh(c, j)
        return self

    def dreams(self, classes, n, seed=0):
        g = np.random.RandomState(seed); X, Y = [], []
        for c in classes:
            used = np.where(self.n[c] > 0)[0]; w = self.n[c][used] / self.n[c][used].sum()
            cell = used[g.choice(len(used), n, p=w)]
            p = (self.on[c] + self.alpha) / (self.n[c][:, None] + 2 * self.alpha)
            X.append(g.random_sample((n, self.on.shape[2])) < p[cell]); Y.append(np.full(n, c))
        return np.concatenate(X), np.concatenate(Y)

    def bits(self):
        return self.on.size * 16


class ScaledCounts:
    """Per-class exact counters with synaptic scaling: on-counts per bit and an example count per class, each B bits.
    When a class's example count reaches 2^B - 1, all its counts are halved (rates kept, memory bounded). Learning is
    counting plus an occasional right shift. Dreams: bit on with probability on/n (random number + compare)."""

    def __init__(self, n_bits, n_cls, B=12):
        self.B, self.top = B, (1 << B) - 1
        self.on = np.zeros((n_cls, n_bits), np.int64); self.n = np.zeros(n_cls, np.int64)

    def learn(self, code, y, chunk=256):
        for c in np.unique(y):
            X = code[y == c]
            for i in range(0, len(X), chunk):                                 # count a chunk, halve when full
                part = X[i:i + chunk]
                while len(part):
                    room = self.top - self.n[c]
                    take = part[:room]; part = part[room:]
                    self.on[c] += take.sum(0); self.n[c] += len(take)
                    if self.n[c] >= self.top:
                        self.on[c] >>= 1; self.n[c] >>= 1
        return self

    def dreams(self, classes, n, seed=0):
        g = np.random.RandomState(seed); X, Y = [], []
        for c in classes:
            p = (self.on[c] + 0.5) / (self.n[c] + 1.0)
            X.append(g.random_sample((n, self.on.shape[1])) < p); Y.append(np.full(n, c))
        return np.concatenate(X), np.concatenate(Y)

    def merge(self, other):
        m = ScaledCounts(self.on.shape[1], self.on.shape[0], self.B); m.on = self.on + other.on; m.n = self.n + other.n
        while (m.n >= m.top).any():
            full = m.n >= m.top; m.on[full] >>= 1; m.n[full] >>= 1
        return m

    def bits(self):
        return self.on.size * self.B + self.n.size * self.B
