"""On-chip detector learning test. The PC fit (Features.fit) samples 200,000 random patches and updates in batches of
1,000. A chip sees a stream: this rule learns from patches in arrival order, one update per patch (winner = most
agreeing detector, first max wins; its 6-bit counters step toward the patch, clip +-31), seeds detectors from the first
non-blank patches, and after each pass re-seeds detectors that never won from the latest non-blank patches.
Data = the stage-1 images (classes 0,1, first 12,000), as for the PC fit. Then the 5-stage integer chip model runs on
codes from both detector sets. usage: DATA_DIR mnist|fashion [passes]"""
import json, os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np, numba
from feature_layer import Features, patches, binarize
from cortex_int import CortexInt
from cortex_core import load

D, DS = sys.argv[1], sys.argv[2]; PASSES = int(sys.argv[3]) if len(sys.argv) > 3 else 3
CH = (50, 150, ("on", 8), ("off", 8)); F = 32


@numba.njit(cache=True)
def online_fit(p, F, passes, cmax, min_on):
    nb = p.shape[1]; cnt = np.zeros((F, nb), np.int32); s = 0
    for i in range(p.shape[0]):                                  # seed: first F non-blank patches
        if s == F: break
        if p[i].sum() >= min_on:
            for j in range(nb): cnt[s, j] = 1 if p[i, j] else -1
            s += 1
    for _ in range(passes):
        wins = np.zeros(F, np.int64); recent = np.zeros((F, nb), np.bool_); rp = 0
        for i in range(p.shape[0]):
            if p[i].sum() < min_on: continue
            best, w = -1 << 30, 0
            for f in range(F):
                a = 0
                for j in range(nb):
                    a += 1 if (p[i, j] == (cnt[f, j] >= 0)) else -1
                if a > best: best, w = a, f
            for j in range(nb):
                v = cnt[w, j] + (1 if p[i, j] else -1)
                cnt[w, j] = min(cmax, max(-cmax, v))
            wins[w] += 1
            recent[rp % F] = p[i]; rp += 1
        k = 0
        for f in range(F):                                       # re-seed dead detectors from the latest patches
            if wins[f] == 0:
                for j in range(nb): cnt[f, j] = 1 if recent[k % F, j] else -1
                k += 1
    return cnt


xtr, ytr, xte, yte = load(D, DS); ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
fit_x = xtr[np.isin(ytr, (0, 1))][:12000]
t0 = time.time(); fes = []
for c in CH:
    f = Features(F, thr=c); pp, _ = patches(binarize(fit_x, c)); f.cnt = online_fit(pp.reshape(-1, pp.shape[-1]), F, PASSES, 31, 3); fes.append(f)
print(DS, "online fit %.0fs" % (time.time() - t0), flush=True)
enc = lambda x: np.concatenate([np.concatenate([f.encode(x[i:i + 2000]) for f in fes], 1) for i in range(0, len(x), 2000)])
on = {"tr": enc(xtr), "te": enc(xte)}
z = np.load(os.path.join(D, f"sep_{DS}_F32_p2.npz")); pc = {"tr": z["tr"], "te": z["te"]}
stages = [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]; res = {}
for name, c in (("pc_fit", pc), ("online_fit", on)):
    m = CortexInt(c["tr"].shape[1]); accs = []
    for i, s in enumerate(stages):
        sel = np.where(np.isin(ytr, s))[0]; sel = sel[np.random.RandomState(i).permutation(len(sel))]
        m.stage(c["tr"][sel], ytr[sel]); seen = np.isin(yte, sum(stages[:i + 1], ()))
        accs.append(round(float((m.predict(c["te"][seen]) == yte[seen]).mean()), 4))
    res[name] = {"stages": accs, "active_bits": round(float(c["te"].sum(1).mean()), 1)}
    print(DS, name, res[name], "%.0fs" % (time.time() - t0), flush=True)
json.dump({"dataset": DS, "label": "SIMULATED (integer chip model)", "passes": PASSES, **res},
          open(os.path.join(os.path.dirname(os.path.abspath(__file__)), f"onchip_detectors_{DS}.json"), "w"), indent=1)
