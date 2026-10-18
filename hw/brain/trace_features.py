"""Invariant sound detectors by a trace rule (step 2 for new words, 19 Oct 2026). Same detectors as feature_layer.Features (winner-take-all on XNOR + popcount, sign templates from
+-counters, dead detectors re-seeded), but learning is linked across VIEWS of the same recording (Foldiak's trace rule, temporal-coherence / slowness learning): the detector that wins the
window of the centre view is nudged toward the SAME window of every other view (the word shifted in time by +-1 frame, or shifted one frequency row), so its template becomes tolerant to
exactly the variation that separates two recordings of one word. No labels, no gradients, no multiplies: counter steps only. Encoding is unchanged (one view, the shipped hardware)."""
import numpy as np
from feature_layer import Features, binarize, patches, support_filter


class TraceFeatures(Features):
    def fit_views(self, views, n_patches=200000, passes=3, cmax=31, w_side=1):
        """views: list of (N, 784) pictures; views[0] is the centre view. Windows at the same spot of the same clip are tied together."""
        P = []
        for x in views:
            p, _ = patches(support_filter(binarize(x, self.thr), self.support)); P.append(p)           # (N, spots, 25)
        P = np.stack(P, 2)                                                                              # (N, spots, V, 25)
        N, SP, V, nb = P.shape
        P = P.reshape(-1, V, nb); P = P[P[:, 0].sum(1) >= self.min_on]
        P = P[self.r.choice(len(P), min(n_patches, len(P)), replace=False)]
        self.cnt = np.where(P[self.r.choice(len(P), self.F), 0], 1, -1).astype(np.int32)
        for _ in range(passes):
            wins = np.zeros(self.F, int)
            for i in range(0, len(P), 1000):
                b = P[i:i + 1000]; w = self.winners(b[:, 0])
                for v in range(V):
                    np.add.at(self.cnt, w, np.where(b[:, v], 1 if v == 0 else w_side, -1 if v == 0 else -w_side))
                np.clip(self.cnt, -cmax, cmax, out=self.cnt)
                wins += np.bincount(w, minlength=self.F)
            dead = np.where(wins == 0)[0]
            self.cnt[dead] = np.where(P[self.r.choice(len(P), len(dead)), 0], 1, -1)
        return self
