"""Sensory layer that learns its own feature detectors, the way early visual cortex does: no labels, no gradients.

  * receptive fields : each detector looks at a small patch (5x5) of the input, tiled across the image
  * matching         : detector response = number of agreeing bits (XNOR + popcount), no multiplies
  * competition      : only the best-matching detector fires at each spot (winner-take-all), so the code is sparse
  * Hebbian learning : the winner nudges its own per-bit counters toward the patch it won; its template bit is
                       the sign of the counter. Detectors that never win are re-seeded from a random patch.
Output: a sparse on/off map (which feature fired where), pooled over 2x2 neighbourhoods.
The numpy dot product below is only a fast way to count agreeing bits in simulation: for +-1 bits,
agreements = (P + dot) / 2. The hardware counts bits."""
import numpy as np

PS, ST = 5, 2


def patches(xb, side=28):
    """xb: (B, side*side) bool -> (B, positions, PS*PS) bool"""
    im = xb.reshape(-1, side, side)
    n = (side - PS) // ST + 1
    out = np.stack([im[:, i * ST:i * ST + PS, j * ST:j * ST + PS].reshape(len(im), -1)
                    for i in range(n) for j in range(n)], 1)
    return out, n


class Features:
    def __init__(self, F=64, seed=0, thr=100, min_on=3):
        self.F, self.r, self.thr, self.min_on = F, np.random.RandomState(seed), thr, min_on
        self.cnt = None

    def fit(self, x, n_patches=200000, passes=3, step=1, cmax=31):
        p, _ = patches(x > self.thr)
        p = p.reshape(-1, PS * PS)
        p = p[p.sum(1) >= self.min_on]                                     # ignore blank patches
        p = p[self.r.choice(len(p), min(n_patches, len(p)), replace=False)]
        self.cnt = np.where(p[self.r.choice(len(p), self.F)], 1, -1).astype(np.int32)
        for _ in range(passes):
            wins = np.zeros(self.F, int)
            for i in range(0, len(p), 1000):
                b = p[i:i + 1000]; w = self.winners(b)
                s = np.where(b, step, -step)
                np.add.at(self.cnt, w, s)                                  # Hebbian nudge toward the input
                np.clip(self.cnt, -cmax, cmax, out=self.cnt)
                wins += np.bincount(w, minlength=self.F)
            dead = np.where(wins == 0)[0]                                  # re-seed detectors that never fire
            self.cnt[dead] = np.where(p[self.r.choice(len(p), len(dead))], 1, -1)
        return self

    def winners(self, b):
        t = np.where(self.cnt >= 0, 1, -1)
        return (np.where(b, 1, -1) @ t.T).argmax(1)                        # = most agreeing bits

    def encode(self, x, pool=2):
        p, n = patches(x > self.thr)
        B = len(x)
        flat = p.reshape(-1, PS * PS)
        w = self.winners(flat).reshape(B, n, n)
        on = (p.sum(2) >= self.min_on).reshape(B, n, n)
        m = n // pool
        code = np.zeros((B, m, m, self.F), bool)
        for di in range(pool):
            for dj in range(pool):
                ww = w[:, di:m * pool:pool, dj:m * pool:pool]; oo = on[:, di:m * pool:pool, dj:m * pool:pool]
                bi, ii, jj = np.nonzero(oo)
                code[bi, ii, jj, ww[bi, ii, jj]] = True                     # OR-pool: feature fired somewhere nearby
        return code.reshape(B, -1)


class CountMemory:
    """Class memory on top of the sparse code: per class, count how often each (place, feature) fired.
    Decision = add up a small lookup-table score per active bit (log-odds from counts, read from a table).
    Learning is counting only: never overwrites, so old classes are never forgotten and two memories merge
    exactly by adding counts."""

    def __init__(self, n_bits, n_cls):
        self.on = np.zeros((n_cls, n_bits), np.int64); self.n = np.zeros(n_cls, np.int64)

    def learn(self, code, y):
        for c in np.unique(y):
            self.on[c] += code[y == c].sum(0); self.n[c] += (y == c).sum()
        return self

    def merge(self, o):
        m = CountMemory(1, 1); m.on, m.n = self.on + o.on, self.n + o.n
        return m

    def table(self, alpha=1.0):
        # per class, per bit: score added when the bit is on / off (precomputed table, small integers in hardware)
        p = (self.on + alpha) / (self.n[:, None] + 2 * alpha)
        return np.log(p), np.log(1 - p)

    def scores(self, code, alpha=1.0, seen=None):
        lon, loff = self.table(alpha)
        s = code.astype(np.float32) @ (lon - loff).T.astype(np.float32) + loff.sum(1)   # sim shortcut for "add per active bit"
        if seen is not None:
            s[:, ~seen] = -np.inf
        return s

    def predict(self, code, **k):
        return self.scores(code, **k).argmax(1)
