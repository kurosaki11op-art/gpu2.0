"""25 Oct 2026, ESTIMATED energy of the clause layer, with the project's per-operation costs (energy_cortex.py: Horowitz ISSCC 2014, 45 nm; 8-bit add 0.03 pJ, 32-bit add 0.1 pJ, XNOR-popcount match 0.2 pJ, SRAM 64-bit read: 8 KB 10 pJ, 32 KB 20 pJ, 1 MB 100 pJ). Counts measured on the saved 800-clause state and 5,000 test images.
Evaluation styles: (a) scan: every clause's literal word is read for every image (one 64-bit word per clause); (b) keyed: each clause is filed under its rarest POSITIVE literal and is read only when that bit is active (clauses with no positive literal stay in an always-evaluated list)."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.argv = ["x"]
from shirt_new_methods_setup import ctr, cte, ytr, yte
CK = "/tmp/claude-0/-home-user-gpu2-0/320c8e52-5b63-5218-8e07-5330166bbbbd/scratchpad/tm_faithful_state.npz"
z = np.load(CK); inc_list, inc_n = z["inc_list"], z["inc_n"]; NCL = len(inc_n); NB = ctr.shape[1]
E = dict(add8=0.03, add32=0.1, match=0.2, s8=10.0, s32=20.0, s1m=100.0)
X = cte[:5000]; act = X.sum(1).mean(); rate = ctr.mean(0) + 1e-6
pos = [[l for l in inc_list[c, :inc_n[c]] if l < NB] for c in range(NCL)]
haspos = np.array([len(p) > 0 for p in pos]); key = np.array([min(p, key=lambda l: rate[l]) if p else -1 for p in pos])
print("clauses %d, average included literals %.1f, share with at least one positive literal %.2f" % (NCL, inc_n.mean(), haspos.mean()))
def kb(n): return n * (inc_n.mean() * 14) / 8 / 1024
def sram(sz_kb): return E["s8"] if sz_kb <= 8 else E["s32"] if sz_kb <= 32 else (E["s32"] + (E["s1m"] - E["s32"]) * min(1.0, (sz_kb - 32) / 992))
front = 576 * 4 * 32 * E["match"] + 576 * 4 * 32 * E["add8"]               # stride-1 detector matching (576 spots), nJ*1000 = pJ
L_dec = act * E["s32"] + act * 10 * E["add32"]
print("L alone: front end %.1f nJ + table %.1f nJ = %.1f nJ per decision (ESTIMATED; stride-1 code as in these tests)" % (front / 1e3, L_dec / 1e3, (front + L_dec) / 1e3))
order = np.argsort(-(1 * np.ones(NCL)))                                       # all clauses
for n_keep, rows, label in ((2000, 416, "top 2,000 clauses (88.74 / AP 0.753)"), (4000, 893, "top 4,000 clauses (89.45 / AP 0.773)"), (8000, 1535, "all 8,000 clauses (89.38 / AP 0.770)")):
    sel = np.arange(NCL)[:n_keep] if n_keep < NCL else np.arange(NCL)
    size_kb = kb(len(sel)); scan = len(sel) * sram(size_kb) + len(sel) * inc_n.mean() * 0.5
    keyed_mask = haspos[sel]; keyed_ids = sel[keyed_mask]; fire = X[:, key[keyed_ids]].sum(1).mean(); always = (~keyed_mask).sum()
    keyed = (fire + always) * sram(size_kb) + (fire + always) * inc_n.mean() * 0.5 + act * 0.5                  # + index lookups of the active bits
    table = rows * E["s32"] + rows * 10 * E["add32"]
    print("%-40s clause store %.0f KB | scan: clause reads %.0f nJ -> total %.0f nJ (x%.1f of L) | keyed: %.0f clauses read per image (%.0f always-on) -> clause reads %.1f nJ, total %.0f nJ (x%.1f of L)" % (label, size_kb, scan / 1e3, (front + scan + table) / 1e3, (front + scan + table) / (front + L_dec), fire + always, always, keyed / 1e3, (front + keyed + table) / 1e3, (front + keyed + table) / (front + L_dec)))
