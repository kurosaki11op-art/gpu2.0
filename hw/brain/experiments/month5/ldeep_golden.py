"""28 Oct 2026, SIMULATED (integer golden model of L Deep, the routed clause layer; bit-exact reference for the RTL in hw/rtl/deep). Rebuilds the best simulated configuration from saved state: 800 clauses per class trained on L's code + raw pixel bits (state tm_faithful_state_both.npz, seed 0), the 4,000 clauses most used by a table trained on 20,000 images, stage-2 table trained on L's code + clause bits, routed by the shipped table's margin (least-sure 30% of images). Everything is integer: literal lists, int table entries, int scores. Writes the files the RTL testbench reads (hex) and the expected scores, and prints accuracy of the integer pipeline (must equal the numpy experiment).
Layout (hw/rtl/deep/): deep_lits.hex (literals of the kept clauses, 14 bits each: index < NB means the bit must be 1, index >= NB means bit (index - NB) must be 0, 0x3FFF is a padding literal that is always true), deep_hdr.hex (per clause: start 16 bits, count 8 bits), deep_wcl.hex (per clause: 10 signed 8-bit entries), deep_wcode.hex (per input bit of L's code: 10 signed 8-bit entries, the stage-2 table's code part), deep_in.hex (routed test images: 6,176 bits each), deep_exp.txt (expected 10 scores and prediction per image), deep_params.txt."""
import os, sys, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.argv = ["x"]
from shirt_new_methods_setup import ctr, cte, ytr, yte, train_table, xtr, xte
from numba import njit, prange
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "rtl", "deep"); NTEST = int(os.environ.get("NTEST", 300)); t0 = time.time()
STATE = "/tmp/claude-0/-home-user-gpu2-0/320c8e52-5b63-5218-8e07-5330166bbbbd/scratchpad/tm_faithful_state_both.npz"
z = np.load(STATE); inc_list, inc_n = z["inc_list"], z["inc_n"]; NCL = len(inc_n)
def _bits(x): im = x.reshape(-1, 28, 28); return np.concatenate([(im > 85).reshape(len(im), -1), (im > 170).reshape(len(im), -1)], 1).astype(np.uint8)
IN_TR = np.concatenate([ctr, _bits(xtr)], 1).astype(np.uint8); IN_TE = np.concatenate([cte, _bits(xte)], 1).astype(np.uint8); NB = IN_TR.shape[1]; NCODE = ctr.shape[1]
@njit(parallel=True)
def fire_all(X, inc_list, inc_n, nb):
    out = np.zeros((len(X), len(inc_n)), np.uint8)
    for i in prange(len(X)):
        for cl in range(len(inc_n)):
            n = inc_n[cl]
            if n == 0: continue
            ok = 1
            for t in range(n):
                lit = inc_list[cl, t]
                if lit < nb:
                    if X[i, lit] == 0: ok = 0; break
                else:
                    if X[i, lit - nb] == 1: ok = 0; break
            out[i, cl] = ok
    return out
fire = lambda X: np.concatenate([fire_all(X[i:i + 5000], inc_list, inc_n, NB) for i in range(0, len(X), 5000)])
ftr, fte = fire(IN_TR), fire(IN_TE); print("[%4.0fs] fired" % (time.time() - t0), flush=True)
W = train_table(ftr[:20000], ytr[:20000]); use = W.max(1) - W.min(1); KEEP = int(os.environ.get("KEEP", 4000)); RQ = float(os.environ.get("RQ", 0.3)); keep = np.argsort(-use)[:KEEP]
W_L = train_table(ctr, ytr); S_L = cte.astype(np.int32) @ W_L; srt = np.sort(S_L, 1); marg = srt[:, -1] - srt[:, -2]; T = int(np.floor(np.quantile(marg, RQ))); route = marg <= T
A = np.concatenate([ctr, ftr[:, keep]], 1); B = np.concatenate([cte, fte[:, keep]], 1); W_LC = train_table(A, ytr); S_LC = B.astype(np.int32) @ W_LC
print("table entry ranges: W_L %d..%d, W_LC %d..%d" % (W_L.min(), W_L.max(), W_LC.min(), W_LC.max()))
assert W_LC.min() >= -128 and W_LC.max() <= 127, "entries do not fit int8"
pred = np.where(route[:, None], S_LC, S_L).argmax(1); print("[%4.0fs] integer pipeline: routed %.1f%% (margin <= %d), accuracy %.4f (L alone %.4f), routed images' accuracy %.4f vs L alone %.4f on them" % (time.time() - t0, 100 * route.mean(), T, (pred == yte).mean(), (S_L.argmax(1) == yte).mean(), (S_LC.argmax(1)[route] == yte[route]).mean(), (S_L.argmax(1)[route] == yte[route]).mean()))
# export: kept clauses in kept order
lits = []; hdr = []; PAD = 0x3FFF
for c in keep:
    n = int(inc_n[c]); hdr.append((len(lits), n)); lits.extend(int(v) for v in inc_list[c, :n])
