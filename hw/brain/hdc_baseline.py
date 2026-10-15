"""Hyperdimensional computing (HDC) baseline, the closest prior art (docs/prior_art_cortex.md), on our three tasks.

Encoders (D = 10,000 bipolar dimensions):
  pixels : standard random-projection HDC: example HV = sign(R x), R random +-1 (D x 784)
  code   : record encoding of OUR sensory code: example HV = sign(sum of random item HVs of the active code bits)
Class memory: bundling (sum of example HVs per class) -> additive, never forgets, merges by adding.
Retrained: HDC's usual accuracy boost (perceptron-style: on a mistake add the HV to the true class, subtract from the
predicted one), 3 passes; done in 5 stages it interferes with old classes like any error-driven learner.
Decision: largest cosine similarity. SIMULATED (float). usage: [CODES=file TAG=_x] python hdc_baseline.py DATA_DIR mnist|fashion|speech"""
import json, os, sys
import numpy as np
from cortex_core import load

D_, DS = sys.argv[1], sys.argv[2]
D = 10000
F = 64 if DS == "speech" else 32
z = np.load(os.path.join(D_, os.environ.get("CODES", f"sep_{DS}_F{F}_p2.npz"))); ctr, cte = z["tr"], z["te"]   # CODES: another code file
if DS == "speech":
    import cochlea
    xtr, ytr, xte, yte = cochlea.load_speech(os.path.join(D_, "speech"), os.path.join(D_, "speech_pics_res.npz"), cochlea.sound_picture_res)
else:
    xtr, ytr, xte, yte = load(D_, DS)
ytr, yte = ytr.astype(int), yte.astype(int)
r = np.random.RandomState(0)
stages = [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]


def hv_pixels(x, R):
    return np.concatenate([np.sign((x[i:i + 2000] / 255.0 - 0.5).astype(np.float32) @ R.T + 1e-9).astype(np.int8)
                           for i in range(0, len(x), 2000)])


def hv_code(c, I):
    return np.concatenate([np.sign(c[i:i + 2000].astype(np.float32) @ I + 1e-9).astype(np.int8) for i in range(0, len(c), 2000)])


def predict(M, H, known=None):
    Mn = M / (np.linalg.norm(M, axis=1, keepdims=True) + 1e-9)
    s = H.astype(np.float32) @ Mn.T
    if known is not None:
        s[:, ~known] = -1e9
    return s.argmax(1)


def retrain(M, H, y, known, passes=3):
    for _ in range(passes):
        for i in np.random.RandomState(1).permutation(len(y)):
            p = predict(M, H[i:i + 1], known)[0]
            if p != y[i]:
                M[y[i]] += H[i]; M[p] -= H[i]
    return M


R = {"dataset": DS, "label": "SIMULATED (float)", "D": D}
for name, enc in (("pixels", lambda: (hv_pixels(xtr, Rm), hv_pixels(xte, Rm))), ("code", lambda: (hv_code(ctr, Im), hv_code(cte, Im)))):
    Rm = r.choice([-1, 1], size=(D, 784)).astype(np.float32) if name == "pixels" else None
    Im = r.choice([-1, 1], size=(ctr.shape[1], D)).astype(np.float32) if name == "code" else None
    Htr, Hte = enc()
    M = np.zeros((10, D), np.float32)
    for c in range(10):
        M[c] = Htr[ytr == c].sum(0, dtype=np.int64)
    bundle = float((predict(M, Hte) == yte).mean())                         # = its 5-stage result (purely additive)
    Mr = retrain(M.copy(), Htr[:20000], ytr[:20000], np.ones(10, bool))
    retr_all = float((predict(Mr, Hte) == yte).mean())
    Ms = np.zeros((10, D), np.float32); known = np.zeros(10, bool)          # retraining done in 5 stages
    for s in stages:
        sel = np.where(np.isin(ytr, s))[0]; known[list(s)] = True
        for c in s:
            Ms[c] = Htr[ytr == c].sum(0, dtype=np.int64)
        Ms = retrain(Ms, Htr[sel[:4000]], ytr[sel[:4000]], known)
    retr_stages = float((predict(Ms, Hte, known) == yte).mean())
    R[name] = {"bundle_all_and_stages": bundle, "retrained_all_at_once_20k": retr_all, "retrained_in_5_stages": retr_stages,
               "class_memory_KB_16bit": 10 * D * 2 / 1024}
    print(DS, name, R[name], flush=True)
json.dump(R, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results", f"hdc_baseline_{DS}{os.environ.get('TAG', '')}.json"), "w"), indent=1)
