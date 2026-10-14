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
    """xb: (B, side*side[, channels]) bool -> (B, positions, PS*PS*channels) bool"""
    im = xb.reshape(len(xb), side, side, -1)
    n = (side - PS) // ST + 1
    out = np.stack([im[:, i * ST:i * ST + PS, j * ST:j * ST + PS].reshape(len(im), -1)
                    for i in range(n) for j in range(n)], 1)
    return out, n


def binarize(x, thr):
    if isinstance(thr, list):                                               # several channels seen jointly
        return np.stack([binarize(x, t) for t in thr], -1)                  # (B, pixels, channels)
    """thr = int: on if brighter than thr (receptor threshold).
    thr = ('on', d) / ('off', d): retina centre-surround cells: on if the pixel is brighter (darker) than the average
    of its 3x3 neighbourhood by more than d. Hardware: 8 adds, a shift (divide by 8) and a compare."""
    if not isinstance(thr, tuple):
        return x > thr
    im = x.reshape(-1, 28, 28).astype(np.int32)
    p = np.pad(im, ((0, 0), (1, 1), (1, 1)), mode="edge")
    nb = sum(p[:, 1 + dy:29 + dy, 1 + dx:29 + dx] for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dy or dx) >> 3
    out = im - nb > thr[1] if thr[0] == "on" else nb - im > thr[1]
    return out.reshape(len(x), -1)


class Features:
    def __init__(self, F=64, seed=0, thr=100, min_on=3, pool=2, k=1):
        self.F, self.r, self.thr, self.min_on, self.pool, self.k = F, np.random.RandomState(seed), thr, min_on, pool, k
        self.cnt = None

    def fit(self, x, n_patches=200000, passes=3, step=1, cmax=31):
        p, _ = patches(binarize(x, self.thr))
        p = p.reshape(-1, p.shape[-1])
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

    def encode(self, x, pool=None):
        pool = pool or self.pool
        p, n = patches(binarize(x, self.thr))
        B = len(x)
        flat = p.reshape(-1, p.shape[-1])
        if self.k == 1:
            W = self.winners(flat).reshape(B, n, n, 1)
        else:                                                               # k winners per spot (k-WTA)
            t = np.where(self.cnt >= 0, 1, -1)
            W = np.argsort(-(np.where(flat, 1, -1) @ t.T), 1)[:, :self.k].reshape(B, n, n, self.k)
        on = (p.sum(2) >= self.min_on).reshape(B, n, n)
        m = n // pool
        code = np.zeros((B, m, m, self.F), bool)
        for di in range(pool):
            for dj in range(pool):
                ww = W[:, di:m * pool:pool, dj:m * pool:pool]; oo = on[:, di:m * pool:pool, dj:m * pool:pool]
                bi, ii, jj = np.nonzero(oo)
                for kk in range(ww.shape[-1]):
                    code[bi, ii, jj, ww[bi, ii, jj, kk]] = True             # OR-pool: feature fired somewhere nearby
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


class ConceptMemory:
    """Concept cells: each class owns P prototype neurons (per-bit on-counts + a use count). An example is matched to
    its own class's best prototype, which counts it (Hebbian, competitive, within the class only). Classes never touch
    each other's cells, so learning a new class cannot disturb an old one, and two chips merge by pooling their cells.
    Decision: the best-matching prototype over all classes; match score = sum of small table values per bit
    (log-frequency lookups), i.e. additions only in hardware."""

    def __init__(self, n_bits, n_cls, P=16, alpha=0.5, seed=0):
        self.P, self.alpha, self.r = P, alpha, np.random.RandomState(seed)
        self.on = np.zeros((n_cls, P, n_bits), np.int64); self.n = np.zeros((n_cls, P), np.int64)

    def _tables(self):
        p = (self.on + self.alpha) / (self.n[..., None] + 2 * self.alpha)
        return (np.log(p) - np.log1p(-p)).astype(np.float32), np.log1p(-p).sum(-1).astype(np.float32)

    def _match(self, code, c=None):
        d, b = self._tables()
        if c is not None:
            d, b = d[c], b[c]
        s = code.astype(np.float32) @ d.reshape(-1, d.shape[-1]).T + b.reshape(-1)
        return s.reshape(len(code), *d.shape[:-1])

    def learn(self, code, y, iters=4):
        for c in np.unique(y):
            X = code[y == c]
            if self.n[c].sum() == 0:                                         # first sight: seed cells from examples
                pick = X[self.r.choice(len(X), self.P, replace=len(X) < self.P)]
                self.on[c] = pick; self.n[c] = 1
            base_on, base_n = self.on[c].copy(), self.n[c].copy()
            for _ in range(iters):                                           # settle which cell owns which example
                a = np.concatenate([self._match(X[i:i + 4000], c).argmax(1) for i in range(0, len(X), 4000)])
                on, n = base_on.copy(), base_n.copy()
                for p_ in range(self.P):
                    m = a == p_; on[p_] += X[m].sum(0); n[p_] += m.sum()
                self.on[c], self.n[c] = on, n
        return self

    def scores(self, code, bs=2000):
        return np.concatenate([self._match(code[i:i + bs]).max(2) for i in range(0, len(code), bs)])

    def predict(self, code):
        return self.scores(code).argmax(1)

    def dreams(self, classes, n_per_class, seed=0):
        r = np.random.RandomState(seed); X, Y = [], []
        for c in classes:
            w = self.n[c] / self.n[c].sum(); cell = r.choice(self.P, n_per_class, p=w)
            p = (self.on[c] + self.alpha) / (self.n[c][:, None] + 2 * self.alpha)
            X.append(r.random_sample((n_per_class, p.shape[1])) < p[cell]); Y.append(np.full(n_per_class, c))
        return np.concatenate(X), np.concatenate(Y)

    def merge(self, other):
        m = ConceptMemory(self.on.shape[2], self.on.shape[0], self.P * 2, self.alpha)
        m.on = np.concatenate([self.on, other.on], 1); m.n = np.concatenate([self.n, other.n], 1)
        empty = m.n == 0                                                     # unused cells never win
        m.on[empty] = 0; m.n[empty] = 0
        return m
