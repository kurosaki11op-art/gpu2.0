"""On-chip sensory detector learning, the hardware rule (bit-exact reference for cortex_encoder.v built with
ENC_LEARN). Per channel: 32 detectors of 25 six-bit counters; the encoder uses their signs (counter >= 0).

  learn one image: for every spot in order (row-major 12x12), if the 5x5 window has >= 3 on bits:
    - while fewer than 32 detectors are seeded: the window seeds the next detector (counters +1 / -1), nothing else;
    - otherwise: winner = detector with the most agreeing bits (first max wins); its counters step +1 toward on bits,
      -1 toward off bits, clipped to +-31; it is marked as having won; the window goes into a ring of the last 32.
  reseed (a separate command, e.g. at the end of a day): every detector that has not won since the last reseed takes
    the next window from the ring (slot 0, 1, ...), as a seed; then all win marks and the ring position clear.
No multiplier, no randomness, nothing stored but the counters, the win marks and the ring."""
import numpy as np
try:
    import numba
    njit = numba.njit(cache=True)
except ImportError:                                                  # pragma: no cover
    njit = lambda f: f


@njit
def _learn(p, cnt, seeded, wins, ring, rp, cmax, min_on):
    """p: (spots, 25) bool windows of one channel, in arrival order. State arrays are updated in place.
    seeded, rp: 1-element int arrays."""
    F, nb = cnt.shape
    for i in range(p.shape[0]):
        on = 0
        for j in range(nb): on += p[i, j]
        if on < min_on: continue
        if seeded[0] < F:
            for j in range(nb): cnt[seeded[0], j] = 1 if p[i, j] else -1
            seeded[0] += 1
            continue
        best, w = -1, 0
        for f in range(F):
            a = 0
            for j in range(nb): a += 1 if p[i, j] == (cnt[f, j] >= 0) else 0
            if a > best: best, w = a, f
        for j in range(nb):
            v = cnt[w, j] + (1 if p[i, j] else -1)
            cnt[w, j] = min(cmax, max(-cmax, v))
        wins[w] = True
        for j in range(nb): ring[rp[0], j] = p[i, j]
        rp[0] = (rp[0] + 1) % F


class StreamDetectors:
    """One channel's detectors; feed windows with learn(), call reseed() when the chip is told to."""
    def __init__(self, F=32, nb=25, cmax=31, min_on=3):
        self.cnt = np.zeros((F, nb), np.int32); self.seeded = np.zeros(1, np.int64); self.wins = np.zeros(F, np.bool_)
        self.ring = np.zeros((F, nb), np.bool_); self.rp = np.zeros(1, np.int64); self.cmax, self.min_on = cmax, min_on

    def learn(self, windows):
        _learn(np.ascontiguousarray(windows.reshape(-1, self.cnt.shape[1]), dtype=np.bool_), self.cnt, self.seeded,
               self.wins, self.ring, self.rp, self.cmax, self.min_on)

    def reseed(self):
        k = 0
        for f in range(len(self.cnt)):
            if not self.wins[f]:
                self.cnt[f] = np.where(self.ring[k % len(self.cnt)], 1, -1); k += 1
        self.wins[:] = False; self.rp[0] = 0
        return k                                                     # detectors reseeded


def learn_features(x, chans=(50, 150, ("on", 8), ("off", 8)), F=32, reseed_every=0):
    """Stream images x once through on-chip learning; returns Features objects using the learned counters.
    reseed_every = 0: one reseed at the end; otherwise after every that many images (and at the end)."""
    from feature_layer import Features, patches, binarize
    out = []
    for c in chans:
        sd = StreamDetectors(F); pp, _ = patches(binarize(x, c))
        step = reseed_every or len(x)
        for i in range(0, len(x), step):
            sd.learn(pp[i:i + step]); sd.reseed()
        f = Features(F, thr=c); f.cnt = sd.cnt.copy(); f.stream = sd; out.append(f)
    return out
