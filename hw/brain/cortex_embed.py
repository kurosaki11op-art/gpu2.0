"""Table-score embedding for new words (Redesign 8, 20 Oct 2026): bit-exact reference for cortex_core.v built with CORTEX_EMBED.
A new word is NOT written into the table. A clip is described by the vector of its table scores over the known classes (e[j] = score of class j if class j is known, else 0), and a word is a PROTOTYPE slot
(a vector of C signed integers, a label, a count) in that score space. Integer only: adds, subtracts, arithmetic shifts, absolute values, compares.
  enroll(slot, label, sh): empty slot -> p = e; else p += (e - p) >> s with s = sh (1..15) or, if sh = 0, s = min(bitlen(n), SMAX) where n = clips already in the slot (bitlen(1)=1, bitlen(2..3)=2, ...);
      n saturates at 255. New words: sh = 0 (a running mean that is exact for 2, 4, 8 ... clips); old words (competitive learning): sh = 5.
  winner(lo, cnt, e): among slots lo .. lo+cnt-1 the first EMPTY slot, else the slot with the smallest L1 distance sum_j |e[j] - p[j]| (first on a tie)  (the host then enrolls the clip into the winner slot).
  match(e): the filled slot with the smallest L1 distance (first on a tie) -> its label.
CortexEmbed subclasses CortexInt (the table, dreams, slow table option are unchanged)."""
import numpy as np
from cortex_int import CortexInt

SMAX = 5


class CortexEmbed(CortexInt):
    def __init__(self, n_bits, n_cls=16, np_slots=32, **kw):
        super().__init__(n_bits, n_cls=n_cls, **kw)
        self.NP = np_slots; self.pv = np.zeros((np_slots, n_cls), np.int64); self.pn = np.zeros(np_slots, np.int64)
        self.plab = np.zeros(np_slots, np.int64); self.pfill = np.zeros(np_slots, bool)

    def embedding(self, code_idx):
        """integer table scores of a clip given as the list of active bit indices, unknown classes 0"""
        e = np.array([int(self.W[c, code_idx].astype(np.int64).sum()) for c in range(self.W.shape[0])], np.int64)
        return np.where(self.known, e, 0)

    def embedding_batch(self, codes):
        e = codes.astype(np.int32) @ self.W.T.astype(np.int32)
        return np.where(self.known[None, :], e, 0).astype(np.int64)

    def enroll(self, e, slot, label, sh=0):
        if not self.pfill[slot]:
            self.pv[slot] = e; self.pfill[slot] = True; self.pn[slot] = 1; self.plab[slot] = label
        else:
            s = sh if sh else min(int(self.pn[slot]).bit_length(), SMAX)
            self.pv[slot] += (e - self.pv[slot]) >> s; self.pn[slot] = min(self.pn[slot] + 1, 255)

    def winner(self, e, lo, cnt):
        best, bs = -1, None
        for s in range(lo, lo + cnt):
            if not self.pfill[s]:
                return s
            d = int(np.abs(e - self.pv[s]).sum())
            if bs is None or d < bs:
                bs, best = d, s
        return best

    def match(self, e):
        idx = np.where(self.pfill)[0]
        d = np.abs(self.pv[idx] - e[None, :]).sum(1)
        j = int(np.argmin(d))                                              # first minimum = lowest slot
        return int(idx[j]), int(self.plab[idx[j]]), int(d[j])

    def match_batch(self, E):
        idx = np.where(self.pfill)[0]
        d = np.abs(E[:, None, :] - self.pv[idx][None]).sum(2)
        return self.plab[idx[d.argmin(1)]]
