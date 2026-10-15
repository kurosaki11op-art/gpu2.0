"""(Variants of senses_v2: name syntax v1_all+v2_F[_R[_S]] = F detectors, R x R blocks, stride S; DS speech uses aligned
word pictures and 10 channels x 64 detectors.)
Redesign 3, step 1-2: two-layer senses (V1 -> V2), tested in the chip model before any RTL.
  V1   : today's encoder (Features: 5x5 receptive fields, winner-take-all detectors, Hebbian counters, 2x2 OR-pool);
         'all' = its detectors learned from all training images (unlabelled) instead of classes 0/1 only.
  V2   : a second bank of F2 detectors learned the same way (no labels, winner-take-all, Hebbian counters, sign
         templates, agreement = bit count) on V1's unpooled map: each V2 receptive field is a 4x4 block of V1
         positions with every V1 channel's winner bits (4x4 x C*F bits), stride 2 -> 5x5 positions; one winner per
         position. The V2 code (25 x F2 bits) is appended to the V1 code. Same core, same rules.
Exact integer chip model, 3 seeds: all at once and 5 stages. usage: DATA_DIR DS [variant ...]"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
from cortex_core import load
from feature_layer import Features, patches, binarize, support_filter
from cortex_int import CortexInt
D, DS = sys.argv[1], sys.argv[2]
if DS == "speech":
    import cochlea_int
    f_ = np.load(os.path.join(D, "speech_framesums_int.npz")); S_, y_, te_ = f_["S"], f_["y"], f_["te"]
    v_ = cochlea_int.noise_floor(S_); e_ = np.floor(np.log2(v_)).astype(np.int64)
    lg_ = 4 * e_ + ((v_ >> np.maximum(e_ - 2, 0)) & 3); top_ = lg_.reshape(len(v_), -1).max(1)[:, None, None]
    P_ = cochlea_int.align_word(np.clip(255 - (top_ - lg_) * 8, 0, 255).reshape(len(v_), -1).astype(np.uint8), 6)
    xtr, xte, ytr, yte = P_[~te_], P_[te_], y_[~te_].astype(np.int64), y_[te_].astype(np.int64)
    CH = (20, 50, 80, 110, 140, 170, 200, 230, ("on", 8), ("off", 8)); F1 = 64
else:
    xtr, ytr, xte, yte = load(D, DS); ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
    xtr = xtr.reshape(len(xtr), -1); xte = xte.reshape(len(xte), -1)
    CH = (50, 150, ("on", 8), ("off", 8)); F1 = 32


def v1_maps(fes, x):
    """unpooled V1 map: (B, 12, 12, len(fes) * F) bool, winner bit per channel and position (blank spots off)"""
    out = []
    for f in fes:
        p, n = patches(support_filter(binarize(x, f.thr), f.support)); B = len(x)
        w = f.winners(p.reshape(-1, p.shape[-1])).reshape(B, n, n); on = (p.sum(2) >= f.min_on).reshape(B, n, n)
        m = np.zeros((B, n, n, f.F), bool); bi, ii, jj = np.nonzero(on); m[bi, ii, jj, w[bi, ii, jj]] = True
        out.append(m)
    return np.concatenate(out, 3)


def v2_patches(M, R=4, S=2):
    n = (M.shape[1] - R) // S + 1
    return np.stack([M[:, i * S:i * S + R, j * S:j * S + R].reshape(len(M), -1) for i in range(n) for j in range(n)], 1), n


class V2:
    def __init__(self, F2, seed=0):
        self.F, self.r = F2, np.random.RandomState(seed)

    def winners(self, b):
        t = np.where(self.cnt >= 0, 1, -1)
        return (np.where(b, 1, -1).astype(np.int32) @ t.T.astype(np.int32)).argmax(1)

    def fit(self, p, n_patches=60000, passes=3, cmax=31):
        p = p.reshape(-1, p.shape[-1]); p = p[p.sum(1) >= 3]
        p = p[self.r.choice(len(p), min(n_patches, len(p)), replace=False)]
        self.cnt = np.where(p[self.r.choice(len(p), self.F)], 1, -1).astype(np.int32)
        for _ in range(passes):
            wins = np.zeros(self.F, int)
            for i in range(0, len(p), 2000):
                b = p[i:i + 2000]; w = self.winners(b)
                np.add.at(self.cnt, w, np.where(b, 1, -1)); np.clip(self.cnt, -cmax, cmax, out=self.cnt)
                wins += np.bincount(w, minlength=self.F)
            dead = np.where(wins == 0)[0]; self.cnt[dead] = np.where(p[self.r.choice(len(p), len(dead))], 1, -1)
        return self

    def encode(self, p, n):
        B = len(p); w = self.winners(p.reshape(-1, p.shape[-1])).reshape(B, n * n); on = p.sum(2) >= 3
        code = np.zeros((B, n * n, self.F), bool); bi, pi = np.nonzero(on); code[bi, pi, w[bi, pi]] = True
        return code.reshape(B, -1)


BS = 400 if DS == "speech" else 3000


def batched(fn, x, bs=None):
    bs = bs or BS
    return np.concatenate([fn(x[i:i + bs]) for i in range(0, len(x), bs)])


def run_chip(ctr, cte):
    r = {}
    for sname, stages in (("all_at_once", [tuple(range(10))]), ("5_stages", [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)])):
        accs = []
        for seed in (1, 2, 3):
            m = CortexInt(ctr.shape[1], night_stop=2, daydream=1, seed=seed)
            for i, s in enumerate(stages):
                sel = np.where(np.isin(ytr, s))[0]; sel = sel[np.random.RandomState(100 * seed + i).permutation(len(sel))]
                m.stage(ctr[sel], ytr[sel])
            accs.append(round(float((m.predict(cte) == yte).mean()), 4))
        r[sname] = {"acc": accs, "mean": round(float(np.mean(accs)), 4)}
    return r


out = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"senses_v3_{DS}.json")
res = json.load(open(out)) if os.path.exists(out) else {}
names = sys.argv[3:] or ["v1_all", "v1_all+v2_64", "v1_all+v2_128"]
fes_all = None
for name in names:
    if name.startswith("v1_all"):
        if fes_all is None:
            src = xtr[np.random.RandomState(5).choice(len(xtr), 12000, replace=False)]   # unlabelled, all classes
            fes_all = [Features(F1, thr=c, pool=2).fit(src) for c in CH]
        fes = fes_all
    else:
        fes = [Features(F1, thr=c, pool=2).fit(xtr[np.isin(ytr, (0, 1))][:12000]) for c in CH]
    enc1 = lambda x: np.concatenate([f.encode(x) for f in fes], 1)
    ctr, cte = batched(enc1, xtr), batched(enc1, xte)
    if "+v2_" in name:
        a = [int(t) for t in name.split("+v2_")[1].split("_")]; F2 = a[0]; R2 = a[1] if len(a) > 1 else 4; S2 = a[2] if len(a) > 2 else 2
        src = v2_patches(v1_maps(fes, xtr[np.random.RandomState(6).choice(len(xtr), 1500 if DS == "speech" else 8000, replace=False)]), R2, S2)[0]
        v2 = V2(F2).fit(src)
        enc2 = lambda x: v2.encode(*v2_patches(v1_maps(fes, x), R2, S2))
        ctr = np.concatenate([ctr, batched(enc2, xtr)], 1); cte = np.concatenate([cte, batched(enc2, xte)], 1)
    r = {"code_bits": int(ctr.shape[1]), "on_bits": round(float(ctr.sum(1).mean()), 1), **run_chip(ctr, cte)}
    res[name] = r; print(DS, name, r, flush=True)
    json.dump({"dataset": DS, "label": "SIMULATED (exact integer chip model, 3 seeds); today's encoder: all at once / 5 stages "
               "digits 96.9 / 94.6, clothing 82.9 / 78.3, words 82.5 / 80.7", **res}, open(out, "w"), indent=1)
