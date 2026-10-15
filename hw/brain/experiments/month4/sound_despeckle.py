"""Speckle removal on sound pictures (integer cochlea + 4x noise floor), clean and at 10 dB white noise, trained clean.
Exact integer chip model, month-2 rule, 3 seeds. usage: DATA_DIR"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import cochlea, cochlea_int
from feature_layer import Features
from cortex_int import CortexInt
from noise_floor import picture, load_framesums  # noqa
D = sys.argv[1]; S, y, te = load_framesums(D)
root = os.path.join(D, "speech"); test = set(open(os.path.join(root, "testing_list.txt")).read().split())
Xte = np.stack([cochlea.read(os.path.join(root, w, f)) for w in cochlea.WORDS for f in sorted(os.listdir(os.path.join(root, w)))
                if f"{w}/{f}" in test])
g = np.random.RandomState(12345); p = (Xte ** 2).mean(1, keepdims=True)
for snr in (20, 10):                                       # same draws as noisy_sound.py: 20 dB first, then 10 dB
    n = g.standard_normal(Xte.shape) * np.sqrt(p / 10 ** (snr / 10))
xn = np.clip(np.round(Xte + n), -32768, 32767).astype(np.int16)
S10 = np.concatenate([cochlea_int._bank(xn[i:i + 1000].astype(np.int64), cochlea_int.A1, cochlea_int.A2, cochlea_int.G, cochlea.FR,
                                        cochlea_int.FB) for i in range(0, len(xn), 1000)])
ytr, yte = y[~te].astype(np.int64), y[te].astype(np.int64)
CH = (20, 50, 80, 110, 140, 170, 200, 230, ("on", 8), ("off", 8)); res = {}
xtr = picture(S[~te], "low4x4"); xc = picture(S[te], "low4x4"); x10 = picture(S10, "low4x4")
for sup in (0, 1):
    fes = [Features(64, thr=c, support=sup).fit(xtr[np.isin(ytr, (0, 1))][:12000]) for c in CH]
    enc = lambda x: np.concatenate([np.concatenate([f.encode(x[i:i + 5000]) for f in fes], 1) for i in range(0, len(x), 5000)])
    ctr = enc(xtr); tests = {"clean": enc(xc), "10dB": enc(x10)}; accs = {k: [] for k in tests}
    for seed in (1, 2, 3):
        m = CortexInt(ctr.shape[1], night_stop=2, daydream=1, seed=seed)
        for i, s in enumerate([(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]):
            sel = np.where(np.isin(ytr, s))[0]; sel = sel[np.random.RandomState(100 * seed + i).permutation(len(sel))]
            m.stage(ctr[sel], ytr[sel])
        for k, c in tests.items():
            accs[k].append(float((m.predict(c) == yte).mean()))
    res[f"support{sup}"] = {k: round(float(np.mean(v)), 4) for k, v in accs.items()}; print("support", sup, res[f"support{sup}"], flush=True)
json.dump({"label": "SIMULATED (exact integer chip model, 3 seeds)", **res},
          open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "sound_despeckle.json"), "w"), indent=1)
