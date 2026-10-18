"""Neurogenesis for new spoken words, second version (19 Oct): new units are RECRUITED by the new recordings and FIRE ONLY ON A STRONG MATCH (agreement >= T of 25 bits),
not as winner-take-all on every window, so the new bits are sparse and silent on familiar sounds (the first version made them fire everywhere, so the old rows, which never
saw those bits, lost: old words 83 -> 12). Detectors per channel: FNEW, fitted without labels on the windows of the k x 5 new recordings (feature_layer.Features.fit, cnt signs as templates).
Code bit = (channel, detector, 2x2 pooled position cell) fires if any window of the cell agrees >= T. New bits appended; old words learned before the bits existed (0 for them).
usage: DATA_DIR FNEW T [T ...]. 2 draws. SIMULATED."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import feature_layer
from feature_layer import Features, binarize, patches
from cortex_int import CortexInt
from sound_align_confirm import align
D, FNEW, TS = sys.argv[1], int(sys.argv[2]), [int(v) for v in sys.argv[3:]]
z = np.load(os.path.join(D, "sep_speech_align_F64_p2.npz")); f = np.load(os.path.join(D, "speech_framesums_int.npz"))
S, y, te = f["S"], f["y"], f["te"]; ytr, yte = y[~te].astype(int), y[te].astype(int); ctr, cte = z["tr"], z["te"]
P = align(S, 6); xtr, xte = P[~te], P[te]
CH = (20, 50, 80, 110, 140, 170, 200, 230, ("on", 8), ("off", 8)); NB = ctr.shape[1]


def enc_thr(fes, x, T):
    out = []
    for fe, c in zip(fes, CH):
        t = np.where(fe.cnt >= 0, 1, -1).astype(np.int32)                      # (F, 25)
        res = []
        for i in range(0, len(x), 500):
            p, n = patches(binarize(x[i:i + 500], c))                           # (B, n*n, 25)
            B = len(p); agree = (25 + np.where(p, 1, -1).astype(np.int32).reshape(-1, 25) @ t.T) // 2
            on = (p.sum(2) >= 3).reshape(B, n, n)
            hit = (agree.reshape(B, n, n, -1) >= T) & on[..., None]
            m = n // 2; cell = np.zeros((B, m, m, hit.shape[-1]), bool)
            for di in range(2):
                for dj in range(2):
                    cell |= hit[:, di:m * 2:2, dj:m * 2:2]
            res.append(cell.reshape(B, -1))
        out.append(np.concatenate(res, 0))
    return np.concatenate(out, 1)


for k in (1, 2, 5):
    for T in TS:
        res = {"base": [], "grow": []}
        for s in (1, 2):
            g = np.random.RandomState(1000 * s); so = np.where(ytr < 5)[0]; so = so[g.permutation(len(so))]
            sn = np.concatenate([g.choice(np.where(ytr == c)[0], k, replace=False) for c in range(5, 10)]); sn = sn[g.permutation(len(sn))]
            fes = [Features(FNEW, thr=c, seed=s).fit(xtr[sn], n_patches=100000, passes=3) for c in CH]
            newtr, newte = enc_thr(fes, xtr[sn], T), enc_thr(fes, xte, T)
            for name in ("base", "grow"):
                nb = NB + (newtr.shape[1] if name == "grow" else 0)
                m = CortexInt(nb, seed=s, imprint=4, B=10, night=2, daydream=1, night_stop=2)
                m.stage(np.concatenate([ctr[so], np.zeros((len(so), nb - NB), bool)], 1) if name == "grow" else ctr[so], ytr[so])
                m.stage(np.concatenate([ctr[sn], newtr], 1) if name == "grow" else ctr[sn], ytr[sn])
                Tt = np.concatenate([cte, newte], 1) if name == "grow" else cte
                sc = Tt.astype(np.int32) @ m.W.T.astype(np.int32); p = sc.argmax(1); nw = yte >= 5
                res[name].append(((p == yte).mean(), (p[nw] == yte[nw]).mean(), (sc[nw][:, 5:].argmax(1) + 5 == yte[nw]).mean(), (p[~nw] == yte[~nw]).mean(), float(newte.sum(1).mean())))
        for name, v in res.items():
            a = np.mean(v, 0); print(f"k={k} T={T} {name:5s}: all-10 {a[0]:.3f}  new(10-way) {a[1]:.3f}  new(5-way) {a[2]:.3f}  old {a[3]:.3f}  new-bits on {a[4]:.1f}", flush=True)
