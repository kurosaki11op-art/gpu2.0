"""26 Oct 2026, ESTIMATED energy and tile mapping of the best-accuracy version (L + top-N clauses over detector + raw-pixel literals), measured counts on 5,000 test images, both seeds.
Keyed evaluation: each clause is filed under its rarest positive literal and read only when that bit is active; clauses with no positive literal sit in an always-on list. Clause ids are spread over tiles by key literal (literal mod TILES); counts distinct tiles touched per decision. Per-op constants as in clause_energy.py (Horowitz 45 nm). env: STATE, N, TILES, TILE_KB"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.argv = ["x"]
from shirt_new_methods_setup import ctr, cte, ytr, yte, train_table, xtr, xte
from numba import njit, prange
E_ = lambda k, d: type(d)(os.environ.get(k, d))
SP = "/tmp/claude-0/-home-user-gpu2-0/320c8e52-5b63-5218-8e07-5330166bbbbd/scratchpad/"
STATE = E_("STATE", SP + "tm_faithful_state_both.npz"); N = E_("N", 4000); TILES = E_("TILES", 16); TILE_KB = E_("TILE_KB", 64)
def bits(x): im = x.reshape(-1, 28, 28); return np.concatenate([(im > 85).reshape(len(im), -1), (im > 170).reshape(len(im), -1)], 1).astype(np.uint8)
Ctr, Cte = np.concatenate([ctr, bits(xtr)], 1).astype(np.uint8), np.concatenate([cte, bits(xte)], 1).astype(np.uint8); NB = Ctr.shape[1]
z = np.load(STATE); inc_list, inc_n = z["inc_list"], z["inc_n"]; NCL = len(inc_n)
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
                elif X[i, lit - nb] == 1: ok = 0; break
            out[i, cl] = ok
    return out
f20 = np.concatenate([fire_all(Ctr[i:i + 5000], inc_list, inc_n, NB) for i in range(0, 20000, 5000)])
W = train_table(f20, ytr[:20000]); keep = np.argsort(-(W.max(1) - W.min(1)))[:N]
rate = Ctr.mean(0) + 1e-6; X = Cte[:5000]
pos = [[l for l in inc_list[c, :inc_n[c]] if l < NB] for c in keep]; has = np.array([len(p) > 0 for p in pos]); key = np.array([min(p, key=lambda l: rate[l]) if p else -1 for p in pos])
keyed_ids = np.where(has)[0]; always = int((~has).sum()); read = X[:, key[keyed_ids]]            # (images, keyed clauses): 1 if the key bit is active -> clause read
nread = read.sum(1) + always; ninc = inc_n[keep].mean()
tile_of = np.where(has, key % TILES, np.arange(len(keep)) % TILES)                                 # always-on clauses spread evenly
touched = np.array([len(np.unique(np.concatenate([tile_of[keyed_ids][read[i] == 1], tile_of[~has]]))) for i in range(500)])
word = 64; bytes_clause = ninc * 14 / 8; store_kb = N * bytes_clause / 1024
tab_bytes = 10 * (NB_ := ctr.shape[1] + N); tab_kb = tab_bytes / 1024                                # 8-bit entries
act = X[:, :ctr.shape[1]].sum(1).mean(); fire = fire_all(X, inc_list, inc_n, NB)[:, keep].sum(1).mean(); rows = act + fire
e = dict(add32=0.1, match=0.2, add8=0.03, s8=10., s32=20., s1m=100.)
sram = lambda kb: e["s8"] if kb <= 8 else e["s32"] if kb <= 32 else e["s32"] + (e["s1m"] - e["s32"]) * min(1, (kb - 32) / 992)
front = 576 * 4 * 32 * (e["match"] + e["add8"]) / 1e3
clause_nJ = (nread * (sram(TILE_KB) + ninc * 0.5) + act * 0.5) / 1e3; table_nJ = rows * (sram(TILE_KB) + 10 * e["add32"]) / 1e3
L_nJ = front + act * (sram(32) + 10 * e["add32"]) / 1e3
tot = front + clause_nJ.mean() + table_nJ if False else front + clause_nJ + table_nJ
print("state %s | N=%d clauses | %.1f included literals/clause | %.0f%% have a positive literal (%d always-on)" % (os.path.basename(STATE), N, ninc, 100 * has.mean(), always))
print("clauses read per image %.0f (of %d) | clauses firing %.0f | table rows read %.0f (%.0f detector + %.0f clause)" % (nread.mean(), N, fire, rows, act, fire))
print("stores: clauses %.0f KB + table %.0f KB (8-bit entries) = %.0f KB = %.1f tiles of %d KB" % (store_kb, tab_kb, store_kb + tab_kb, (store_kb + tab_kb) / TILE_KB, TILE_KB))
print("tile mapping (%d clause tiles by key literal): distinct tiles touched per decision %.1f of %d (min %d); clause-read messages (one per clause read, to its tile) %.0f; partial-score messages %d" % (TILES, touched.mean(), TILES, touched.min(), nread.mean(), 10 * TILES))
print("ESTIMATED energy per decision: L alone %.1f nJ | L + clauses %.1f nJ (front end %.1f, clause reads %.1f, table %.1f) = x%.2f of L | routed 30%%: %.1f nJ (x%.2f)" % (L_nJ, tot.mean(), front, clause_nJ.mean(), table_nJ.mean() if hasattr(table_nJ, 'mean') else table_nJ, tot.mean() / L_nJ, L_nJ + 0.3 * (tot.mean() - L_nJ), (L_nJ + 0.3 * (tot.mean() - L_nJ)) / L_nJ))