assert max(lits) < 0x3FFF and len(lits) < 65536
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, "deep_lits.hex"), "w").write("\n".join("%04x" % v for v in lits) + "\n")
open(os.path.join(OUT, "deep_hdr.hex"), "w").write("\n".join("%04x%02x" % (s, n) for s, n in hdr) + "\n")
row = lambda r: "".join("%02x" % (int(v) & 255) for v in r[::-1])           # entry for class 9 first so class 0 is the lowest byte
open(os.path.join(OUT, "deep_wcl.hex"), "w").write("\n".join(row(W_LC[NCODE + k]) for k in range(len(keep))) + "\n")
open(os.path.join(OUT, "deep_wcode.hex"), "w").write("\n".join(row(W_LC[i]) for i in range(NCODE)) + "\n")
ids = np.nonzero(route)[0][:NTEST]
open(os.path.join(OUT, "deep_in.hex"), "w").write("\n".join("%0*x" % ((NB + 3) // 4, int("".join(str(int(b)) for b in IN_TE[i][::-1]), 2)) for i in ids) + "\n")
open(os.path.join(OUT, "deep_exp.txt"), "w").write("\n".join(" ".join(str(int(v)) for v in S_LC[i]) + " %d" % int(S_LC[i].argmax()) for i in ids) + "\n")
open(os.path.join(OUT, "deep_params.txt"), "w").write("NB %d\nNCODE %d\nNCL %d\nNLITS %d\nNTEST %d\nNCLS 10\nROUTE_T %d\n" % (NB, NCODE, len(keep), len(lits), len(ids), T))
mem_kb = (len(lits) * 14 + len(keep) * 24 + len(keep) * 80 + NCODE * 80) / 8 / 1024
print("exported: %d kept clauses, %d literals (mean %.2f per clause, max %d), test images %d; memory at int8 entries %.0f KB (literals %.0f + headers %.0f + clause rows %.0f + code rows %.0f)" % (len(keep), len(lits), len(lits) / len(keep), max(n for _, n in hdr), len(ids), mem_kb, len(lits) * 14 / 8192, len(keep) * 24 / 8192, len(keep) * 80 / 8192, NCODE * 80 / 8192))

# system test files: the first NSYS test images in order (routed and not routed), final scores and prediction of the two-stage pipeline
NSYS = int(os.environ.get("NSYS", 200)); sid = np.arange(NSYS)
open(os.path.join(OUT, "deep_wcode1.hex"), "w").write("\n".join(row(W_L[i]) for i in range(NCODE)) + "\n")
open(os.path.join(OUT, "sys_in.hex"), "w").write("\n".join("%0*x" % ((NB + 3) // 4, int("".join(str(int(b)) for b in IN_TE[i][::-1]), 2)) for i in sid) + "\n")
fin = np.where(route[:, None], S_LC, S_L)
open(os.path.join(OUT, "sys_exp.txt"), "w").write("\n".join("%d " % int(route[i]) + " ".join(str(int(v)) for v in fin[i]) + " %d" % int(fin[i].argmax()) for i in sid) + "\n")
print("system test: %d images, %d routed, pipeline accuracy on them %.4f" % (NSYS, route[sid].sum(), (fin[sid].argmax(1) == yte[sid]).mean()))
