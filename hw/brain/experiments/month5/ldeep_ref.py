"""28 Oct 2026. Independent reference model of the L Deep system, written from the RTL memory files only (deep_wcode1.hex, deep_wcode.hex, deep_wcl.hex, deep_hdr.hex, deep_lits.hex and the routing threshold in l_system.v), not from the training code. Used by the virtual-device tests to check the RTL on inputs the golden exporter never saw (the whole test set, all-zero and all-one images, random bit vectors). Input rows: 6,176 bits (4,608 code bits then 1,568 raw pixel bits)."""
import os, re
import numpy as np
from numba import njit, prange
D = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "rtl", "deep")); NB = 6176; NCODE = 4608
def _rows(f):
    out = []
    for l in open(os.path.join(D, f)):
        l = l.strip()
        if not l: continue
        out.append([int(l[2 * (9 - k):2 * (9 - k) + 2], 16) for k in range(10)])       # class 0 is the lowest byte
    a = np.array(out, np.int64); return np.where(a > 127, a - 256, a)
W1, W2, WCL = _rows("deep_wcode1.hex"), _rows("deep_wcode.hex"), _rows("deep_wcl.hex")
hdr = [(int(l.strip()[:4], 16), int(l.strip()[4:], 16)) for l in open(os.path.join(D, "deep_hdr.hex")) if l.strip()]; lits = [int(l, 16) for l in open(os.path.join(D, "deep_lits.hex")) if l.strip()]
NCL = len(hdr); INC_N = np.array([n for _, n in hdr], np.int32); INC = np.zeros((NCL, max(INC_N)), np.int32)
for c, (s, n) in enumerate(hdr): INC[c, :n] = lits[s:s + n]
ROUTE_T = int(re.search(r"ROUTE_T = (\d+)", open(os.path.join(D, "l_system.v")).read()).group(1))
@njit(parallel=True)
def _fire(X, inc, inn, nb):
    out = np.zeros((len(X), len(inn)), np.int64)
    for i in prange(len(X)):
        for c in range(len(inn)):
            n = inn[c]
            if n == 0: continue
            ok = 1
            for t in range(n):
                lit = inc[c, t]
                if lit < nb:
                    if X[i, lit] == 0: ok = 0; break
                else:
                    if X[i, lit - nb] == 1: ok = 0; break
            out[i, c] = ok
    return out
def run(X):
    """returns routed flags (n,), final scores (n, 10) int64, predictions (n,)"""
    X = np.ascontiguousarray(X, np.uint8); S1 = X[:, :NCODE].astype(np.int64) @ W1; srt = np.sort(S1, 1); marg = srt[:, -1] - srt[:, -2]; routed = marg <= ROUTE_T
    S = S1.copy()
    if routed.any():
        Xr = X[routed]; S2 = Xr[:, :NCODE].astype(np.int64) @ W2 + _fire(Xr, INC, INC_N, NB) @ WCL; S[routed] = S2
    return routed.astype(np.int64), S, S.argmax(1)
if __name__ == "__main__":
    # self-check against the golden exporter's expected file (200 images)
    X = np.array([[(int(l.strip(), 16) >> b) & 1 for b in range(NB)] for l in open(os.path.join(D, "sys_in.hex")) if l.strip()], np.uint8)
    r, S, p = run(X); exp = [list(map(int, l.split())) for l in open(os.path.join(D, "sys_exp.txt")) if l.strip()]
    bad = sum(1 for i, e in enumerate(exp) if [r[i]] + list(S[i]) + [p[i]] != e); print("reference model vs golden exporter: %d mismatches in %d images (routing threshold %d, %d clauses)" % (bad, len(exp), ROUTE_T, NCL))
