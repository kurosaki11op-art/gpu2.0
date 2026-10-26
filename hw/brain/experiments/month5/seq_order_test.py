"""26 Oct 2026, SIMULATED. PART 2, first test (our own design): a counting sequence model whose STATE is the longest context order matched so far, with entries ALLOCATED ONLY ON ERROR (burst allocation: when the longest matching context predicts the wrong byte, the next-longer context is stored), compared at equal memory with fixed-order models (a window of the last k bytes, with backoff to shorter orders) and with a full backoff model that stores every context. Byte-level next-symbol prediction, online (predict, then update), one pass over text from this repo's markdown notes; accuracy is scored on the second half of the stream. Counters only, no multiply.
Memory is counted as number of stored contexts (each a context hash plus a small count table of the next bytes seen; reported as entries, not bytes)."""
import glob, os, sys
import numpy as np
root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../.."))
root = "/home/user/gpu2.0" if not os.path.isdir(os.path.join(root, "docs")) else root
txt = b"".join(open(f, "rb").read() for f in sorted(glob.glob(os.path.join(root, "docs", "**", "*.md"), recursive=True)))[:700000]; N = len(txt); half = N // 2
print("corpus: %d bytes of notes" % N, flush=True)
def run(maxk, mode):
    tabs = [dict() for _ in range(maxk + 1)]; ok = tot = 0; matched_hist = np.zeros(maxk + 1, int)
    for i in range(N):
        c = txt[i]; best = None; bk = -1
        for k in range(min(maxk, i), -1, -1):
            t = tabs[k].get(txt[i - k:i])
            if t is not None: best = t; bk = k; break
        pred = max(best, key=best.get) if best else -1
        if i >= half: tot += 1; ok += (pred == c); matched_hist[max(bk, 0)] += 1
        if mode == "full":                                                                         # store every context of every order
            for k in range(min(maxk, i) + 1):
                t = tabs[k].setdefault(txt[i - k:i], {}); t[c] = t.get(c, 0) + 1
        elif mode == "window":                                                                      # one fixed order only (plus order 0), no backoff beyond it
            for k in (0, min(maxk, i)):
                t = tabs[k].setdefault(txt[i - k:i], {}); t[c] = t.get(c, 0) + 1
        else:                                                                                       # burst: update the matched context; if it was wrong, allocate the next longer context
            if bk < 0: tabs[0].setdefault(b"", {})[c] = 1
            else: t = tabs[bk][txt[i - bk:i]]; t[c] = t.get(c, 0) + 1
            if pred != c and bk < maxk and i - bk - 1 >= 0 and bk + 1 <= i: tabs[bk + 1].setdefault(txt[i - bk - 1:i], {})[c] = 1
    return ok / tot, sum(len(t) for t in tabs), matched_hist
for k in (1, 2, 3, 4, 6, 8):
    a, m, _ = run(k, "window"); print("RESULT fixed window order %d (+order 0): accuracy %.4f, stored contexts %8d" % (k, a, m), flush=True)
for k in (2, 3, 4, 6, 8):
    a, m, _ = run(k, "full"); print("RESULT full backoff up to order %d:        accuracy %.4f, stored contexts %8d" % (k, a, m), flush=True)
for k in (3, 4, 6, 8, 12):
    a, m, h = run(k, "burst"); print("RESULT burst allocation, max order %2d:     accuracy %.4f, stored contexts %8d (matched order histogram %s)" % (k, a, m, h.tolist()), flush=True)
