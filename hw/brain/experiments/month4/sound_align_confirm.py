"""Confirm word alignment (sound_align.py): threshold 3/4 of the loudest frame, word start moved to frame LEAD
(4, 6, 8), 5 seeds, all at once and 5 stages; saves the best codes as sep_speech_align_F64_p2.npz in DATA_DIR.
Exact integer chip model. usage: DATA_DIR"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
import cochlea_int
from feature_layer import Features
from cortex_int import CortexInt
D = sys.argv[1]
z = np.load(os.path.join(D, "speech_framesums_int.npz")); S, y, te = z["S"], z["y"], z["te"]
ytr, yte = y[~te].astype(np.int64), y[te].astype(np.int64)


def align(S, lead):
    """integer cochlea picture (noise floor) with the word's start moved to frame `lead`"""
    v = cochlea_int.noise_floor(S); e = np.floor(np.log2(v)).astype(np.int64)
    lg = 4 * e + ((v >> np.maximum(e - 2, 0)) & 3); top = lg.reshape(len(v), -1).max(1)[:, None, None]
    P0 = np.clip(255 - (top - lg) * 8, 0, 255).astype(np.uint8)
    loud = P0.astype(np.int64).sum(1); thr = loud.max(1, keepdims=True) * 3 >> 2
    start = np.argmax(loud >= thr, 1); P = np.zeros_like(P0)
    for i in range(len(P0)):
        sh = lead - start[i]
        if sh >= 0:
            P[i, :, sh:] = P0[i, :, :28 - sh]
        else:
            P[i, :, :28 + sh] = P0[i, :, -sh:]
    return P.reshape(len(P), -1)


if __name__ == "__main__":
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sound_align_confirm.json"); res = {}; best = (0, None)
    for lead in (4, 6, 8):
        P = align(S, lead); xtr, xte = P[~te], P[te]
        CH = (20, 50, 80, 110, 140, 170, 200, 230, ("on", 8), ("off", 8))
        fes = [Features(64, thr=c).fit(xtr[np.isin(ytr, (0, 1))][:12000]) for c in CH]
        enc = lambda x: np.concatenate([np.concatenate([f.encode(x[i:i + 5000]) for f in fes], 1) for i in range(0, len(x), 5000)])
        ctr, cte = enc(xtr), enc(xte); r = {}
        for sname, stages in (("all_at_once", [tuple(range(10))]), ("5_stages", [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)])):
            accs = []
            for seed in (1, 2, 3, 4, 5):
                m = CortexInt(ctr.shape[1], night_stop=2, daydream=1, seed=seed)
                for i, s in enumerate(stages):
                    sel = np.where(np.isin(ytr, s))[0]; sel = sel[np.random.RandomState(100 * seed + i).permutation(len(sel))]
                    m.stage(ctr[sel], ytr[sel])
                accs.append(round(float((m.predict(cte) == yte).mean()), 4))
            r[sname] = {"acc": accs, "mean": round(float(np.mean(accs)), 4)}
        res[f"lead{lead}"] = r; print(f"lead{lead}", r, flush=True)
        if r["all_at_once"]["mean"] > best[0]:
            best = (r["all_at_once"]["mean"], lead); np.savez_compressed(os.path.join(D, "sep_speech_align_F64_p2.npz"), tr=ctr, te=cte, lead=lead)
        json.dump({"label": "SIMULATED (integer cochlea + floor + word alignment, exact integer chip model, 5 seeds)", **res},
                  open(out, "w"), indent=1)
    print("best lead", best[1], best[0], flush=True)
