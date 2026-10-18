"""New spoken words with a larger base vocabulary (18 Oct 2026, 35-word Speech Commands subset pushed by the user, 100 clips per word, speaker-disjoint split).
New words = left, right, up, off, on (never in the table; each has twin / near words among the others). Table words = the first T of the remaining 30 in a fixed random order, T = 5, 10, 15 (table rows C <= 16 in the RTL).
Sound code: finer grid 3,3,1,1,4,4,64, detectors fitted on table-pool training clips. Compared, k = 1, 2, 5 recordings per new word, 3 draws, single view:
  shipped path : table of T words, then the new words IMPRINTed (CortexSlow, n_cls 32 so that T = 15 fits, a more generous test than the 16-row chip)
  embedding    : CortexEmbed (hardware-exact rules), table over the T words, one prototype slot per old word (competitive learning, sh 5), new words running mean (sh 0)
plus the all-at-once reference (all T + 5 words learned together). Reports all / new / old accuracy. usage: DATA_DIR. SIMULATED."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from sound_features import SoundFeatures
from sound_align_confirm import align
from cortex_slow import CortexSlow
from cortex_embed import CortexEmbed
D = sys.argv[1]
z = np.load(os.path.join(D, "sc35_framesums_int.npz")); S, y, te, WORDS = z["S"], z["y"].astype(int), z["te"], [str(w) for w in z["words"]]
NEW = [WORDS.index(w) for w in ("left", "right", "up", "off", "on")]
pool = [i for i in range(len(WORDS)) if i not in NEW]; pool = list(np.random.RandomState(0).permutation(pool))
P = align(S, 6); CH = (20, 50, 80, 110, 140, 170, 200, 230, ("on", 8), ("off", 8))
cf = os.path.join(D, "sc35_codes_geom3311.npz")
if os.path.exists(cf):
    codes = np.load(cf)["codes"]
else:
    tr = np.where(~te & np.isin(y, pool[:15]))[0][:12000]
    fes = [SoundFeatures(64, c, 3, 3, 1, 1, 4, 4).fit(P[tr]) for c in CH]
    codes = np.concatenate([np.concatenate([q.encode(P[i:i + 500]) for q in fes], 1) for i in range(0, len(P), 500)])
    np.savez_compressed(cf, codes=codes)
print("codes", codes.shape, "pool order", [WORDS[i] for i in pool], flush=True)
nb = codes.shape[1]
for T in (5, 10, 15):
    tab = pool[:T]; lab = {w: i for i, w in enumerate(tab + NEW)}          # table words 0..T-1, new words T..T+4
    sel = np.isin(y, tab + NEW); yy = np.array([lab.get(v, -1) for v in y])
    itr, ite = np.where(sel & ~te)[0], np.where(sel & te)[0]; ytr, yte = yy[itr], yy[ite]; ctr, cte = codes[itr], codes[ite]
    nw = yte >= T
    m = CortexSlow(nb, n_cls=32, ch=100, K=5, seed=1, night_stop=2, daydream=1); g = np.random.RandomState(5); pp = g.permutation(len(ytr)); m.stage(ctr[pp], ytr[pp])
    p = m.predict(cte); print(f"T={T} all-at-once reference (T+5 words together): all {(p == yte).mean():.3f}  new {(p[nw] == yte[nw]).mean():.3f}  old {(p[~nw] == yte[~nw]).mean():.3f}", flush=True)
    old = np.where(ytr < T)[0]
    m0 = CortexEmbed(nb, n_cls=32, np_slots=64, seed=1, night=0, daydream=0); pp = np.random.RandomState(0).permutation(len(old)); m0.stage(ctr[old][pp], ytr[old][pp])
    Etr, Ete = m0.embedding_batch(ctr), m0.embedding_batch(cte)
    for k in (1, 2, 5):
        r_s, r_e = [], []
        for s in (1, 2, 3):
            g = np.random.RandomState(1000 * s)
            sn = np.concatenate([g.choice(np.where(ytr == c)[0], k, replace=False) for c in range(T, T + 5)]); sn = sn[g.permutation(len(sn))]
            so = old[np.random.RandomState(s).permutation(len(old))]
            ms = CortexSlow(nb, n_cls=32, ch=100, K=5, seed=s, imprint=4, B=10, night=2, daydream=1, night_stop=2); ms.stage(ctr[so], ytr[so]); ms.stage(ctr[sn], ytr[sn])
            p = ms.predict(cte); r_s.append(((p == yte).mean(), (p[nw] == yte[nw]).mean(), (p[~nw] == yte[~nw]).mean()))
            me = CortexEmbed(nb, n_cls=32, np_slots=64, seed=1); me.W = m0.W; me.known = m0.known
            for cl in range(T):
                idx = np.where(ytr == cl)[0]; idx = idx[np.random.RandomState(s * 10 + cl).permutation(len(idx))]
                for i in idx:
                    me.enroll(Etr[i], me.winner(Etr[i], cl, 1), cl, sh=5)
            for cl in range(T, T + 5):
                for i in sn[ytr[sn] == cl]:
                    me.enroll(Etr[i], cl, cl, sh=0)
            p = me.match_batch(Ete); r_e.append(((p == yte).mean(), (p[nw] == yte[nw]).mean(), (p[~nw] == yte[~nw]).mean()))
        a, b = np.mean(r_s, 0), np.mean(r_e, 0)
        print(f"T={T} k={k}: shipped all {a[0]:.3f} new {a[1]:.3f} old {a[2]:.3f} | embedding all {b[0]:.3f} new {b[1]:.3f} old {b[2]:.3f}", flush=True)
