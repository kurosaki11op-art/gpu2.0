"""Pattern separation (fruit-fly mushroom body / hippocampal dentate gyrus): the chip's code bits fan out to an
expansion layer of M cells; each cell adds up S randomly chosen code bits (wiring from a fixed random generator, so no
wiring memory on chip) and only the top ~P percent of cells fire for each input (inhibition: a count histogram and a
threshold compare; ties broken by cell index). Adds and compares only. The table, IMPRINT and sleep then run on the
expanded sparse code. Tests: (1) all classes at once, (2) few-shot after shipping (0-4 known, 5-9 from k = 1, 2, 5
examples) with IMPRINT + a short sleep (300 dreams per class). 3 seeds. usage: DATA_DIR DS"""
import json, os, sys, copy
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
from cortex_core import load
from cortex_int import CortexInt, _dream, _practise
D, DS = sys.argv[1], sys.argv[2]
if DS == "speech":
    z = np.load(os.path.join(D, "sep_speech_align_F64_p2.npz")); f = np.load(os.path.join(D, "speech_framesums_int.npz"))
    y, te = f["y"], f["te"]; ytr, yte = y[~te], y[te]
else:
    z = np.load(os.path.join(D, f"sep_{DS}_F32_p2.npz")); _, ytr, _, yte = load(D, DS)
ctr0, cte0 = z["tr"], z["te"]; ytr = ytr.astype(np.int64); yte = yte.astype(np.int64); NB = ctr0.shape[1]
RULE = dict(B=10, night=2, daydream=1, night_stop=2)
S_IN, P = 8, 5


def expand(code, M, wiring):
    out = np.zeros((len(code), M), bool); kf = M * P // 100
    for i in range(0, len(code), 500):
        cnt = code[i:i + 500][:, wiring].sum(2).astype(np.int16)                 # (b, M): adds only
        for r in range(len(cnt)):
            c = cnt[r]; h = np.bincount(c, minlength=S_IN + 1)
            above = np.cumsum(h[::-1])[::-1]                                         # cells with count >= t
            t = next((t for t in range(1, S_IN + 1) if above[t] <= kf), S_IN + 1)
            fire = c >= t
            if t > 1:                                                                # fill up from count t-1 by index
                extra = np.nonzero(c == t - 1)[0][:kf - int(fire.sum())]; fire[extra] = True
            out[i + r] = fire
    return out


def sleep(m, S):
    buf = np.zeros(m.W.shape[1], np.int32); kn = np.where(m.known)[0]
    for j in range(S * len(kn)):
        c = kn[j % len(kn)]; k = _dream(m.on, m.n, c, m.rng, buf); _practise(m.W, buf, k, c, m.known, m.margin, m.cmax)


old_te, new_te = yte < 5, yte >= 5; res = {}
for name, M in (("today", 0), ("expand2x", 2 * NB), ("expand4x", 4 * NB)):
    if M:
        wiring = np.random.RandomState(7).randint(0, NB, (M, S_IN))
        ctr, cte = expand(ctr0, M, wiring), expand(cte0, M, wiring)
    else:
        ctr, cte = ctr0, cte0
    r = {"code_bits": int(ctr.shape[1]), "on_bits": round(float(ctr.sum(1).mean()), 1)}
    acc = []
    for s in (1, 2, 3):
        m = CortexInt(ctr.shape[1], seed=s, **RULE); sel = np.random.RandomState(100 * s).permutation(len(ytr))
        m.stage(ctr[sel], ytr[sel]); acc.append(float((m.predict(cte) == yte).mean()))
    r["all_at_once"] = round(float(np.mean(acc)), 4)
    for k in (1, 2, 5):
        rows = []
        for s in (1, 2, 3):
            g = np.random.RandomState(1000 * s)
            so = np.where(ytr < 5)[0]; so = so[g.permutation(len(so))]
            sn = np.concatenate([g.choice(np.where(ytr == c)[0], k, replace=False) for c in range(5, 10)]); sn = sn[g.permutation(len(sn))]
            m = CortexInt(ctr.shape[1], seed=s, imprint=4, **RULE); m.stage(ctr[so], ytr[so]); m.stage(ctr[sn], ytr[sn]); sleep(m, 300)
            p = m.predict(cte) == yte
            rows.append({"old": float(p[old_te].mean()), "new": float(p[new_te].mean()), "all": float(p.mean())})
        r[f"k{k}_imprint_sleep"] = {key: round(float(np.mean([q[key] for q in rows])), 4) for key in ("old", "new", "all")}
    res[name] = r; print(DS, name, r, flush=True)
    json.dump({"dataset": DS, "label": "SIMULATED (exact integer chip model, 3 seeds)", **res},
              open(os.path.join(os.path.dirname(os.path.abspath(__file__)), f"expand_kc_{DS}.json"), "w"), indent=1)
