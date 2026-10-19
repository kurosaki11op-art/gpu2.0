"""Second sensory layer, learned on the chip's own rule (19 Oct 2026). SIMULATED. Layer 1 = the shipped code (4 channels, 6 x 6 spots x 32 features). Layer 2, per channel: 3 x 3 windows over the spots (3 x 3 x 32 = 288 bits),
64 detectors learned by the on-chip one-pass competitive rule (detector_learn.StreamDetectors, nb = 288), the winner per window, 2 x 2 OR pooling over the 4 x 4 window spots -> 2 x 2 x 64 = 256 bits per channel (1,024 bits for 4 channels)
added to the layer-1 code. Arms: base (layer 1 only), v2 (layer 1 + layer 2), staged and all-at-once, slow-table chip. Same pipeline as brain_strict_digits.py. usage: DATA_DIR; env DS, NPS, SEEDS, MINON, F2."""
import json, os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
from cortex_core import load
from cortex_slow import CortexSlow
import detector_learn
D = sys.argv[1]; DS = os.environ.get("DS", "mnist"); NPS = int(os.environ.get("NPS", 2000)); SEEDS = int(os.environ.get("SEEDS", 3)); MINON = int(os.environ.get("MINON", 6)); F2 = int(os.environ.get("F2", 64))
STAGES = [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]; t0 = time.time()
xtr, ytr, xte, yte = load(D, DS); ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
rs = np.random.RandomState(5); idx = np.concatenate([rs.permutation(np.where(np.isin(ytr, s))[0])[:NPS] for s in STAGES]); xtr, ytr = xtr[idx], ytr[idx]
ti = rs.permutation(len(xte))[:2000]; xte, yte = xte[ti], yte[ti]
fes = detector_learn.learn_features(xtr[np.isin(ytr, STAGES[0])])
enc = lambda x: np.concatenate([np.concatenate([g.encode(x[i:i + 2000]) for g in fes], 1) for i in range(0, len(x), 2000)])
c1tr, c1te = enc(xtr), enc(xte); first = np.isin(ytr, STAGES[0]); print("layer 1", c1tr.shape, "%.0fs" % (time.time() - t0), flush=True)


def windows(code, ch):
    """(B, 16, 288) bool: 3 x 3 windows over the 6 x 6 spots of channel ch"""
    x = code[:, ch * 1152:(ch + 1) * 1152].reshape(len(code), 6, 6, 32); w = np.zeros((len(code), 4, 4, 3, 3, 32), bool)
    for i in range(3):
        for j in range(3): w[:, :, :, i, j] = x[:, i:i + 4, j:j + 4]
    return w.reshape(len(code), 16, 288)


dets = []
for ch in range(4):
    sd = detector_learn.StreamDetectors(F2, nb=288, min_on=MINON); w = windows(c1tr[first], ch).reshape(-1, 288); sd.learn(w); sd.reseed(); dets.append(np.where(sd.cnt >= 0, 1, -1).astype(np.int8))


def layer2(code):
    out = []
    for i in range(0, len(code), 1000):
        c = code[i:i + 1000]; parts = []
        for ch in range(4):
            w = windows(c, ch); on = w.sum(2) >= MINON; win = (np.where(w, 1, -1).astype(np.int8).reshape(-1, 288).astype(np.float32) @ dets[ch].T.astype(np.float32)).argmax(1).reshape(len(c), 4, 4)
            z = np.zeros((len(c), 2, 2, F2), bool)
            for di in range(2):
                for dj in range(2):
                    ww = win[:, di::2, dj::2]; oo = on.reshape(len(c), 4, 4)[:, di::2, dj::2]; bi, ii, jj = np.nonzero(oo); z[bi, ii, jj, ww[bi, ii, jj]] = True
            parts.append(z.reshape(len(c), -1))
        out.append(np.concatenate(parts, 1))
    return np.concatenate(out)


v2tr, v2te = layer2(c1tr), layer2(c1te); print("layer 2", v2tr.shape, "active bits per example", round(float(v2tr.sum(1).mean()), 1), "%.0fs" % (time.time() - t0), flush=True)
CODES = {"base": (c1tr, c1te), "v2": (np.concatenate([c1tr, v2tr], 1), np.concatenate([c1te, v2te], 1)), "v2only": (v2tr, v2te)}; res = {}
for arm, (ctr, cte) in CODES.items():
    out = {"staged": [], "once": []}
    for seed in range(1, SEEDS + 1):
        for mode in ("staged", "once"):
            m = CortexSlow(ctr.shape[1], ch=100, K=5, night_stop=2, daydream=1, seed=seed); groups = STAGES if mode == "staged" else [tuple(range(10))]
            for i, s in enumerate(groups):
                o = np.where(np.isin(ytr, s))[0]; o = o[np.random.RandomState(100 * seed + i).permutation(len(o))]; m.stage(ctr[o], ytr[o])
            out[mode].append(float((m.predict(cte) == yte).mean()))
    res[arm] = {k: round(float(np.mean(v)), 4) for k, v in out.items()}; print(DS, arm, res[arm], "%.0fs" % (time.time() - t0), flush=True)
    json.dump(res, open("brain_strict_v2_%s.json" % DS, "w"), indent=1)
