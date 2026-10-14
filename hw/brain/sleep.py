"""Fast correction memory + sleep (dream replay), for SPARK Cortex.

Two memories, as in the brain's complementary learning systems:
  * CountMemory (feature_layer.py) : slow, stable. Only adds counts, so it never forgets and merges exactly.
  * SurpriseTable (here)           : fast, sharper. Small signed counters per (class, feature bit); a decision adds
                                     the counters of the active bits. Written only when surprised (wrong or close):
                                     +1 for the true class, -1 for the rival, on the active bits only.
The fast table alone forgets old classes when it practises only new ones. Fix used by the brain: during sleep the
stable memory replays (dreams) old experiences. Here a dream of class c is a random code where each feature bit is
on with the frequency the count memory has stored for c (hardware: a random number generator and a compare).
The table practises on real new examples mixed with dreams of old classes. No real images are stored.
The numpy products below only add the counters of active bits; the hardware adds."""
import numpy as np


class SurpriseTable:
    def __init__(self, n_bits, n_cls, cmax=127, margin=8):
        self.W = np.zeros((n_cls, n_bits), np.int32); self.cmax, self.margin = cmax, margin

    def scores(self, code, known=None):
        s = code.astype(np.int32) @ self.W.T
        if known is not None:
            s[:, ~known] = -(1 << 30)
        return s

    def predict(self, code, known=None):
        return self.scores(code, known).argmax(1)

    def practise(self, code, y, known, epochs=3, bs=50, seed=0):
        r = np.random.RandomState(seed); writes = 0
        for _ in range(epochs):
            o = r.permutation(len(y))
            for i in range(0, len(y), bs):
                idx = o[i:i + bs]; c = code[idx].astype(np.int32); yy = y[idx]; ar = np.arange(len(idx))
                s = self.scores(code[idx], known); t = s[ar, yy].copy(); s[ar, yy] = -(1 << 30); rv = s.argmax(1)
                sup = (t - s[ar, rv]) <= self.margin
                if sup.any():
                    np.add.at(self.W, yy[sup], c[sup]); np.subtract.at(self.W, rv[sup], c[sup])
                    np.clip(self.W, -self.cmax, self.cmax, out=self.W); writes += int(sup.sum())
        self.last_writes = writes
        return self

    def merge(self, other):
        m = SurpriseTable(1, 1, self.cmax, self.margin); m.W = np.clip(self.W + other.W, -self.cmax, self.cmax)
        return m


def dreams(count_mem, classes, n_per_class, seed=0):
    """Dream codes for `classes` from the stable count memory (each bit on with its stored frequency)."""
    r = np.random.RandomState(seed)
    p = (count_mem.on + 1) / (count_mem.n[:, None] + 2)
    codes = [r.random_sample((n_per_class, p.shape[1])) < p[c] for c in classes]
    return np.concatenate(codes), np.repeat(np.array(classes), n_per_class)
