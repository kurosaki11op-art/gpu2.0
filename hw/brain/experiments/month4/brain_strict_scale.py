"""Scale test (22 Oct 2026) SIMULATED. Does the chip hold up with more training data? 5 stages of 2 classes, NPS training images per class (2,000 = the usual test; 6,000 = the full 60,000-image sets), the 10,000 test images, margin 256 / 1,500 dreams / 1 night, one pass and staged; arms: shipped table, tail memory (3/16). The table and dream memory keep the same size at any data size (84 KB).
usage: DATA_DIR; env DS, NPS, SEEDS, ARMS"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np, detector_learn
from cortex_core import load
from cortex_slow import CortexSlow
import cortex_rules
D = sys.argv[1]; STAGES = [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]; SEEDS = int(os.environ.get("SEEDS", 2)); NPS = int(os.environ.get("NPS", 6000)); t0 = time.time(); os.environ["TMIX"] = "3"
for DS in os.environ.get("DS", "fashion,mnist").split(","):
    xtr, ytr, xte, yte = load(D, DS); ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
    rs = np.random.RandomState(5); idx = np.concatenate([rs.permutation(np.where(np.isin(ytr, s))[0])[:NPS] for s in STAGES]); xtr, ytr = xtr[idx], ytr[idx]
    fes = detector_learn.learn_features(xtr[np.isin(ytr, STAGES[0])][:12000]); enc = lambda x: np.concatenate([np.concatenate([g.encode(x[i:i + 1000]) for g in fes], 1) for i in range(0, len(x), 1000)])
    ctr, cte = enc(xtr), enc(xte); print(DS, "train", ctr.shape, "test", cte.shape, "%.0fs" % (time.time() - t0), flush=True)
    for arm in os.environ.get("ARMS", "base,tail").split(","):
        for staged in ((True,) if os.environ.get("STAGED_ONLY") else (False, True)):
            acc = []
            for seed in range(1, SEEDS + 1):
                kw = dict(ch=(max(100, NPS // 30) if os.environ.get("CHK") == "auto" else max(100, NPS >> 5) if os.environ.get("CHK") == "shift32" else int(os.environ.get("CHK", 100))), K=int(os.environ.get("KS", 5)), night_stop=2, daydream=int(os.environ.get("DAYD", 1)), seed=seed, margin=int(os.environ.get("MARGIN", 256)), ndream=int(os.environ.get("NDREAM", 1500)), night=int(os.environ.get("NIGHT", 1)), B=int(os.environ.get("B", 10)))
                if arm.startswith("real"):                                           # stored examples: E hardest real traces per class, replayed in a short night (mix/16 of the replays)
                    _, E, mix = arm.split(":"); os.environ["HARD"] = "1"; os.environ["CONS"] = os.environ.get("CONSMODE", "1"); os.environ["REALMIX"] = mix
                    m = cortex_rules.CortexRules(ctr.shape[1], rule="real", par=int(E), **kw)
                elif arm.startswith("proto"):
                    from cortex_proto_slow import CortexProtoSlow; m = CortexProtoSlow(ctr.shape[1], protos=int(arm.split(":")[1]), **kw)
                else: m = CortexSlow(ctr.shape[1], **kw) if arm == "base" else cortex_rules.CortexRules(ctr.shape[1], rule="tailmem", **kw)
                for i, s in enumerate(STAGES if staged else [tuple(range(10))]):
                    o = np.where(np.isin(ytr, s))[0]; o = o[np.random.RandomState(100 * seed + i).permutation(len(o))]; m.stage(ctr[o], ytr[o])
                acc.append(float((m.predict(cte) == yte).mean()))
            print(DS, "NPS", NPS, arm, "staged" if staged else "one pass", "%.4f" % np.mean(acc), "%.0fs" % (time.time() - t0), flush=True)
