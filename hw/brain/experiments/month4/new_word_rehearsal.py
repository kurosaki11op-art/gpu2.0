"""Teaching a new spoken word to the board's image chip: does rehearsal help? Words 0-7 pre-taught (300 clips each,
stages of two, month-2 schedule); then word 8 is taught from N clips, each followed by D daydreams of the new word and
20 dreams of old words (the demo's teach step), then a short night. Accuracy on unseen clips of word 8 and on all known
words. Emulator of the chip (bit-exact). usage: DATA_DIR (needs <DATA_DIR>/speech_pics_int_floor.npz from cortex_host.py)"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "board")); sys.path.insert(0, os.path.join(HERE, "..", ".."))
import numpy as np
from cortex_host import Emu, SEED_LANES, run_stage, speech, RULE  # noqa
from feature_layer import Features  # noqa
D = sys.argv[1]
xtr, ytr, xte, yte = speech(D)
fes = [Features(32, thr=c).fit(xtr[np.isin(ytr, (0, 1))][:12000]) for c in (50, 150, ("on", 8), ("off", 8))]
enc = lambda x: np.concatenate([f.encode(x) for f in fes], 1)
for N, DD in ((10, 1), (10, 5), (10, 20), (30, 1), (30, 5), (30, 20)):
    dev = Emu(4608); dev.seed(SEED_LANES); dev.clear(); known = set()
    for s0 in range(0, 8, 2):
        sel = np.concatenate([np.where(ytr == c)[0][:300] for c in (s0, s0 + 1)]); sel = sel[np.random.RandomState(s0).permutation(len(sel))]
        run_stage(dev, enc(xtr[sel]), ytr[sel], known)
    new = 8; dev.known(new); known.add(new); idx = np.where(yte == new)[0]; old = sorted(known - {new})
    for i in idx[:N]:
        dev.learn(new, enc(xte[i][None])[0])
        for _ in range(DD):
            dev.dream(new)
        for j in range(20):
            dev.dream(old[j % len(old)])
    kn = sorted(known); blockw = run = 0
    for j in range(3000):
        blockw += dev.dream(kn[j % len(kn)])[1]; run += 1
        if run % 256 == 0:
            if blockw > RULE["night_stop"]:
                break
            blockw = 0
    rest = idx[N:N + 150]; acc_new = np.mean([dev.predict(enc(xte[i][None])[0]) == new for i in rest])
    sel = np.where(np.isin(yte, kn))[0][:400]; acc_all = np.mean([dev.predict(enc(xte[i][None])[0]) == yte[i] for i in sel])
    print(f"clips {N:3d} daydreams {DD:3d}: new word {acc_new:.3f}, all known words {acc_all:.3f}", flush=True)
