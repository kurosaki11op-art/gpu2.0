"""Sound sensory layer with rectangular receptive fields (Redesign 5, 16 Oct 2026). Same rule as feature_layer.Features (winner-take-all
detectors, Hebbian +-counters, dead detectors re-seeded, XNOR + popcount, OR-pool) but the receptive field is PH rows (frequency) x PW
columns (time), stride (SY, SX), pool (PY, PX). A word is long in time and narrow in frequency, so a wide-in-time field sees a sub-word
sound (a rise, a burst, a gap) instead of a 5x5 blob. Integer / bit operations only (the numpy matmul is a popcount shortcut)."""
import numpy as np
from feature_layer import binarize, support_filter


def windows(xb, ph, pw, sy, sx):
    im = xb.reshape(len(xb), 28, 28, -1)
    ny, nx = (28 - ph) // sy + 1, (28 - pw) // sx + 1
    out = np.stack([im[:, i * sy:i * sy + ph, j * sx:j * sx + pw].reshape(len(im), -1) for i in range(ny) for j in range(nx)], 1)
    return out, ny, nx


class SoundFeatures:
    def __init__(self, F=64, thr=100, ph=5, pw=5, sy=2, sx=2, py=2, px=2, min_on=3, seed=0):
        self.F, self.thr, self.ph, self.pw, self.sy, self.sx, self.py, self.px = F, thr, ph, pw, sy, sx, py, px
        self.min_on = min_on * (ph * pw) // 25; self.r = np.random.RandomState(seed); self.cnt = None

    def _w(self, x):
        return windows(binarize(x, self.thr), self.ph, self.pw, self.sy, self.sx)

    def fit(self, x, n_patches=200000, passes=3, cmax=31):
        p, _, _ = self._w(x); p = p.reshape(-1, p.shape[-1]); p = p[p.sum(1) >= self.min_on]
        p = p[self.r.choice(len(p), min(n_patches, len(p)), replace=False)]
        self.cnt = np.where(p[self.r.choice(len(p), self.F)], 1, -1).astype(np.int32)
        for _ in range(passes):
            wins = np.zeros(self.F, int)
            for i in range(0, len(p), 1000):
                b = p[i:i + 1000]; w = self.winners(b)
                np.add.at(self.cnt, w, np.where(b, 1, -1)); np.clip(self.cnt, -cmax, cmax, out=self.cnt)
                wins += np.bincount(w, minlength=self.F)
            dead = np.where(wins == 0)[0]; self.cnt[dead] = np.where(p[self.r.choice(len(p), len(dead))], 1, -1)
        return self

    def winners(self, b):
        return (np.where(b, 1, -1) @ np.where(self.cnt >= 0, 1, -1).T).argmax(1)

    def encode(self, x):
        p, ny, nx = self._w(x); B = len(x); flat = p.reshape(-1, p.shape[-1])
        W = self.winners(flat).reshape(B, ny, nx); on = (p.sum(2) >= self.min_on).reshape(B, ny, nx)
        my, mx = ny // self.py, nx // self.px; code = np.zeros((B, my, mx, self.F), bool)
        for di in range(self.py):
            for dj in range(self.px):
                ww = W[:, di:my * self.py:self.py, dj:mx * self.px:self.px]; oo = on[:, di:my * self.py:self.py, dj:mx * self.px:self.px]
                bi, ii, jj = np.nonzero(oo); code[bi, ii, jj, ww[bi, ii, jj]] = True
        return code.reshape(B, -1)
