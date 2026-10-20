"""New spoken words with time-shifted views (19 Oct 2026). SIMULATED. The 35-word test of sc35_embed.py (base T = 15 table words, new words left/right/up/off/on, table-score embedding path, k = 1 / 2 / 5 recordings, 3 draws), with
"hearing it again with slightly different timing": every recording is seen at three window starts (lead 5, 6, 7), the same shifts as the chip's look-again at test. Arms:
  single : the shipped test (lead 6 only, for training and test)
  views  : every training recording enrols its 3 views (old words: competitive learning with all views; new words: running mean over the views), and the test score vector is the sum over the 3 views (look again)
Reports all / new / old accuracy. Scores are linear in the code, so the embedding of the summed views is the sum of the per-view embeddings. usage: DATA_DIR (holds sc35_framesums_int.npz)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from sound_features import SoundFeatures
import cochlea_int


def align(S, lead):
    """same as sound_align_confirm.align (copied here because importing that module loads another data file): integer cochlea picture (noise floor), word start at frame `lead`"""
    v = cochlea_int.noise_floor(S); e = np.floor(np.log2(v)).astype(np.int64)
    lg = 4 * e + ((v >> np.maximum(e - 2, 0)) & 3); top = lg.reshape(len(v), -1).max(1)[:, None, None]
    P0 = np.clip(255 - (top - lg) * 8, 0, 255).astype(np.uint8)
    loud = P0.astype(np.int64).sum(1); thr = loud.max(1, keepdims=True) * 3 >> 2
    start = np.argmax(loud >= thr, 1); P = np.zeros_like(P0)
    for i in range(len(P0)):
        sh = lead - start[i]
        if sh >= 0: P[i, :, sh:] = P0[i, :, :28 - sh]
        else: P[i, :, :28 + sh] = P0[i, :, -sh:]
    return P.reshape(len(P), -1)
from cortex_slow import CortexSlow
from cortex_embed import CortexEmbed
D = sys.argv[1]; T = int(os.environ.get("T", 15))
z = np.load(os.path.join(D, "sc35_framesums_int.npz")); S, y, te, WORDS = z["S"], z["y"].astype(int), z["te"], [str(w) for w in z["words"]]
NEW = [WORDS.index(w) for w in ("left", "right", "up", "off", "on")]
pool = [i for i in range(len(WORDS)) if i not in NEW]; pool = list(np.random.RandomState(0).permutation(pool)); CH = (20, 50, 80, 110, 140, 170, 200, 230, ("on", 8), ("off", 8))
cf = os.path.join(D, "sc35_codes_views.npz")
if os.path.exists(cf):
    CV = np.load(cf)["codes"]
else:
    P6 = align(S, 6); tr = np.where(~te & np.isin(y, pool[:15]))[0][:12000]; fes = [SoundFeatures(64, c, 3, 3, 1, 1, 4, 4).fit(P6[tr]) for c in CH]
    enc = lambda P: np.concatenate([np.concatenate([q.encode(P[i:i + 500]) for q in fes], 1) for i in range(0, len(P), 500)])
    CV = np.stack([enc(align(S, L)) for L in (5, 6, 7)]); np.savez_compressed(cf, codes=CV)
print("view codes", CV.shape, flush=True); nb = CV.shape[2]
tab = pool[:T]; lab = {w: i for i, w in enumerate(tab + NEW)}; sel = np.isin(y, tab + NEW); yy = np.array([lab.get(v, -1) for v in y])
itr, ite = np.where(sel & ~te)[0], np.where(sel & te)[0]; ytr, yte = yy[itr], yy[ite]; nw = yte >= T; old = np.where(ytr < T)[0]
ctr = CV[:, itr]; cte = CV[:, ite]                                                     # (3, n, nb)
m0 = CortexEmbed(nb, n_cls=32, np_slots=64, seed=1, night=0, daydream=0, margin=int(os.environ.get('MARGIN', 32))); pp = np.random.RandomState(0).permutation(len(old)); m0.stage(ctr[1][old][pp], ytr[old][pp])   # the table learns from lead 6 only
Etr = [m0.embedding_batch(ctr[v]) for v in range(3)]; Ete = [m0.embedding_batch(cte[v]) for v in range(3)]; Ete_sum = sum(Ete)
for k in (1, 2, 5):
    res = {"single": [], "views": []}
    for s in (1, 2, 3):
        g = np.random.RandomState(1000 * s); sn = np.concatenate([g.choice(np.where(ytr == c)[0], k, replace=False) for c in range(T, T + 5)]); sn = sn[g.permutation(len(sn))]
        for arm in ("single", "views"):
            me = CortexEmbed(nb, n_cls=32, np_slots=64, seed=1); me.W = m0.W; me.known = m0.known; vs = (1,) if arm == "single" else (0, 1, 2)
            for cl in range(T):
                idx = np.where(ytr == cl)[0]; idx = idx[np.random.RandomState(s * 10 + cl).permutation(len(idx))]
                for i in idx:
                    for v in vs: me.enroll(Etr[v][i], me.winner(Etr[v][i], cl, 1), cl, sh=5)
            for cl in range(T, T + 5):
                for i in sn[ytr[sn] == cl]:
                    for v in vs: me.enroll(Etr[v][i], cl, cl, sh=0)
            p = me.match_batch(Ete[1]) if arm == "single" else me.match_batch(Ete_sum // 3)
            res[arm].append(((p == yte).mean(), (p[nw] == yte[nw]).mean(), (p[~nw] == yte[~nw]).mean()))
    a, b = np.mean(res["single"], 0), np.mean(res["views"], 0)
    print(f"T={T} k={k}: single all {a[0]:.3f} new {a[1]:.3f} old {a[2]:.3f} | views all {b[0]:.3f} new {b[1]:.3f} old {b[2]:.3f}", flush=True)
